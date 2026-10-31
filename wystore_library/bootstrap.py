"""One-time operator account bootstrap; never print Google credentials."""
import argparse
import getpass
import os
import re
import secrets
import subprocess


class AuthenticationError(RuntimeError):
    pass


def require_token(response):
    token = response.get("Token")
    if isinstance(token, str) and token:
        return token
    known = {"BadAuthentication", "NeedsBrowser", "CaptchaRequired", "AccountDisabled", "ServiceDisabled"}
    error = response.get("Error")
    reason = error if error in known else "authentication refused"
    raise AuthenticationError(f"Google: {reason}. Complete interactive account verification and retry with GOOGLE_OAUTH_TOKEN.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default="wyrtensi/wystore-library")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        raise SystemExit("Invalid repository.")
    import gpsoauth
    email = os.environ.get("GOOGLE_EMAIL") or input("Google email: ").strip()
    android_id = os.environ.get("GOOGLE_ANDROID_ID") or secrets.token_hex(8)
    oauth_token = os.environ.get("GOOGLE_OAUTH_TOKEN")
    try:
        if oauth_token:
            result = gpsoauth.exchange_token(email, oauth_token, android_id)
        else:
            password = os.environ.get("GOOGLE_PASSWORD") or getpass.getpass("Google password: ")
            result = gpsoauth.perform_master_login(email, password, android_id)
        token = require_token(result)
        # Google may resolve a sign-in alias to a different primary address.
        # Subsequent Play authorization must use the account paired with the token.
        email = result.get("Email", email)
        if not isinstance(email, str) or not re.fullmatch(r"[^@\s]+@[^@\s]+", email):
            raise AuthenticationError("Google returned an invalid account email; no credentials were stored.")
    except AuthenticationError as error:
        raise SystemExit(str(error)) from None
    except Exception:
        # Auth library diagnostics may contain cookies and token-bearing URLs.
        raise SystemExit("Google authentication request failed; no credentials were published.") from None
    for name, value in (("GOOGLE_EMAIL", email), ("GOOGLE_AAS_TOKEN", token)):
        command = ["gh", "secret", "set", name, "--repo", args.repository]
        result = subprocess.run(command, input=value, text=True, capture_output=True, timeout=60)
        if result.returncode:
            raise SystemExit(f"Could not store {name} in GitHub Secrets.")
    print("Account token stored in GitHub Secrets. No secret was written to the repository.")


if __name__ == "__main__":
    main()
