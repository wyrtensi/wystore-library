import contextlib
import io
import os
import sys
import types
import unittest
from unittest.mock import patch
from wystore_library.bootstrap import AuthenticationError, main, require_token


class BootstrapTests(unittest.TestCase):
    def test_success_returns_token_without_treating_other_fields_as_credentials(self):
        self.assertEqual(require_token({"Token": "example-token", "SID": "other-secret"}), "example-token")

    def test_browser_challenge_has_actionable_safe_error(self):
        with self.assertRaisesRegex(AuthenticationError, "NeedsBrowser"):
            require_token({"Error": "NeedsBrowser", "Url": "https://example.test/?secret=private"})

    def test_unknown_response_never_exposes_upstream_secrets(self):
        with self.assertRaises(AuthenticationError) as error:
            require_token({"Error": "token=private", "SID": "other-secret"})
        self.assertNotIn("private", str(error.exception))
        self.assertNotIn("other-secret", str(error.exception))

    def test_empty_token_is_not_success(self):
        with self.assertRaises(AuthenticationError):
            require_token({"Token": ""})

    def run_bootstrap(self, response, stored):
        def store_secret(command, *, input, **kwargs):
            stored[command[3]] = input
            return types.SimpleNamespace(returncode=0)

        provider = types.SimpleNamespace(exchange_token=lambda *args: response)
        with patch.dict(os.environ, {"GOOGLE_EMAIL": "alias@example.test", "GOOGLE_OAUTH_TOKEN": "one-time-token"}, clear=True), \
                patch.dict(sys.modules, {"gpsoauth": provider}), \
                patch.object(sys, "argv", ["bootstrap"]), \
                patch("wystore_library.bootstrap.subprocess.run", side_effect=store_secret), \
                contextlib.redirect_stdout(io.StringIO()):
            main()

    def test_bootstrap_pairs_token_with_google_canonical_account_email(self):
        stored = {}
        self.run_bootstrap({"Token": "new-master-token", "Email": "canonical@example.test"}, stored)
        self.assertEqual(stored, {"GOOGLE_EMAIL": "canonical@example.test", "GOOGLE_AAS_TOKEN": "new-master-token"})

    def test_bootstrap_keeps_requested_email_when_google_omits_it(self):
        stored = {}
        self.run_bootstrap({"Token": "new-master-token"}, stored)
        self.assertEqual(stored["GOOGLE_EMAIL"], "alias@example.test")

    def test_invalid_google_account_email_is_not_published_or_saved(self):
        for value in ("", "invalid private value", "private@example.test\nextra", None):
            with self.subTest(value=value):
                stored = {}
                with self.assertRaises(SystemExit) as error:
                    self.run_bootstrap({"Token": "new-master-token", "Email": value}, stored)
                self.assertEqual(stored, {})
                self.assertNotIn("private", str(error.exception))
                self.assertNotIn("new-master-token", str(error.exception))


if __name__ == "__main__":
    unittest.main()
