"""GitHub release and atomic index operations through the authenticated gh CLI."""
import base64
import binascii
import json
import re
from urllib.parse import quote, urlsplit
import subprocess
from pathlib import Path

class Publisher:
    def __init__(self, repository):
        self.repository = repository
        self.index_sha = None
        self.index_read = False

    def _gh(self, *args, allow_not_found=False, input_data=None):
        result = subprocess.run(['gh', *args], input=input_data, capture_output=True, text=True, encoding='utf-8', check=False)
        if result.returncode:
            if allow_not_found and ('HTTP 404' in result.stderr):
                return None
            raise RuntimeError('GitHub operation failed: gh ' + ' '.join(args[:2]))
        return result.stdout

    def _list_releases(self):
        pages = json.loads(self._gh('api', f'repos/{self.repository}/releases', '--paginate', '--slurp'))
        if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
            raise ValueError('Invalid releases response')
        releases = []
        for page in pages:
            for release in page:
                if not isinstance(release, dict) or not isinstance(release.get('tag_name'), str) or not release['tag_name']:
                    raise ValueError('Invalid release in response')
                releases.append(release)
        return releases

    def release(self, tag):
        raw = self._gh('api', f'repos/{self.repository}/releases/tags/{tag}', allow_not_found=True)
        if raw is not None:
            return json.loads(raw)
        matches = [release for release in self._list_releases() if release['tag_name'] == tag]
        if len(matches) > 1:
            raise ValueError('Multiple releases match the same tag')
        return matches[0] if matches else None

    def _read_file(self, path, *, allow_not_found=False):
        raw = self._gh('api', f'repos/{self.repository}/contents/{path}?ref=main', allow_not_found=allow_not_found)
        if raw is None:
            return None
        try:
            response = json.loads(raw)
            if not isinstance(response, dict) or not isinstance(response.get('sha'), str) or not response['sha']:
                raise ValueError('Invalid file response')
            if response.get('encoding') == 'base64':
                content = base64.b64decode(''.join(response['content'].split()), validate=True).decode('utf-8')
            elif response.get('encoding') == 'none':
                # Contents omits payloads above 1 MB. Read the immutable blob,
                # retaining the same SHA for the later optimistic index write.
                content = self._gh('api', f"repos/{self.repository}/git/blobs/{quote(response['sha'], safe='')}",
                                   '-H', 'Accept: application/vnd.github.raw+json')
            else:
                raise ValueError('Unsupported file encoding')
            return content, response['sha']
        except (KeyError, TypeError, ValueError, UnicodeError, binascii.Error):
            raise ValueError('Invalid published file') from None

    def read_index(self):
        record = self._read_file('library/index.json', allow_not_found=True)
        if record is None:
            self.index_sha = None
            self.index_read = True
            return {'schema': 1, 'entries': []}
        content, sha = record
        try:
            index = json.loads(content)
            if not isinstance(index, dict) or index.get('schema') != 1 or not isinstance(index.get('entries'), list):
                raise ValueError('Invalid published index')
        except (TypeError, ValueError):
            raise ValueError('Invalid published index') from None
        self.index_sha = sha
        self.index_read = True
        return index

    def read_readme(self):
        return self._read_file('README.md')

    def write_readme(self, content, sha):
        if not isinstance(content, str) or not isinstance(sha, str) or not sha:
            raise ValueError('Invalid README update')
        self._write_content('README.md', content.encode('utf-8'), sha,
                            'Refresh the application catalog in the README.')

    def _write_content(self, path, content, sha, message):
        identity = {'name': 'wyrtensi', 'email': 'wyrtensi@gmail.com'}
        body = {'message': message, 'content': base64.b64encode(content).decode('ascii'),
                'branch': 'main', 'author': identity, 'committer': identity}
        if sha is not None:
            body['sha'] = sha
        self._gh('api', '--method', 'PUT', f'repos/{self.repository}/contents/{path}',
                 '--input', '-', input_data=json.dumps(body))

    def publish_release(self, tag, paths, expected, *, title=None, notes=None):
        def check_identity(value, expected_id=None):
            if (not isinstance(value, dict) or type(value.get('id')) is not int or value['id'] <= 0
                    or value.get('tag_name') != tag or (expected_id is not None and value['id'] != expected_id)):
                raise RuntimeError('Release identity is invalid')

        release = self.release(tag)
        if release is None:
            body = {'tag_name': tag, 'name': title if title is not None else tag,
                    'body': notes if notes is not None else 'Verified APK set', 'draft': True}
            release = json.loads(self._gh('api', '--method', 'POST', f'repos/{self.repository}/releases',
                                          '--input', '-', input_data=json.dumps(body)))
            check_identity(release)
            if release.get('draft') is not True:
                raise RuntimeError('Created release is not a draft')
        if release and release.get('draft') is True:
            check_identity(release)
            release_id = release['id']
            present = self._check_assets(release, expected, draft=True, allow_missing=True)
            missing = [Path(path) for path in paths if Path(path).name not in present]
            for path in missing:
                endpoint = (f'https://uploads.github.com/repos/{self.repository}/releases/{release_id}/assets?name='
                            + quote(path.name, safe=''))
                self._gh('api', '--method', 'POST', endpoint, '-H', 'Content-Type: application/octet-stream',
                         '-H', f'Content-Length: {path.stat().st_size}', '--input', str(path))
            if missing:
                release = json.loads(self._gh('api', f'repos/{self.repository}/releases/{release_id}'))
                check_identity(release, release_id)
            self._check_assets(release, expected, draft=True)
            release = json.loads(self._gh('api', '--method', 'PATCH', f'repos/{self.repository}/releases/{release_id}',
                                          '--input', '-', input_data=json.dumps({'draft': False})))
            check_identity(release, release_id)
        self._check_assets(release, expected, draft=False)
        return {a['name']: a['browser_download_url'] for a in release['assets']}

    @staticmethod
    def _check_assets(release, expected, draft, allow_missing=False):
        if not release or release.get('draft') != draft:
            raise RuntimeError('Release state is incomplete')
        assets = release.get('assets', [])
        actual = {a['name']: (a.get('digest'), a.get('size'), a.get('state')) for a in assets}
        wanted = {name: ('sha256:' + data['sha256'], data['size'], 'uploaded') for name, data in expected.items()}
        if len(actual) != len(assets) or any(name not in wanted or wanted[name] != value for name, value in actual.items()) or (not allow_missing and actual != wanted):
            raise RuntimeError('Release assets do not match verified files')
        return set(actual)

    def prune_releases(self, entries):
        if not isinstance(entries, list):
            raise ValueError('Invalid cleanup entries')
        keepers = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError('Invalid cleanup entry')
            package, profile, version = entry.get('package'), entry.get('profile'), entry.get('version_code')
            if (not isinstance(package, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+', package)
                    or not isinstance(profile, str) or not re.fullmatch(r'[A-Za-z0-9_]+', profile)
                    or type(version) is not int or version <= 0 or (package, profile) in keepers):
                raise ValueError('Invalid cleanup identity')
            assets = entry.get('assets')
            if not isinstance(assets, list) or not assets:
                raise ValueError('Invalid cleanup assets')
            expected, urls = {}, {}
            def add_asset(name, size, digest, url):
                if (not isinstance(name, str) or not name or name in expected or '/' in name or '\\' in name
                        or any(ord(c) < 32 for c in name) or name in ('.', '..')
                        or type(size) is not int or size <= 0
                        or not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest)
                        or not isinstance(url, str)):
                    raise ValueError('Invalid cleanup asset')
                parsed = urlsplit(url)
                if parsed.scheme != 'https' or not parsed.netloc:
                    raise ValueError('Invalid cleanup asset URL')
                expected[name] = {'sha256': digest, 'size': size}
                urls[name] = url
            for asset in assets:
                if not isinstance(asset, dict):
                    raise ValueError('Invalid cleanup asset')
                add_asset(asset.get('name'), asset.get('size'), asset.get('sha256'), asset.get('url'))
            add_asset('manifest-public.json', entry.get('manifest_size'), entry.get('manifest_sha256'), entry.get('manifest_url'))
            tag = f'{package}-{profile}-{version}'
            release = self.release(tag)
            if not isinstance(release, dict) or release.get('tag_name') != tag:
                raise RuntimeError('Keeper release is missing or has a different tag')
            self._check_assets(release, expected, draft=False)
            if any(a.get('browser_download_url') != urls[a['name']] for a in release['assets']):
                raise RuntimeError('Keeper release URLs do not match the index')
            keepers[(package, profile)] = version
        if not keepers:
            return
        tags = []
        for release in self._list_releases():
            tag = release['tag_name']
            for (package, profile), version in keepers.items():
                match = re.fullmatch(re.escape(f'{package}-{profile}-') + r'([1-9][0-9]*)', tag)
                # A completed index is authoritative even after Play rolls a
                # version back. Interrupted runs must not leave extra releases.
                if match and int(match.group(1)) != version:
                    tags.append(tag)
                    break
        for tag in tags:
            self._gh('release', 'delete', tag, '--yes', '--cleanup-tag', '--repo', self.repository)

    def publish_index(self, path):
        if not self.index_read:
            raise RuntimeError('Index must be read before publication')
        self._write_content('library/index.json', Path(path).read_bytes(), self.index_sha,
                            'Update library index')
        self.index_read = False
