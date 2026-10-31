import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
from wystore_library.verification import inspect_apk, verify_manifest

class InspectionTests(unittest.TestCase):
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
    def test_manifest_version_is_not_trusted(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'base.apk'; path.write_bytes(b'apk')
            digest = hashlib.sha256(b'apk').hexdigest()
            manifest = {'schema': 'playfetch/v1', 'app': {'package': 'org.example.app', 'version_code': 2}, 'files': [{'name':'base.apk','role':'base','size':3,'local':{'sha256':digest},'play_sha256':digest}]}
            with patch('wystore_library.verification.inspect_apk', return_value=('org.example.app', 1, '', {'a'*64}, {'b'*40})):
                with self.assertRaises(ValueError): verify_manifest(manifest, Path(tmp), 'org.example.app', 2, ['a'*64], None)
    def test_public_record_excludes_raw_secrets(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'base.apk'; path.write_bytes(b'apk')
            digest = hashlib.sha256(b'apk').hexdigest()
            manifest = {'schema': 'playfetch/v1', 'source': {'account':'secret@example.com'}, 'app': {'package':'org.example.app','version_code':2}, 'files':[{'name':'base.apk','role':'base','size':3,'local':{'sha256':digest},'play_sha256':digest,'url':'secret'}]}
            with patch('wystore_library.verification.inspect_apk', return_value=('org.example.app',2,'',{'a'*64},{'b'*40})):
                result = verify_manifest(manifest, Path(tmp), 'org.example.app', 2, ['a'*64], None)
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
        self.inspect = patch('wystore_library.verification.inspect_apk', return_value=('org.example.app',2,'',{'a'*64},{'b'*40}))
        self.inspect.start(); self.addCleanup(self.inspect.stop)
    def verify(self, previous=None):
        return verify_manifest(self.manifest, self.root, 'org.example.app', 2, ['a'*64], previous)
    def test_google_hash_mismatch_rejected_even_if_verified(self):
        self.manifest['files'][0].update(play_sha256='f'*64, verified=True)
        with self.assertRaises(ValueError): self.verify()
    def test_wrong_apk_package_rejected(self):
        self.inspect.stop()
        with patch('wystore_library.verification.inspect_apk', return_value=('org.other',2,'',{'a'*64},{'b'*40})):
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
