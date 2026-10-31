"""GitHub release and atomic index operations through the authenticated gh CLI."""
import base64
import binascii
import json
import subprocess
from pathlib import Path

class Publisher:
    def __init__(self, repository):
        self.repository = repository
        self.index_sha = None
        self.index_read = False

    def _gh(self, *args, allow_not_found=False, input_data=None):
        result = subprocess.run(['gh', *args], input=input_data, capture_output=True, text=True, check=False)
        if result.returncode:
            if allow_not_found and ('HTTP 404' in result.stderr):
                return None
            raise RuntimeError('GitHub operation failed: gh ' + ' '.join(args[:2]))
        return result.stdout

    def release(self, tag):
        raw = self._gh('api', f'repos/{self.repository}/releases/tags/{tag}', allow_not_found=True)
        return json.loads(raw) if raw is not None else None

    def read_index(self):
        raw = self._gh('api', f'repos/{self.repository}/contents/library/index.json?ref=main', allow_not_found=True)
        if raw is None:
            self.index_sha = None
            self.index_read = True
            return {'schema': 1, 'entries': []}
        try:
            response = json.loads(raw)
            if response.get('encoding') != 'base64' or not isinstance(response.get('sha'), str) or not response['sha']:
                raise ValueError('Invalid index response')
            content = base64.b64decode(''.join(response['content'].split()), validate=True)
            index = json.loads(content.decode('utf-8'))
            if not isinstance(index, dict) or index.get('schema') != 1 or not isinstance(index.get('entries'), list):
                raise ValueError('Invalid published index')
        except (KeyError, TypeError, ValueError, UnicodeError, binascii.Error):
            raise ValueError('Invalid published index') from None
        self.index_sha = response['sha']
        self.index_read = True
        return index

    def publish_release(self, tag, paths, expected):
        release = self.release(tag)
        if release is None:
            self._gh('release', 'create', tag, '--repo', self.repository, '--draft', '--title', tag, '--notes', 'Verified APK set')
            release = self.release(tag)
        if release and release.get('draft') is True:
            present = self._check_assets(release, expected, draft=True, allow_missing=True)
            missing = [str(path) for path in paths if Path(path).name not in present]
            if missing:
                self._gh('release', 'upload', tag, *missing, '--repo', self.repository)
                release = self.release(tag)
            self._check_assets(release, expected, draft=True)
            self._gh('release', 'edit', tag, '--repo', self.repository, '--draft=false')
            release = self.release(tag)
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

    def publish_index(self, path):
        if not self.index_read:
            raise RuntimeError('Index must be read before publication')
        content = base64.b64encode(Path(path).read_bytes()).decode('ascii')
        identity = {'name': 'wyrtensi', 'email': 'wyrtensi@gmail.com'}
        body = {'message': 'Update library index', 'content': content, 'branch': 'main', 'author': identity, 'committer': identity}
        if self.index_sha is not None:
            body['sha'] = self.index_sha
        self._gh('api', '--method', 'PUT', f'repos/{self.repository}/contents/library/index.json', '--input', '-', input_data=json.dumps(body))
        self.index_read = False
