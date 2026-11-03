import copy
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from wystore_library.variant_sync import run
from wystore_library.profiles import load_profiles


class VariantSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / 'apps.json'
        self.config.write_text(json.dumps({'schema': 1, 'apps': [{'package': 'org.example.app', 'name': 'Example', 'profiles': ['px_9a']}]}))
        self.profiles = load_profiles('delivery-profiles.json')
        self.client, self.publisher = Mock(), Mock()
        self.publisher.read_index.return_value = {'schema': 1, 'entries': []}
        self.publisher.read_index.side_effect = lambda: copy.deepcopy(self.committed or self.publisher.read_index.return_value)
        self.client.info.side_effect = lambda package, profile: {'app': {'package': package, 'version_code': 2, 'version_name': '2', 'free': True}, 'device': {k: self.profiles[profile][k] for k in ('sdk', 'abis', 'density', 'locale')}}
        def pull(package, profile, version, folder):
            (folder / 'base.apk').write_bytes(b'abc')
            return {'device': self.client.info(package, profile)['device']}
        self.client.pull.side_effect = pull
        self.publisher.publish_application.side_effect = lambda package, paths, expected, **kw: {name: f'https://github.com/owner/repo/releases/download/{package}-library/{name}' for name in expected}
        self.committed = {}
        self.events = []
        self.publisher.publish_index.side_effect = lambda path: (self.committed.update(json.loads(path.read_text(encoding='utf-8'))), self.events.append('index'))
        self.publisher.cleanup_applications.side_effect = lambda apps, profiles, **kwargs: self.events.append('cleanup')
        self.verified = {'package': 'org.example.app', 'version_code': 2, 'certificate_sha256': ['c' * 64], 'files': [{'name': 'base.apk', 'size': 3, 'sha256': hashlib.sha256(b'abc').hexdigest(), 'role': 'base', 'split': ''}]}

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_migrates_all_profiles_deduplicates_and_commits_before_cleanup(self, verify, compatibility):
        verify.return_value = self.verified
        self.assertTrue(run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles))
        app = self.committed['applications'][0]
        self.assertEqual({v['id'] for v in app['variants']}, set(self.profiles))
        self.assertEqual(len(app['artifacts']), 1)
        self.assertEqual(len(self.committed['entries']), 1)
        self.assertEqual(self.committed['entries'][0]['assets'][0]['name'], self.verified['files'][0]['sha256'] + '.apk')
        self.assertEqual(self.events, ['index', 'cleanup'])
        self.assertEqual(self.client.pull.call_count, len(self.profiles))

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_noop_retries_cleanup_without_pulls_or_index_write(self, verify, compatibility):
        verify.return_value = self.verified
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.publisher.read_index.return_value = copy.deepcopy(self.committed)
        self.client.pull.reset_mock(); self.publisher.publish_index.reset_mock(); self.publisher.publish_application.reset_mock(); self.publisher.cleanup_applications.reset_mock()
        self.assertFalse(run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles))
        self.client.pull.assert_not_called(); self.publisher.publish_index.assert_not_called(); self.publisher.publish_application.assert_not_called()
        self.publisher.cleanup_applications.assert_called_once()

    @patch('wystore_library.variant_sync.verify_manifest', side_effect=ValueError('signature failure'))
    def test_verification_failure_does_not_commit_or_clean(self, verify):
        with self.assertRaisesRegex(ValueError, 'signature failure'):
            run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.publisher.publish_index.assert_not_called(); self.publisher.cleanup_applications.assert_not_called()

    @patch('wystore_library.variant_sync.collect_compatibility')
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_incompatible_profile_recorded_and_not_downloaded_again(self, verify, compatibility):
        from wystore_library.compatibility import ProfileIncompatible
        verify.return_value = self.verified
        def compatible(folder, verified, profile, device):
            if profile['id'] == 'legacy_armv7_en':
                raise ProfileIncompatible('abi')
            return {'min_sdk': 26}
        compatibility.side_effect = compatible
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.assertEqual(self.committed['applications'][0]['unavailable'][0]['id'], 'legacy_armv7_en')
        self.publisher.read_index.return_value = copy.deepcopy(self.committed)
        self.client.pull.reset_mock(); self.publisher.publish_index.reset_mock()
        self.assertFalse(run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles))
        self.client.pull.assert_not_called(); self.publisher.publish_index.assert_not_called()

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_legacy_default_newer_than_play_requests_and_verifies_published_version(self, verify, compatibility):
        old = {'package': 'org.example.app', 'profile': 'px_9a', 'version_code': 3, 'version_name': '3.0', 'certificate_sha256': ['c' * 64]}
        self.publisher.read_index.return_value['entries'] = [old]
        verify.side_effect = lambda manifest, folder, package, version, certs, **kwargs: {**self.verified, 'version_code': version}
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        default_pull = next(c for c in self.client.pull.call_args_list if c.args[1] == 'px_9a')
        self.assertEqual(default_pull.args[2], 3)
        self.assertEqual(verify.call_args_list[0].args[3:5], (3, ['c' * 64]))
        default = next(v for v in self.committed['applications'][0]['variants'] if v['id'] == 'px_9a')
        self.assertEqual((default['version_code'], default['version_name']), (3, '3.0'))
        self.assertEqual(self.committed['entries'][0]['version_code'], 3)

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_later_application_failure_preserves_checkpointed_application(self, verify, compatibility):
        self.config.write_text(json.dumps({'schema': 1, 'apps': [{'package': 'org.example.app', 'profiles': ['px_9a']}, {'package': 'org.example.other', 'profiles': ['px_9a']}]}))
        verify.return_value = self.verified
        original_info = self.client.info.side_effect
        def info(package, profile):
            if package == 'org.example.other':
                raise RuntimeError('Play unavailable')
            return original_info(package, profile)
        self.client.info.side_effect = info
        with self.assertRaisesRegex(RuntimeError, 'Play unavailable'):
            run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.publisher.publish_index.assert_called_once()
        self.publisher.cleanup_applications.assert_called_once()
        self.assertEqual(self.committed['applications'][0]['package'], 'org.example.app')
        self.assertEqual(self.committed['migration_pending'], ['org.example.other'])

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_partial_migration_keeps_legacy_entries_and_pending_packages(self, verify, compatibility):
        self.config.write_text(json.dumps({'schema': 1, 'apps': [{'package': 'org.example.app', 'profiles': ['px_9a']}, {'package': 'org.example.other', 'profiles': ['px_9a']}]}))
        old = {'package': 'org.example.other', 'profile': 'px_9a', 'version_code': 1, 'certificate_sha256': ['d' * 64]}
        self.publisher.read_index.return_value['entries'] = [old]
        verify.return_value = self.verified
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles, packages=['org.example.app'])
        self.assertIn(old, self.committed['entries'])
        self.assertEqual(self.committed['migration_pending'], ['org.example.other'])

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_updated_profile_checks_prior_signer_and_reuses_other_variants(self, verify, compatibility):
        verify.return_value = self.verified
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.publisher.read_index.return_value = copy.deepcopy(self.committed)
        self.committed.clear(); self.client.pull.reset_mock(); verify.reset_mock()
        changed_profiles = copy.deepcopy(self.profiles)
        changed_profiles['legacy_armv7_en']['density'] = 321
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, changed_profiles)
        self.assertEqual(self.client.pull.call_count, 1)
        self.assertEqual(self.client.pull.call_args.args[1], 'legacy_armv7_en')
        self.assertEqual(verify.call_args.args[4], ['c' * 64])
        self.assertEqual(len(self.committed['applications'][0]['artifacts']), 1)

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_play_rollback_preserves_newer_canonical_variants(self, verify, compatibility):
        verify.return_value = self.verified
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.publisher.read_index.return_value = copy.deepcopy(self.committed)
        self.client.info.side_effect = lambda package, profile: {'app': {'package': package, 'version_code': 1, 'version_name': '1', 'free': True}}
        self.client.pull.reset_mock(); self.publisher.publish_index.reset_mock()
        self.assertFalse(run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles))
        self.client.pull.assert_not_called(); self.publisher.publish_index.assert_not_called()

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_unavailable_play_profile_is_recorded_without_pull(self, verify, compatibility):
        verify.return_value = self.verified
        original = self.client.info.side_effect
        def info(package, profile):
            if profile == 'legacy_armv7_en':
                return {'app': {'package': package, 'version_code': 0, 'version_name': '', 'free': True}}
            return original(package, profile)
        self.client.info.side_effect = info
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        unavailable = self.committed['applications'][0]['unavailable'][0]
        self.assertEqual((unavailable['id'], unavailable['version_code'], unavailable['reason']), ('legacy_armv7_en', 0, 'play_unavailable'))
        self.assertFalse(any(call.args[1] == 'legacy_armv7_en' for call in self.client.pull.call_args_list))
        self.publisher.read_index.return_value = copy.deepcopy(self.committed)
        self.client.pull.reset_mock(); self.publisher.publish_index.reset_mock()
        self.assertFalse(run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles))
        self.client.pull.assert_not_called(); self.publisher.publish_index.assert_not_called()

    def test_missing_default_play_version_stops_migration(self):
        self.client.info.return_value = {'app': {'package': 'org.example.app', 'version_code': 0, 'version_name': '', 'free': True}}
        self.client.info.side_effect = None
        with self.assertRaisesRegex(ValueError, 'default'):
            run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.publisher.publish_index.assert_not_called()

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_releases_each_profile_and_application_staging_before_next_download(self, verify, compatibility):
        self.config.write_text(json.dumps({'schema': 1, 'apps': [{'package': 'org.example.app', 'profiles': ['px_9a']}, {'package': 'org.example.other', 'profiles': ['px_9a']}]}))
        verify.return_value = self.verified
        profile_folders, first_app_files = [], []
        def pull(package, profile, version, folder):
            self.assertTrue(all(not previous.exists() for previous in profile_folders))
            if package == 'org.example.other' and profile == 'px_9a':
                self.assertTrue(first_app_files)
                self.assertTrue(all(not path.exists() for path in first_app_files))
            profile_folders.append(folder)
            (folder / 'base.apk').write_bytes(b'abc')
            return {'device': {k: self.profiles[profile][k] for k in ('sdk', 'abis', 'density', 'locale')}}
        self.client.pull.side_effect = pull
        def publish(package, paths, expected, **kwargs):
            self.assertTrue(all(path.is_file() for path in paths))
            if package == 'org.example.app':
                first_app_files.extend(paths)
            return {name: f'https://github.com/owner/repo/releases/download/{package}-library/{name}' for name in expected}
        self.publisher.publish_application.side_effect = publish
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.assertEqual(self.events, ['index', 'cleanup', 'index', 'cleanup'])

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_concurrent_index_change_refuses_second_checkpoint(self, verify, compatibility):
        self.config.write_text(json.dumps({'schema': 1, 'apps': [{'package': 'org.example.app', 'profiles': ['px_9a']}, {'package': 'org.example.other', 'profiles': ['px_9a']}]}))
        verify.return_value = self.verified
        original = self.publisher.read_index.side_effect
        reads = []
        def read_index():
            value = original()
            if reads:
                value['external_change'] = True
            reads.append(True)
            return value
        self.publisher.read_index.side_effect = read_index
        with self.assertRaisesRegex(RuntimeError, 'changed during synchronization'):
            run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.publisher.publish_index.assert_called_once()
        self.assertEqual(len(self.committed['applications']), 1)
        self.assertEqual(self.committed['migration_pending'], ['org.example.other'])

    def test_unavailable_pinned_delivery_keeps_previous_index_and_release(self):
        old = {'package': 'org.example.app', 'profile': 'px_9a', 'version_code': 3, 'version_name': '3.0', 'certificate_sha256': ['c' * 64]}
        self.publisher.read_index.return_value['entries'] = [old]
        self.client.pull.side_effect = RuntimeError('Pinned delivery unavailable')
        with self.assertRaisesRegex(RuntimeError, 'Pinned delivery unavailable'):
            run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.assertEqual(self.client.pull.call_args.args[2], 3)
        self.publisher.publish_index.assert_not_called()
        self.publisher.cleanup_applications.assert_not_called()
        self.assertEqual(self.publisher.read_index.return_value['entries'], [old])

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_cleanup_retry_precedes_later_application_failure(self, verify, compatibility):
        verify.return_value = self.verified
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.publisher.cleanup_applications.reset_mock()
        self.client.info.side_effect = RuntimeError('Play unavailable')
        with self.assertRaisesRegex(RuntimeError, 'Play unavailable'):
            run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        self.publisher.cleanup_applications.assert_called_once()

    @patch('wystore_library.variant_sync.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.variant_sync.verify_manifest')
    def test_each_checkpoint_cleans_only_its_application(self, verify, compatibility):
        self.config.write_text(json.dumps({'schema': 1, 'apps': [{'package': 'org.example.app', 'profiles': ['px_9a']}, {'package': 'org.example.other', 'profiles': ['px_9a']}]}))
        verify.return_value = self.verified
        run(self.config, 'owner/repo', self.root / 'out', self.client, self.publisher, self.profiles)
        calls = self.publisher.cleanup_applications.call_args_list
        self.assertEqual([[a['package'] for a in c.args[0]] for c in calls], [['org.example.app'], ['org.example.other']])
        self.assertEqual([c.kwargs['configured_packages'] for c in calls], [{'org.example.app'}, {'org.example.other'}])
