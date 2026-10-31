import re
import unittest
from wystore_library.presentation import release_presentation


class PresentationTests(unittest.TestCase):
    def test_profile_scoped_signing_identity_is_explicit(self):
        app = {'package': 'org.example.app', 'version_code': 2}
        verified = {'files': [], 'certificate_sha256': ['b' * 64],
                    'certificate_scope': {'mode': 'android-sdk', 'sdk': 35}}
        _, notes = release_presentation(app, 'px_9a', {'sdk': 35}, verified)
        self.assertIn('Recorded signing identity: **Android SDK 35**', notes)
        self.assertIn('cryptographic', notes)
        self.assertIn('Listing certificate metadata is not used for verification', notes)

    def test_legacy_full_signer_verification_keeps_existing_release_representation(self):
        app = {'package': 'org.example.app', 'version_code': 2}
        verified = {'files': [], 'certificate_sha256': ['b' * 64]}
        _, notes = release_presentation(app, 'px_9a', {'sdk': 35}, verified)
        self.assertIn('### Signing certificate SHA-256\n\n- `' + 'b' * 64 + '`', notes)
        self.assertNotIn('Recorded signing identity:', notes)

    def test_inline_code_preserves_real_split_and_architecture_names(self):
        app = {'package': 'org.example.app', 'title': 'Example', 'version_code': 2}
        verified = {'files': [{'name': 'split_config.arm64_v8a.apk', 'size': 3, 'sha256': 'a' * 64}],
                    'certificate_sha256': ['b' * 64]}
        _, notes = release_presentation(app, 'px_9a', {'abis': ['x86_64']}, verified)
        self.assertIn('`split_config.arm64_v8a.apk`', notes)
        self.assertIn('`x86_64`', notes)
        self.assertTrue(all(r'\_' not in span for span in re.findall(r'`([^`\n]*)`', notes)))
