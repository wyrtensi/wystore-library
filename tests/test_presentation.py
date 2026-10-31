import re
import unittest
from wystore_library.presentation import release_presentation


class PresentationTests(unittest.TestCase):
    def test_inline_code_preserves_real_split_and_architecture_names(self):
        app = {'package': 'org.example.app', 'title': 'Example', 'version_code': 2}
        verified = {'files': [{'name': 'split_config.arm64_v8a.apk', 'size': 3, 'sha256': 'a' * 64}],
                    'certificate_sha256': ['b' * 64]}
        _, notes = release_presentation(app, 'px_9a', {'abis': ['x86_64']}, verified)
        self.assertIn('`split_config.arm64_v8a.apk`', notes)
        self.assertIn('`x86_64`', notes)
        self.assertTrue(all(r'\_' not in span for span in re.findall(r'`([^`\n]*)`', notes)))
