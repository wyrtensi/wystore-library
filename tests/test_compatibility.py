import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from subprocess import CompletedProcess
import zipfile
import hashlib
from wystore_library.compatibility import collect_compatibility, ProfileIncompatible
from wystore_library.profiles import load_profiles

class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = load_profiles(Path('delivery-profiles.json'))['px_9a']
        self.device = {k:self.profile[k] for k in ('sdk','abis','density','locale')}
        with zipfile.ZipFile(self.root/'base.apk','w') as z: z.writestr('lib/arm64-v8a/libx.so', b'x')
        data = (self.root/'base.apk').read_bytes()
        self.manifest = {'files':[{'name':'base.apk','role':'base','split':'','size':len(data),'sha256':hashlib.sha256(data).hexdigest()}]}
    def tools(self, args, **kwargs):
        output = "package: name='org.example.app' versionCode='1'\nsdkVersion:'26'\nlocales: '--_--' 'en' 'ru'\nuses-feature: name='android.hardware.camera'\n"
        if 'xmltree' in args: output = 'E: manifest (line=1)\n'
        return CompletedProcess(args, 0, output, '')
    def test_actual_metadata(self):
        with patch('wystore_library.compatibility.subprocess.run', side_effect=self.tools):
            result = collect_compatibility(self.root, self.manifest, self.profile, self.device)
        self.assertEqual(result['min_sdk'], 26)
        self.assertEqual(result['native_abis'], ['arm64-v8a'])
        self.assertIn('ru', result['languages'])
    def test_required_split_types_and_dependencies_must_be_present(self):
        def tools(args, **kwargs):
            if 'badging' in args: return self.tools(args, **kwargs)
            return CompletedProcess(args, 0, 'E: manifest (line=1)\n  A: android:requiredSplitTypes(0x0101064e)="base__abi"\n  E: uses-split (line=2)\n    A: android:name(0x01010003)="feature"\n', '')
        with patch('wystore_library.compatibility.subprocess.run', side_effect=tools):
            with self.assertRaisesRegex(ValueError, 'Incomplete'): collect_compatibility(self.root, self.manifest, self.profile, self.device)

    def test_digest_and_tool_failure_are_not_unavailability(self):
        self.manifest['files'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'changed'): collect_compatibility(self.root, self.manifest, self.profile, self.device)

    def test_missing_native_libraries_keeps_requested_constraint(self):
        with zipfile.ZipFile(self.root/'base.apk','w'): pass
        data = (self.root/'base.apk').read_bytes()
        self.manifest['files'][0].update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        with patch('wystore_library.compatibility.subprocess.run', side_effect=self.tools):
            result = collect_compatibility(self.root, self.manifest, self.profile, self.device)
        self.assertEqual(result['native_abis'], [])
        self.assertEqual(result['abis'], ['arm64-v8a'])

    def test_gles_typed_aapt2_xml_value_is_retained(self):
        def tools(args, **kwargs):
            if 'badging' in args:
                return self.tools(args, **kwargs)
            return CompletedProcess(args, 0, 'E: manifest (line=1)\n  E: uses-feature (line=2)\n    A: android:glEsVersion(0x01010281)=(type 0x11)0x30002\n', '')
        with patch('wystore_library.compatibility.subprocess.run', side_effect=tools):
            result = collect_compatibility(self.root, self.manifest, self.profile, self.device)
        self.assertEqual(result['gl_es_version'], 0x30002)

    def test_invalid_gles_xml_fails_instead_of_losing_constraint(self):
        def tools(args, **kwargs):
            if 'badging' in args:
                return self.tools(args, **kwargs)
            return CompletedProcess(args, 0, 'E: manifest (line=1)\n  A: android:glEsVersion(0x01010281)=(type 0x11)invalid\n', '')
        with patch('wystore_library.compatibility.subprocess.run', side_effect=tools):
            with self.assertRaisesRegex(ValueError, 'OpenGL ES'): collect_compatibility(self.root, self.manifest, self.profile, self.device)

    def test_device_mismatch_rejected(self):
        self.device['sdk'] = 29
        with self.assertRaises(ValueError): collect_compatibility(self.root, self.manifest, self.profile, self.device)
    def test_abi_incompatible(self):
        with zipfile.ZipFile(self.root/'base.apk','w') as z: z.writestr('lib/x86/libx.so', b'x')
        data = (self.root/'base.apk').read_bytes()
        self.manifest['files'][0].update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        with patch('wystore_library.compatibility.subprocess.run', side_effect=self.tools):
            with self.assertRaises(ProfileIncompatible) as error: collect_compatibility(self.root, self.manifest, self.profile, self.device)
        self.assertEqual(error.exception.reason, 'abi')
