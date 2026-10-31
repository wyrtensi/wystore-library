import unittest
from wystore_library.bootstrap import AuthenticationError, require_token


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


if __name__ == "__main__":
    unittest.main()
