"""Publish immutable per-application releases and safely remove obsolete files."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote

from .github import Publisher

_PACKAGE = re.compile(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+')
_ASSET = re.compile(r'(?:(?:catalog|manifest)-)?([0-9a-f]{64})\.(?:apk|json)')


def _asset_hash(name):
    if not isinstance(name, str):
        raise ValueError('Invalid asset name')
    match = _ASSET.fullmatch(name)
    if not match or (name.endswith('.apk') and len(name) != 68) or (name.endswith('.json') and not name.startswith(('catalog-', 'manifest-'))):
        raise ValueError('Unrecognized managed asset')
    return match.group(1)


class AppPublisher(Publisher):
    def _identity(self, release, tag, draft=None, release_id=None):
        if (not isinstance(release, dict) or type(release.get('id')) is not int or release['id'] <= 0
                or release.get('tag_name') != tag or type(release.get('draft')) is not bool
                or (draft is not None and release['draft'] != draft)
                or (release_id is not None and release['id'] != release_id)):
            raise RuntimeError('Invalid release identity or state')

    def _url(self, tag, name=None):
        base = f'https://github.com/{self.repository}/releases/'
        return base + ('tag/' + quote(tag, safe='') if name is None else 'download/' + quote(tag, safe='') + '/' + quote(name, safe=''))

    def _assets(self, release, tag, expected, allow_missing=False):
        assets = release.get('assets')
        if not isinstance(assets, list):
            raise RuntimeError('Missing release assets')
        actual, ids = {}, set()
        for item in assets:
            if not isinstance(item, dict):
                raise RuntimeError('Invalid release asset')
            name = item.get('name')
            digest = _asset_hash(name)
            asset_url = item.get('browser_download_url')
            valid_url = asset_url == self._url(tag, name)
            if release.get('draft') is True and isinstance(asset_url, str):
                temporary = (re.escape(f'https://github.com/{self.repository}/releases/download/untagged-')
                             + r'[0-9a-f]+/' + re.escape(quote(name, safe='')))
                valid_url = valid_url or bool(re.fullmatch(temporary, asset_url))
            if (name in actual or type(item.get('id')) is not int or item['id'] <= 0 or item['id'] in ids
                    or item.get('digest') != 'sha256:' + digest or item.get('state') != 'uploaded'
                    or type(item.get('size')) is not int or item['size'] <= 0
                    or not valid_url):
                raise RuntimeError('Invalid managed asset')
            actual[name] = item
            ids.add(item['id'])
        for name, desc in expected.items():
            digest = _asset_hash(name)
            if (not isinstance(desc, dict) or desc.get('sha256') != digest
                    or type(desc.get('size')) is not int or desc['size'] <= 0):
                raise ValueError('Invalid expected asset')
            item = actual.get(name)
            if item is None:
                if not allow_missing:
                    raise RuntimeError('Missing expected asset')
            elif item['size'] != desc['size'] or item['digest'] != 'sha256:' + desc['sha256']:
                raise RuntimeError('Expected asset differs from release')
        return actual

    @staticmethod
    def _tag(package):
        if not isinstance(package, str) or not _PACKAGE.fullmatch(package):
            raise ValueError('Invalid package')
        return package + '-library'

    def publish_application(self, package: str, paths: list[Path], expected: dict, *, title, notes) -> dict:
        tag = self._tag(package)
        if not isinstance(expected, dict) or not expected:
            raise ValueError('Invalid expected assets')
        # Validate the entire request before creating or mutating a release.
        self._assets({'assets': []}, tag, expected, allow_missing=True)
        by_name = {}
        for path in paths:
            path = Path(path)
            if path.name in by_name or path.name not in expected:
                raise ValueError('Unexpected or duplicate upload path')
            by_name[path.name] = path
        release = self.release(tag)
        if release is None:
            body = {'tag_name': tag, 'name': title, 'body': notes, 'draft': True}
            release = json.loads(self._gh('api', '--method', 'POST', f'repos/{self.repository}/releases', '--input', '-', input_data=json.dumps(body)))
            self._identity(release, tag, draft=True)
        self._identity(release, tag)
        release_id = release['id']
        draft = release['draft']
        actual = self._assets(release, tag, expected, allow_missing=True)
        missing = [name for name in expected if name not in actual]
        for name in missing:
            if name not in by_name:
                raise ValueError('Missing upload path')
            path = by_name[name]
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
            if path.stat().st_size != expected[name]['size'] or digest.hexdigest() != expected[name]['sha256']:
                raise ValueError('Upload file does not match expected digest and size')
        for name in missing:
            path = by_name[name]
            endpoint = f'https://uploads.github.com/repos/{self.repository}/releases/{release_id}/assets?name=' + quote(name, safe='')
            self._gh('api', '--method', 'POST', endpoint, '-H', 'Content-Type: application/octet-stream', '-H', f'Content-Length: {path.stat().st_size}', '--input', str(path))
        if missing:
            release = json.loads(self._gh('api', f'repos/{self.repository}/releases/{release_id}'))
            self._identity(release, tag, draft=draft, release_id=release_id)
        actual = self._assets(release, tag, expected)
        if draft:
            release = json.loads(self._gh('api', '--method', 'PATCH', f'repos/{self.repository}/releases/{release_id}', '--input', '-', input_data=json.dumps({'draft': False})))
            self._identity(release, tag, draft=False, release_id=release_id)
            actual = self._assets(release, tag, expected)
        return {name: actual[name]['browser_download_url'] for name in expected}

    def cleanup_applications(self, applications: list[dict], legacy_profiles: list[str], *, configured_packages=None) -> None:
        if not isinstance(applications, list) or not isinstance(legacy_profiles, list) or any(not isinstance(p, str) or not re.fullmatch(r'[A-Za-z0-9_]+', p) for p in legacy_profiles):
            raise ValueError('Invalid cleanup request')
        if configured_packages is not None and (not isinstance(configured_packages, (list, tuple, set)) or any(not isinstance(p, str) or not _PACKAGE.fullmatch(p) for p in configured_packages)):
            raise ValueError('Invalid configured packages')
        keepers, packages = [], set()
        for app in applications:
            if not isinstance(app, dict):
                raise ValueError('Invalid application')
            package = app.get('package')
            tag = self._tag(package)
            if package in packages:
                raise ValueError('Duplicate application')
            packages.add(package)
            publication = app.get('publication')
            if not isinstance(publication, dict) or publication.get('tag') != tag or publication.get('release_url') != self._url(tag):
                raise ValueError('Invalid publication')
            artifacts = app.get('artifacts')
            if not isinstance(artifacts, list) or not artifacts:
                raise ValueError('Invalid artifacts')
            descriptors = artifacts + [publication.get('catalog'), publication.get('compat_manifest')]
            expected = {}
            for desc in descriptors:
                if not isinstance(desc, dict) or desc.get('name') in expected:
                    raise ValueError('Invalid asset descriptor')
                name = desc.get('name')
                _asset_hash(name)
                if desc.get('url') != self._url(tag, name):
                    raise ValueError('Invalid asset URL')
                expected[name] = desc
            if not publication['catalog']['name'].startswith('catalog-') or not publication['compat_manifest']['name'].startswith('manifest-') or any(not a['name'].endswith('.apk') for a in artifacts):
                raise ValueError('Invalid asset type')
            body = self._presentation(app, {item['sha256'] for item in artifacts})
            release = self.release(tag)
            self._identity(release, tag, draft=False)
            if release.get('html_url') != publication['release_url']:
                raise RuntimeError('Keeper release URL differs')
            actual = self._assets(release, tag, expected)
            keepers.append((release, expected, actual, app['name'], body))
        if not keepers:
            return
        if configured_packages is not None:
            packages.intersection_update(configured_packages)
        releases = self._list_releases()
        obsolete = []
        for release in releases:
            tag = release['tag_name']
            if any(re.fullmatch(re.escape(package + '-' + profile + '-') + r'[1-9][0-9]*', tag) for package in packages for profile in legacy_profiles):
                obsolete.append(tag)
        managed = [keeper for keeper in keepers if keeper[0]['tag_name'] in {package + '-library' for package in packages}]
        for release, expected, actual, name, body in managed:
            self._gh('api', '--method', 'PATCH', f"repos/{self.repository}/releases/{release['id']}", '--input', '-', input_data=json.dumps({'name': name, 'body': body}))
        for release, expected, actual, name, body in managed:
            for asset_name, item in actual.items():
                if asset_name not in expected:
                    self._gh('api', '--method', 'DELETE', f"repos/{self.repository}/releases/assets/{item['id']}")
        for tag in obsolete:
            self._gh('release', 'delete', tag, '--yes', '--cleanup-tag', '--repo', self.repository)

    @staticmethod
    def _presentation(app, artifacts):
        if not isinstance(app.get('name'), str) or not app['name'] or not isinstance(app.get('variants'), list) or not app['variants']:
            raise ValueError('Invalid application presentation')
        lines = ['Choose ONE compatible variant and install its complete set of files. Do not install all release APKs.', '']
        for variant in app['variants']:
            if not isinstance(variant, dict) or not isinstance(variant.get('compatibility'), dict) or not isinstance(variant.get('files'), list) or not variant['files']:
                raise ValueError('Invalid variant')
            if not isinstance(variant.get('id'), str) or type(variant.get('version_code')) is not int or variant['version_code'] <= 0 or not isinstance(variant.get('version_name'), str):
                raise ValueError('Invalid variant identity')
            lines.extend([f"## {variant['id']} — {variant['version_name']} ({variant['version_code']})", '', 'Compatibility: ' + json.dumps(variant['compatibility'], ensure_ascii=False, sort_keys=True), '', 'Files:'])
            for file in variant['files']:
                if not isinstance(file, dict) or not isinstance(file.get('artifact'), str) or not re.fullmatch(r'[0-9a-f]{64}', file['artifact']) or file['artifact'] not in artifacts:
                    raise ValueError('Invalid variant file')
                lines.append(f"- {file.get('original_name', '')}: {file['artifact']}.apk")
            lines.append('')
        return '\n'.join(lines)
