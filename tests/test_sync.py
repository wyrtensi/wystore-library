import unittest
from unittest.mock import Mock, patch
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from wystore_library.sync import run

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / 'apps.json'
        self.config.write_text(json.dumps({'schema': 1, 'apps': [{'package': 'org.example.app', 'profiles': ['px_9a']}]}))
        self.client = Mock(); self.publisher = Mock()
        self.publisher.read_index.return_value = {'schema': 1, 'entries': []}
        self.client.info.return_value = {'app': {'package': 'org.example.app', 'version_code': 2, 'free': True, 'certificate_hashes': ['ab']}}
    def test_equal_version_skips_download(self):
        self.publisher.read_index.return_value['entries'] = [{'package': 'org.example.app', 'profile': 'px_9a', 'version_code': 2}]
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.client.pull.assert_not_called(); self.publisher.publish_index.assert_not_called()
    def test_unknown_version_never_downloads(self):
        self.client.info.return_value['app']['version_code'] = 0
        with self.assertRaises(ValueError): run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.client.pull.assert_not_called()
    @patch('wystore_library.sync.verify_manifest')
    def test_failed_release_preserves_index(self, verify):
        verify.return_value = {'files': [], 'certificate_sha256': ['abc']}
        self.publisher.publish_release.side_effect = RuntimeError('failed')
        with self.assertRaises(RuntimeError): run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.publisher.publish_index.assert_not_called()
    @patch('wystore_library.sync.verify_manifest')
    def test_later_failure_never_publishes_partial_index(self, verify):
        self.config.write_text(json.dumps({'schema':1, 'apps':[{'package':'org.example.app','profiles':['px_9a']}, {'package':'org.example.other','profiles':['px_9a']}]}))
        self.client.info.side_effect = lambda package, profile: {'app': {'package':package, 'version_code':2, 'free':True, 'certificate_hashes':['abc']}}
        verify.return_value = {'files': [], 'certificate_sha256':['abc']}
        self.publisher.publish_release.side_effect = [{'manifest-public.json':'https://example.test/manifest'}, RuntimeError('failed')]
        with self.assertRaises(RuntimeError): run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.publisher.publish_index.assert_not_called()
    @patch('wystore_library.sync.verify_manifest')
    def test_version_name_published_as_display_metadata(self, verify):
        self.client.info.return_value['app']['version_name'] = '2.1'
        verify.return_value = {'files': [], 'certificate_sha256':['abc']}
        self.publisher.publish_release.return_value = {'manifest-public.json':'https://example.test/manifest'}
        captured = {}
        def capture(path): captured.update(json.loads(path.read_text(encoding='utf-8')))
        self.publisher.publish_index.side_effect = capture
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.assertEqual(captured['entries'][0]['version_name'], '2.1')
