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
        self.publisher.publish_release.assert_not_called()
        self.publisher.prune_releases.assert_called_once_with(self.publisher.read_index.return_value['entries'])
    def test_check_only_never_cleans_up_releases(self):
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, check_only=True)
        self.client.pull.assert_not_called()
        self.publisher.prune_releases.assert_not_called()
    @patch('wystore_library.sync.verify_manifest')
    def test_index_is_committed_before_old_versions_are_removed(self, verify):
        verify.return_value = {'files': [], 'certificate_sha256': ['abc']}
        self.publisher.publish_release.return_value = {'manifest-public.json': 'https://example.test/manifest'}
        events, captured = [], {}
        def publish_index(path):
            captured.update(json.loads(path.read_text(encoding='utf-8')))
            events.append('index')
        self.publisher.publish_index.side_effect = publish_index
        self.publisher.prune_releases.side_effect = lambda entries: events.append('cleanup')
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.assertEqual(events, ['index', 'cleanup'])
        entry = captured['entries'][0]
        self.assertRegex(entry['manifest_sha256'], r'^[0-9a-f]{64}$')
        self.assertGreater(entry['manifest_size'], 0)
        self.publisher.prune_releases.assert_called_once_with(captured['entries'])
    @patch('wystore_library.sync.verify_manifest')
    def test_failed_cleanup_can_retry_without_downloading_the_same_version(self, verify):
        verify.return_value = {'files': [], 'certificate_sha256': ['abc']}
        self.publisher.publish_release.return_value = {'manifest-public.json': 'https://example.test/manifest'}
        committed = {}
        self.publisher.publish_index.side_effect = lambda path: committed.update(json.loads(path.read_text()))
        self.publisher.prune_releases.side_effect = RuntimeError('Cleanup failed')
        with self.assertRaisesRegex(RuntimeError, 'Cleanup failed'):
            run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.assertEqual(committed['entries'][0]['version_code'], 2)
        self.publisher.read_index.return_value = committed
        self.publisher.prune_releases.side_effect = None
        self.client.pull.reset_mock()
        self.publisher.publish_release.reset_mock()
        self.publisher.publish_index.reset_mock()
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.client.pull.assert_not_called()
        self.publisher.publish_release.assert_not_called()
        self.publisher.publish_index.assert_not_called()
    def test_cleanup_does_not_include_apps_removed_from_the_allowlist(self):
        current = {'package': 'org.example.app', 'profile': 'px_9a', 'version_code': 2}
        other = {'package': 'org.example.removed', 'profile': 'px_9a', 'version_code': 1}
        self.publisher.read_index.return_value['entries'] = [current, other]
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.publisher.prune_releases.assert_called_once_with([current])
    def test_missing_google_certificates_never_downloads_or_prunes(self):
        self.client.info.return_value['app']['certificate_hashes'] = []
        with self.assertRaisesRegex(ValueError, 'publisher certificates'):
            run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        self.client.pull.assert_not_called()
        self.publisher.prune_releases.assert_not_called()
    @patch('wystore_library.sync.verify_manifest')
    def test_release_uses_app_version_profile_and_verified_asset_details(self, verify):
        self.client.info.return_value['app'].update(title='Example App', version_name='2.1')
        self.client.info.return_value['device'] = {'model': 'Pixel 9a', 'release': '15', 'sdk': 35, 'abis': ['arm64-v8a'], 'density': 420}
        self.client.info.return_value['source'] = {'account': 'account-token-do-not-publish'}
        verify.return_value = {'files': [{'name': 'base.apk', 'role': 'base', 'size': 3, 'sha256': 'a' * 64}], 'certificate_sha256': ['b' * 64]}
        self.publisher.publish_release.return_value = {'manifest-public.json': 'https://example.test/manifest', 'base.apk': 'https://example.test/base.apk'}
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher)
        presentation = self.publisher.publish_release.call_args.kwargs
        self.assertIsInstance(presentation.get('title'), str)
        self.assertIn('Example App', presentation['title'])
        self.assertIn('2.1', presentation['title'])
        self.assertIn('Pixel 9a', presentation['title'])
        self.assertIn('https://play.google.com/store/apps/details?id=org.example.app', presentation['notes'])
        self.assertIn('arm64-v8a', presentation['notes'])
        self.assertIn('a' * 64, presentation['notes'])
        self.assertIn('b' * 64, presentation['notes'])
        self.assertNotIn('account-token-do-not-publish', str(presentation))
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
