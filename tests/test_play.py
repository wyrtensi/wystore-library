import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


class PlayClientTests(unittest.TestCase):
    def test_google_rejection_reports_only_a_known_reason(self):
        from wystore_library.play import safe_failure_reason

        message = "error: google auth rejected the AAS token: BadAuthentication account@example.test private-token"
        self.assertEqual(safe_failure_reason(message), "Google rejected account authentication (BadAuthentication)")

    def test_endpoint_failure_excludes_response_body_and_account(self):
        from wystore_library.play import safe_failure_reason

        message = "error: play checkin: HTTP 403: account@example.test secret-cookie"
        self.assertEqual(safe_failure_reason(message), "Google checkin returned HTTP 403")

    def test_unknown_diagnostics_stay_private(self):
        from wystore_library.play import safe_failure_reason

        self.assertEqual(safe_failure_reason("private-token account@example.test"), "upstream diagnostic withheld")

    def test_missing_credentials_never_starts_anonymous_backend(self):
        from wystore_library.play import PlayClient, PlayError

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(PlayError, "GOOGLE_AAS_TOKEN"):
                PlayClient(binary="missing-program")

    def test_explicit_account_and_metadata_without_secret_arguments(self):
        from wystore_library.play import PlayClient

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "backend.py"
            script.write_text(
                "import json,os,sys,pathlib\n"
                "c=json.loads(pathlib.Path(os.environ['PLAYFETCH_CREDENTIALS']).read_text())\n"
                "assert c['email']=='account@example.test' and c['aas_token']=='private-token'\n"
                "assert '-account' in sys.argv and sys.argv[sys.argv.index('-account')+1]=='default'\n"
                "assert 'private-token' not in str(sys.argv)\n"
                "print(json.dumps({'app':{'package':sys.argv[2], 'version_code':42}}))\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"GOOGLE_EMAIL": "account@example.test", "GOOGLE_AAS_TOKEN": "private-token"}):
                with PlayClient(binary=[sys.executable, str(script)]) as client:
                    credentials = client.credentials_path
                    result = client.info("org.example.app", "px_9a")
                    self.assertEqual(result["app"]["version_code"], 42)
                    self.assertTrue(credentials.is_file())
                    if os.name != "nt":
                        self.assertEqual(credentials.stat().st_mode & 0o777, 0o600)
                self.assertFalse(credentials.exists())

    def test_profiles_use_builtin_and_isolated_sessions_with_overrides(self):
        from wystore_library.play import PlayClient
        from subprocess import CompletedProcess
        with patch.dict(os.environ, {"GOOGLE_EMAIL": "account@example.test", "GOOGLE_AAS_TOKEN": "private-token"}):
            with PlayClient() as client, patch('wystore_library.play.subprocess.run', return_value=CompletedProcess([], 0, '{"app":{}}', '')) as run:
                client.info('org.example.app', 'legacy_armv7_ru')
                args = run.call_args.args[0]
                for flag, expected in [('-profile','op_3'), ('-sdk','26'), ('-abi','armeabi-v7a'), ('-dpi','320'), ('-locale','ru_RU')]:
                    self.assertEqual(args[args.index(flag)+1], expected)
                self.assertTrue(args[args.index('-session')+1].endswith('session-legacy_armv7_ru.json'))

    def test_backend_error_cannot_publish_raw_diagnostics(self):
        from wystore_library.play import PlayClient, PlayError

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "backend.py"
            script.write_text("import sys\nprint('private-token secret-cookie',file=sys.stderr)\nsys.exit(7)\n")
            with patch.dict(os.environ, {"GOOGLE_EMAIL": "account@example.test", "GOOGLE_AAS_TOKEN": "private-token"}):
                with PlayClient(binary=[sys.executable, str(script)]) as client:
                    with self.assertRaises(PlayError) as error:
                        client.info("org.example.app", "px_9a")
                    self.assertNotIn("private-token", str(error.exception))
                    self.assertNotIn("secret-cookie", str(error.exception))
                    self.assertIn("7", str(error.exception))

    def test_pull_reads_manifest_without_printing_download_output(self):
        from wystore_library.play import PlayClient

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "backend.py"
            script.write_text(
                "import json,pathlib,sys\n"
                "out=pathlib.Path(sys.argv[sys.argv.index('-out')+1]);out.mkdir(parents=True,exist_ok=True)\n"
                "assert sys.argv[sys.argv.index('-vc')+1]=='42'\n"
                "(out/'manifest.json').write_text(json.dumps({'schema':'playfetch/v1','files':[]}))\n"
                "print('secret backend progress')\n"
            )
            with patch.dict(os.environ, {"GOOGLE_EMAIL": "account@example.test", "GOOGLE_AAS_TOKEN": "private-token"}):
                with PlayClient(binary=[sys.executable, str(script)]) as client:
                    result = client.pull("org.example.app", "px_9a", 42, Path(directory) / "download")
                    self.assertEqual(result["schema"], "playfetch/v1")


if __name__ == "__main__":
    unittest.main()
