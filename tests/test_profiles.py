import unittest
from pathlib import Path
from wystore_library.profiles import load_profiles, profile_fingerprint

class ProfilesTests(unittest.TestCase):
    def test_registry_and_fingerprint(self):
        profiles = load_profiles(Path('delivery-profiles.json'))
        self.assertEqual(len(profiles), 6)
        self.assertEqual(profiles['legacy_armv7_ru']['abis'], ['armeabi-v7a'])
        self.assertEqual(profiles['legacy_arm64_en']['base'], 'op_3')
        self.assertEqual(profiles['legacy_arm64_ru']['base'], 'op_3')
        self.assertEqual(len(profile_fingerprint(profiles['px_9a'])), 64)
        self.assertNotEqual(profile_fingerprint(profiles['px_9a']), profile_fingerprint(profiles['modern_arm64_ru']))
    def test_reject_invalid(self):
        with self.assertRaises(ValueError): profile_fingerprint({'id':'x'})

class MinimumSdkTests(unittest.TestCase):
    def test_minimum_above_requested_sdk_is_typed_even_without_selected_signer(self):
        from subprocess import CompletedProcess
        from unittest.mock import patch
        from wystore_library.verification import inspect_apk_details
        from wystore_library.compatibility import ProfileIncompatible
        signature = 'V3.1 Signer: (minSdkVersion=33, maxSdkVersion=100) certificate SHA-256 digest: ' + 'a'*64 + '\nV3.1 Signer: (minSdkVersion=33, maxSdkVersion=100) certificate SHA-1 digest: ' + 'b'*40
        badging = "package: name='org.example.app' versionCode='1'\nminSdkVersion:'33'"
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([],0,signature,''), CompletedProcess([],0,badging,'')]):
            with self.assertRaises(ProfileIncompatible) as error: inspect_apk_details('base.apk', 29)
        self.assertEqual((error.exception.reason, error.exception.minimum_sdk), ('min_sdk',33))

    def test_malformed_signer_does_not_become_unavailability(self):
        from subprocess import CompletedProcess
        from unittest.mock import patch
        from wystore_library.verification import inspect_apk_details
        from wystore_library.compatibility import ProfileIncompatible
        badging = "package: name='org.example.app' versionCode='1'\nminSdkVersion:'33'"
        with patch('wystore_library.verification.subprocess.run', side_effect=[CompletedProcess([],0,'broken',''), CompletedProcess([],0,badging,'')]):
            with self.assertRaises(ValueError) as error: inspect_apk_details('base.apk', 29)
        self.assertNotIsInstance(error.exception, ProfileIncompatible)

class IncompatibleSetVerificationTests(unittest.TestCase):
    def test_wrong_package_is_not_reported_as_unavailable(self):
        import hashlib
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from wystore_library import verification
        from wystore_library.compatibility import ProfileIncompatible
        with TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'base.apk').write_bytes(b'base')
            digest = hashlib.sha256(b'base').hexdigest()
            manifest = {'schema':'playfetch/v1', 'device':{'sdk':29}, 'app':{'package':'org.example.app','version_code':1}, 'files':[{'name':'base.apk','role':'base','size':4,'local':{'sha256':digest},'play_sha256':digest}]}
            other = verification.ApkInspection('org.example.other', 1, '', {'a'*64}, {'b'*40}, min_sdk=33)
            with patch('wystore_library.verification.inspect_apk_details', side_effect=[ProfileIncompatible('min_sdk',33), other]):
                with self.assertRaisesRegex(ValueError, 'package or version mismatch') as error:
                    verification.verify_manifest(manifest, root, 'org.example.app', 1, None, sdk=29)
            self.assertNotIsInstance(error.exception, ProfileIncompatible)

    def test_corrupt_split_is_not_reported_as_unavailable(self):
        import hashlib
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from wystore_library import verification
        from wystore_library.compatibility import ProfileIncompatible
        with TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'base.apk').write_bytes(b'base'); (root/'split.apk').write_bytes(b'broken')
            digest=hashlib.sha256(b'base').hexdigest()
            files=[{'name':'base.apk','role':'base','size':4,'local':{'sha256':digest},'play_sha256':digest}, {'name':'split.apk','role':'split','split':'config.en','size':1,'local':{'sha256':digest},'play_sha256':digest}]
            manifest={'schema':'playfetch/v1','device':{'sdk':29},'app':{'package':'org.example.app','version_code':1},'files':files}
            base=verification.ApkInspection('org.example.app',1,'',{'a'*64},{'b'*40},min_sdk=33)
            with patch('wystore_library.verification.inspect_apk_details', side_effect=[ProfileIncompatible('min_sdk',33),base]):
                with self.assertRaisesRegex(ValueError, 'hash or size') as error: verification.verify_manifest(manifest, root, 'org.example.app', 1, None, sdk=29)
            self.assertNotIsInstance(error.exception, ProfileIncompatible)
