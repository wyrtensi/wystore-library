import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from wystore_library.coverage_validation import partition_packages, validate_batch, ValidationFailed
from wystore_library.play import PlayError
from wystore_library.compatibility import ProfileIncompatible


class CoverageValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.report = self.root / 'report.json'
        self.config = self.root / 'apps.json'
        self.config.write_text(json.dumps({'schema': 1, 'apps': [{'package': 'org.example.app', 'profiles': ['px_9a']}]}))
        self.profiles = {'px_9a': json.loads(Path('delivery-profiles.json').read_text(encoding='utf-8'))[0]}
        self.index = {'applications': []}
        self.client = Mock()
        self.client.info.return_value = {'app': {'package': 'org.example.app', 'version_code': 0, 'version_name': '', 'free': True}}

    def report_data(self):
        return json.loads(self.report.read_text(encoding='utf-8'))

    def test_partitions_cover_all_packages_once_and_reject_invalid_batch(self):
        packages = ['a', 'b', 'c', 'd', 'e']
        self.assertEqual([partition_packages(packages, i, 3) for i in range(3)], [['a', 'd'], ['b', 'e'], ['c']])
        with self.assertRaises(ValueError):
            partition_packages(packages, 3, 3)

    def test_zero_version_is_unavailable_without_download(self):
        validate_batch(self.config, self.profiles, self.index, self.client, self.report, 0, 1)
        self.assertEqual(self.report_data()['records'][0]['status'], 'play_unavailable')
        self.client.pull.assert_not_called()

    def test_bad_apk_hash_fails_with_sanitized_checkpoint(self):
        self.client.info.return_value['app'].update(version_code=1, version_name='1')
        def pull(package, profile, version, folder):
            (folder / 'base.apk').write_bytes(b'bad')
            return {'schema': 'playfetch/v1', 'app': {'package': package, 'version_code': version}, 'device': {'sdk':35}, 'files': [{'name':'base.apk','role':'base','size':3,'local':{'sha256':hashlib.sha256(b'good').hexdigest()},'play_sha256':hashlib.sha256(b'good').hexdigest()}]}
        self.client.pull.side_effect = pull
        with self.assertRaises(ValidationFailed):
            validate_batch(self.config, self.profiles, self.index, self.client, self.report, 0, 1)
        report = self.report_data()
        self.assertFalse(report['complete'])
        self.assertEqual(report['records'][0]['status'], 'verification_error')
        self.assertFalse(list(self.root.rglob('*.apk')))

    def test_play_error_is_not_reported_as_unavailable_or_leaked(self):
        self.client.info.side_effect = PlayError('account@example.com secret token')
        with self.assertRaises(ValidationFailed):
            validate_batch(self.config, self.profiles, self.index, self.client, self.report, 0, 1)
        data = self.report.read_text(encoding='utf-8')
        self.assertNotIn('secret', data)
        self.assertNotIn('account@example.com', data)
        self.assertEqual(json.loads(data)['records'][0]['status'], 'play_error')

    def test_rate_limit_stops_with_explicit_error_and_partial_report(self):
        self.client.info.side_effect = PlayError('Google Play details returned HTTP 429')
        with self.assertRaises(ValidationFailed):
            validate_batch(self.config, self.profiles, self.index, self.client, self.report, 0, 1)
        report = self.report_data()
        self.assertFalse(report['complete'])
        self.assertEqual(report['records'][0]['status'], 'rate_limited')

    @patch('wystore_library.coverage_validation.verify_manifest', side_effect=ProfileIncompatible('min_sdk', minimum_sdk=36))
    def test_verified_incompatibility_is_distinct_from_play_unavailable(self, verify):
        self.client.info.return_value['app'].update(version_code=1, version_name='1')
        self.client.pull.return_value = {'device': {}}
        validate_batch(self.config, self.profiles, self.index, self.client, self.report, 0, 1)
        record = self.report_data()['records'][0]
        self.assertEqual((record['status'], record['reason'], record['minimum_sdk']), ('incompatible', 'min_sdk', 36))

    @patch('wystore_library.coverage_validation.collect_compatibility', return_value={'min_sdk': 26})
    @patch('wystore_library.coverage_validation.verify_manifest', return_value={'files': [{'role': 'base'}]})
    def test_unchanged_published_variant_is_downloaded_and_prior_certificate_checked(self, verify, compatibility):
        self.client.info.return_value['app'].update(version_code=1, version_name='1')
        self.client.pull.return_value = {'device': {}}
        self.index['applications'] = [{'package': 'org.example.app', 'variants': [{'id':'px_9a','version_code':1,'certificate_sha256':['abc']}]}]
        validate_batch(self.config, self.profiles, self.index, self.client, self.report, 0, 1)
        self.assertEqual(self.report_data()['records'][0]['status'], 'verified')
        self.client.pull.assert_called_once()
        self.assertEqual(verify.call_args.args[4], ['abc'])


if __name__ == '__main__':
    unittest.main()
