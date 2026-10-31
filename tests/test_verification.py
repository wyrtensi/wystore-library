import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
from wystore_library.verification import inspect_apk, verify_manifest
from wystore_library import verification

class ProfileInspectionTests(unittest.TestCase):
    def inspect(self, output, sdk=None):
        from subprocess import CompletedProcess
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output, ''), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'", '')]) as run:
            result = verification.inspect_apk_details('base.apk', sdk)
        self.assertEqual(run.call_args_list[0].args[0], ['apksigner', 'verify', '--verbose', '--print-certs', 'base.apk'])
        return result

    def lines(self, label, sha256, sha1):
        return label + ' certificate SHA-256 digest: ' + sha256 * 64 + '\n' + label + ' certificate SHA-1 digest: ' + sha1 * 40

    def test_selects_sdk_signer_and_marks_scope(self):
        output = self.lines('V3.0 Signer: (minSdkVersion=24, maxSdkVersion=32)', 'a', 'b') + '\n' + self.lines('V3.1 Signer: (minSdkVersion=33, maxSdkVersion=100)', 'c', 'd')
        result = self.inspect(output, 35)
        self.assertEqual((result.certificate_sha256, result.certificate_sha1, result.certificate_scope), ({'c'*64}, {'d'*40}, {'mode':'android-sdk', 'sdk':35}))
        result = self.inspect(output)
        self.assertEqual((result.certificate_sha256, result.certificate_scope), ({'a'*64, 'c'*64}, None))

    def test_same_identity_across_ranges_does_not_mark_scope(self):
        output = self.lines('V3.0 Signer: (minSdkVersion=24, maxSdkVersion=32)', 'a', 'b') + '\n' + self.lines('V3.1 Signer: (minSdkVersion=33, maxSdkVersion=100)', 'a', 'b')
        self.assertIsNone(self.inspect(output, 35).certificate_scope)

    def test_invalid_or_incomplete_extra_signer_is_rejected(self):
        good = self.lines('Signer #1', 'a', 'b')
        for extra in [self.lines('V3.1 Signer: (minSdkVersion=x, maxSdkVersion=100)', 'c', 'd'), self.lines('V3.1 Signer: (minSdkVersion=50, maxSdkVersion=33)', 'c', 'd'), 'V3.1 Signer: (minSdkVersion=33, maxSdkVersion=100) certificate SHA-256 digest: ' + 'c'*64, 'Signer #2 certificate SHA-1 digest: ' + 'd'*40]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.inspect(good + '\n' + extra, 35)

    def test_no_signer_covers_sdk_is_rejected(self):
        with self.assertRaises(ValueError):
            self.inspect(self.lines('V3.0 Signer: (minSdkVersion=24, maxSdkVersion=32)', 'a', 'b'), 35)

class ProfileManifestTests(unittest.TestCase):
    def test_sdk_must_match_manifest(self):
        manifest = {'schema':'playfetch/v1', 'app':{'package':'org.example.app', 'version_code':2}, 'device':{'sdk':34}, 'files':[{}]}
        for sdk in (35, 0, True, '35'):
            with self.subTest(sdk=sdk), self.assertRaises(ValueError):
                verify_manifest(manifest, '.', 'org.example.app', 2, None, sdk=sdk)
        del manifest['device']
        with self.assertRaises(ValueError):
            verify_manifest(manifest, '.', 'org.example.app', 2, None, sdk=35)

    def test_scoped_manifest_records_signers_and_checks_previous(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / 'base.apk').write_bytes(b'apk')
            h = hashlib.sha256(b'apk').hexdigest()
            manifest = {'schema':'playfetch/v1', 'app':{'package':'org.example.app', 'version_code':2}, 'device':{'sdk':35}, 'files':[{'name':'base.apk','role':'base','size':3,'local':{'sha256':h},'play_sha256':h}]}
            details = verification.ApkInspection('org.example.app', 2, '', {'a'*64, 'c'*64}, {'b'*40, 'd'*40}, {'mode':'android-sdk','sdk':35})
            with patch('wystore_library.verification.inspect_apk_details', return_value=details):
                with self.assertRaisesRegex(ValueError, 'changed'):
                    verify_manifest(manifest, tmp, 'org.example.app', 2, ['a'*64], sdk=35)
                result = verify_manifest(manifest, tmp, 'org.example.app', 2, None, sdk=35)
                self.assertEqual(result['certificate_sha256'], ['a'*64, 'c'*64])
                self.assertEqual(result['certificate_scope'], {'mode':'android-sdk', 'sdk':35})

    def test_split_signers_must_match_and_scope_from_any_split_is_retained(self):
        with TemporaryDirectory() as tmp:
            h = hashlib.sha256(b'apk').hexdigest()
            files = []
            for name, role in [('base.apk', 'base'), ('split.apk', 'split')]:
                (Path(tmp) / name).write_bytes(b'apk')
                record = {'name':name, 'role':role, 'size':3, 'local':{'sha256':h}, 'play_sha256':h}
                if role == 'split': record['split'] = 'config.en'
                files.append(record)
            manifest = {'schema':'playfetch/v1', 'app':{'package':'org.example.app', 'version_code':2}, 'device':{'sdk':35}, 'files':files}
            base = verification.ApkInspection('org.example.app', 2, '', {'a'*64}, {'b'*40})
            split = verification.ApkInspection('org.example.app', 2, 'config.en', {'a'*64}, {'b'*40}, {'mode':'android-sdk', 'sdk':35})
            with patch('wystore_library.verification.inspect_apk_details', side_effect=[base, split]):
                self.assertEqual(verify_manifest(manifest, tmp, 'org.example.app', 2, None, sdk=35)['certificate_scope'], {'mode':'android-sdk', 'sdk':35})
            split.certificate_sha256 = {'c'*64}
            split.certificate_sha1 = {'d'*40}
            with patch('wystore_library.verification.inspect_apk_details', side_effect=[base, split]):
                with self.assertRaisesRegex(ValueError, 'split signatures differ'):
                    verify_manifest(manifest, tmp, 'org.example.app', 2, None, sdk=35)

class InspectionTests(unittest.TestCase):
    def test_failed_apksigner_rejects_apk(self):
        from subprocess import CompletedProcess
        with patch('wystore_library.verification.subprocess.run', return_value=CompletedProcess([], 1, '', 'invalid signature')):
            with self.assertRaisesRegex(ValueError, 'APK inspection failed: apksigner'):
                inspect_apk('base.apk')

    def test_rotated_signers_include_each_sdk_range_and_exclude_other_identities(self):
        from subprocess import CompletedProcess
        output = '\n'.join([
            'V3.0 Signer: (minSdkVersion=24, maxSdkVersion=32) certificate SHA-256 digest: ' + 'a' * 64,
            'V3.0 Signer: (minSdkVersion=24, maxSdkVersion=32) certificate SHA-1 digest: ' + 'b' * 40,
            'V3.1 Signer: (minSdkVersion=33, maxSdkVersion=2147483647) certificate SHA-256 digest: ' + 'c' * 64,
            'V3.1 Signer: (minSdkVersion=33, maxSdkVersion=2147483647) certificate SHA-1 digest: ' + 'd' * 40,
            'V3.1 Signer: (minSdkVersion=33, maxSdkVersion=2147483647) public key SHA-256 digest: ' + 'e' * 64,
            'Source Stamp Signer: (minSdkVersion=33, maxSdkVersion=2147483647) certificate SHA-256 digest: ' + 'f' * 64,
            'Source Stamp Signer: (minSdkVersion=33, maxSdkVersion=2147483647) certificate SHA-1 digest: ' + 'f' * 40,
        ])
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output, ''), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'", '')]):
            self.assertEqual(inspect_apk('base.apk'), ('org.example.app', 2, '', {'a' * 64, 'c' * 64}, {'b' * 40, 'd' * 40}))

    def test_older_aosp_sdk_range_signer_is_recognized(self):
        from subprocess import CompletedProcess
        prefix = 'Signer (minSdkVersion=33, maxSdkVersion=2147483647) certificate '
        output = prefix + 'SHA-256 digest: ' + 'a' * 64 + '\n' + prefix + 'SHA-1 digest: ' + 'b' * 40
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output, ''), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'", '')]):
            self.assertEqual(inspect_apk('base.apk')[3:], ({'a' * 64}, {'b' * 40}))

    def test_malformed_sdk_range_does_not_count_as_signer(self):
        from subprocess import CompletedProcess
        for annotation in ('minSdkVersion=x, maxSdkVersion=32', 'minSdkVersion=24, maxSdkVersion=', 'maxSdkVersion=32, minSdkVersion=24'):
            with self.subTest(annotation=annotation):
                prefix = 'V3.0 Signer: (' + annotation + ') certificate '
                output = prefix + 'SHA-256 digest: ' + 'a' * 64 + '\n' + prefix + 'SHA-1 digest: ' + 'b' * 40
                with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output, ''), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'", '')]):
                    with self.assertRaises(ValueError):
                        inspect_apk('base.apk')

    def test_split_metadata_uses_aapt2_without_resolving_legacy_label_references(self):
        from subprocess import CompletedProcess
        def tools(args, **kwargs):
            if args[0] == 'apksigner':
                return CompletedProcess(args, 0, 'Signer #1 certificate SHA-256 digest: ' + 'a' * 64 + '\nSigner #1 certificate SHA-1 digest: ' + 'b' * 40, '')
            if args[:3] == ['aapt2', 'dump', 'badging']:
                return CompletedProcess(args, 0, "package: name='org.example.app' versionCode='2' split='chrome'", '')
            return CompletedProcess(args, 1, '', "ERROR getting 'android:label' attribute: attribute value reference does not exist")
        with patch('wystore_library.verification.subprocess.run', side_effect=tools):
            try:
                result = inspect_apk('split_chrome.apk')
            except ValueError as error:
                self.fail('Supported split metadata was rejected: ' + str(error))
        self.assertEqual(result[:3], ('org.example.app', 2, 'chrome'))

    def test_build_tools_37_scheme_signer_excludes_source_stamp_and_public_key(self):
        from subprocess import CompletedProcess
        output = '\n'.join([
            'V3.0 Signer: certificate SHA-256 digest: ' + 'a' * 64,
            'V3.0 Signer: certificate SHA-1 digest: ' + 'b' * 40,
            'V3.0 Signer: public key SHA-256 digest: ' + 'e' * 64,
            'Source Stamp Signer: certificate SHA-256 digest: ' + 'c' * 64,
            'Source Stamp Signer: certificate SHA-1 digest: ' + 'd' * 40,
        ])
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output, ''), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'", '')]):
            try:
                result = inspect_apk('base.apk')
            except ValueError as error:
                self.fail('Supported SDK 37 signer output was rejected: ' + str(error))
        self.assertEqual(result, ('org.example.app', 2, '', {'a' * 64}, {'b' * 40}))

    def test_source_stamp_alone_never_counts_as_an_app_signer(self):
        from subprocess import CompletedProcess
        output = 'Source Stamp Signer: certificate SHA-256 digest: ' + 'a' * 64 + '\nSource Stamp Signer: certificate SHA-1 digest: ' + 'b' * 40
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output, ''), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'", '')]):
            with self.assertRaises(ValueError):
                inspect_apk('base.apk')

    def test_supported_tool_output_retains_package_version_and_both_digests(self):
        from subprocess import CompletedProcess
        output = 'Signer #1 certificate SHA-256 digest: ' + 'a' * 64 + '\nSigner #1 certificate SHA-1 digest: ' + 'b' * 40
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2' split='config.en'")]):
            self.assertEqual(inspect_apk('split.apk'), ('org.example.app', 2, 'config.en', {'a' * 64}, {'b' * 40}))

    def test_unsupported_tool_output_reports_structure_without_raw_values(self):
        from subprocess import CompletedProcess
        output = 'Signer #1 (SDK=35) certificate SHA-256 digest: private-account-token\nSigner #1 certificate DN: private-account-email'
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'")]):
            with self.assertRaises(ValueError) as error:
                inspect_apk('base.apk')
        self.assertIn('sha256=0', str(error.exception))
        self.assertIn('sha1=0', str(error.exception))
        self.assertIn('version_code=True', str(error.exception))
        self.assertIn('Signer #1 (SDK=35) certificate SHA-256 digest', str(error.exception))
        self.assertNotIn('private-account', str(error.exception))

    def test_diagnostics_distinguish_empty_stdout_from_certificate_lines_on_stderr(self):
        from subprocess import CompletedProcess
        stderr = 'Signer #1 certificate SHA-256 digest: private-account-token\nSigner #1 certificate SHA-1 digest: private-account-email'
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, '', stderr), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'", '')]):
            with self.assertRaises(ValueError) as error:
                inspect_apk('base.apk')
        message = str(error.exception)
        self.assertIn('"stdout": {"bytes": 0', message)
        self.assertIn('"sha256_mentions": 1', message)
        self.assertIn('"sha1_mentions": 1', message)
        self.assertNotIn('private-account', message)

    def test_diagnostic_labels_keep_signer_scopes_before_digest_separator(self):
        from subprocess import CompletedProcess
        output = 'Signer #1: certificate SHA-256 digest: private-account-token'
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output, ''), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'", '')]):
            with self.assertRaises(ValueError) as error:
                inspect_apk('base.apk')
        self.assertIn('Signer #1: certificate SHA-256 digest', str(error.exception))
        self.assertNotIn('private-account', str(error.exception))

class VerificationTests(unittest.TestCase):
    def test_rotated_signer_is_recorded_without_listing_certificates(self):
        from subprocess import CompletedProcess
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'base.apk'; path.write_bytes(b'apk')
            file_hash = hashlib.sha256(b'apk').hexdigest()
            manifest = {'schema': 'playfetch/v1', 'app': {'package': 'org.example.app', 'version_code': 2}, 'device': {'sdk': 35}, 'files': [{'name': 'base.apk', 'role': 'base', 'size': 3, 'local': {'sha256': file_hash}, 'play_sha256': file_hash}]}
            output = '\n'.join([
                'V3.0 Signer: (minSdkVersion=24, maxSdkVersion=32) certificate SHA-256 digest: ' + 'a' * 64,
                'V3.0 Signer: (minSdkVersion=24, maxSdkVersion=32) certificate SHA-1 digest: ' + 'b' * 40,
                'V3.1 Signer: (minSdkVersion=33, maxSdkVersion=2147483647) certificate SHA-256 digest: ' + 'c' * 64,
                'V3.1 Signer: (minSdkVersion=33, maxSdkVersion=2147483647) certificate SHA-1 digest: ' + 'd' * 40,
            ])
            with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([], 0, output, ''), CompletedProcess([], 0, "package: name='org.example.app' versionCode='2'", '')]):
                result = verify_manifest(manifest, tmp, 'org.example.app', 2, None, sdk=35)
                self.assertEqual(result['certificate_sha256'], ['c' * 64])
                self.assertEqual(result['certificate_scope'], {'mode': 'android-sdk', 'sdk': 35})

    def test_manifest_version_is_not_trusted(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'base.apk'; path.write_bytes(b'apk')
            digest = hashlib.sha256(b'apk').hexdigest()
            manifest = {'schema': 'playfetch/v1', 'app': {'package': 'org.example.app', 'version_code': 2}, 'files': [{'name':'base.apk','role':'base','size':3,'local':{'sha256':digest},'play_sha256':digest}]}
            with patch('wystore_library.verification.inspect_apk_details', return_value=verification.ApkInspection('org.example.app', 1, '', {'a'*64}, {'b'*40})):
                with self.assertRaises(ValueError): verify_manifest(manifest, Path(tmp), 'org.example.app', 2, None)
    def test_public_record_excludes_raw_secrets(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'base.apk'; path.write_bytes(b'apk')
            digest = hashlib.sha256(b'apk').hexdigest()
            manifest = {'schema': 'playfetch/v1', 'source': {'account':'secret@example.com'}, 'app': {'package':'org.example.app','version_code':2}, 'files':[{'name':'base.apk','role':'base','size':3,'local':{'sha256':digest},'play_sha256':digest,'url':'secret'}]}
            with patch('wystore_library.verification.inspect_apk_details', return_value=verification.ApkInspection('org.example.app',2,'',{'a'*64},{'b'*40})):
                result = verify_manifest(manifest, Path(tmp), 'org.example.app', 2, None)
            self.assertNotIn('secret', str(result))
import hashlib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from wystore_library.verification import verify_manifest

class FailureTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); (self.root / 'base.apk').write_bytes(b'apk')
        h = hashlib.sha256(b'apk').hexdigest()
        self.manifest = {'schema': 'playfetch/v1', 'app': {'package':'org.example.app','version_code':2}, 'files':[{'name':'base.apk','role':'base','size':3,'local':{'sha256':h},'play_sha256':h}]}
        self.inspect = patch('wystore_library.verification.inspect_apk_details', return_value=verification.ApkInspection('org.example.app',2,'',{'a'*64},{'b'*40}))
        self.inspect.start(); self.addCleanup(self.inspect.stop)
    def verify(self, previous=None):
        return verify_manifest(self.manifest, self.root, 'org.example.app', 2, previous)
    def test_google_hash_mismatch_rejected_even_if_verified(self):
        self.manifest['files'][0].update(play_sha256='f'*64, verified=True)
        with self.assertRaises(ValueError): self.verify()
    def test_wrong_apk_package_rejected(self):
        self.inspect.stop()
        with patch('wystore_library.verification.inspect_apk_details', return_value=verification.ApkInspection('org.other',2,'',{'a'*64},{'b'*40})):
            with self.assertRaises(ValueError): self.verify()
    def test_changed_signer_rejected(self):
        with self.assertRaises(ValueError): self.verify(['c'*64])
    def test_unknown_file_role_rejected(self):
        self.manifest['files'][0]['role'] = 'obb'
        with self.assertRaises(ValueError): self.verify()
    def test_path_traversal_rejected(self):
        self.manifest['files'][0]['name'] = '../base.apk'
        with self.assertRaises(ValueError): self.verify()
    def test_unknown_manifest_schema_rejected(self):
        self.manifest['schema'] = 'unexpected'
        with self.assertRaises(ValueError): self.verify()
    def test_nondict_file_record_rejected(self):
        self.manifest['schema'] = 'playfetch/v1'; self.manifest['files'] = ['unexpected']
        with self.assertRaises(ValueError): self.verify()
