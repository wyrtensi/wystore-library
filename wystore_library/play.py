"""Run pinned playfetch with private operator credentials and safe diagnostics."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


class PlayError(RuntimeError):
    """An actionable backend failure without secret-bearing upstream output."""


def safe_failure_reason(diagnostic: str) -> str:
    """Report recognized failure categories, never upstream response text."""
    known = "BadAuthentication|NeedsBrowser|CaptchaRequired|AccountDisabled|ServiceDisabled|DeviceManagementRequired"
    match = re.search(r"google auth rejected the AAS token: (" + known + r")\b", diagnostic)
    if match:
        return "Google rejected account authentication (" + match.group(1) + ")"
    match = re.search(r"play (checkin|details|uploadDeviceConfig|delivery|purchase|toc): HTTP ([1-5][0-9]{2})\b", diagnostic)
    if match:
        return "Google " + match.group(1) + " returned HTTP " + match.group(2)
    match = re.search(r"google auth returned HTTP ([1-5][0-9]{2})\b", diagnostic)
    if match:
        return "Google authorization returned HTTP " + match.group(1)
    if "DF-DFERH-01" in diagnostic:
        return "Google Play reported DF-DFERH-01"
    if "no accounts are stored" in diagnostic or "no stored account called" in diagnostic:
        return "the configured private account could not be loaded"
    if "terms of service" in diagnostic.lower():
        return "Google Play terms require account-owner action"
    return "upstream diagnostic withheld"


class PlayClient:
    def __init__(self, binary: str | list[str] = "playfetch"):
        email = os.environ.get("GOOGLE_EMAIL", "").strip()
        token = os.environ.get("GOOGLE_AAS_TOKEN", "").strip()
        if not email or not token:
            raise PlayError("GOOGLE_EMAIL and GOOGLE_AAS_TOKEN are required; run account bootstrap first.")
        self._binary = [binary] if isinstance(binary, str) else list(binary)
        self._temporary = tempfile.TemporaryDirectory(prefix="wystore-library-auth-")
        self.credentials_path = Path(self._temporary.name) / "credentials.json"
        with open(self.credentials_path, "x", encoding="utf-8", opener=self._private_open) as stream:
            json.dump({"email": email, "aas_token": token}, stream)
        self._environment = dict(os.environ)
        # The backend needs only its credential file. Do not pass the password
        # or the master token as inherited environment variables as well.
        for name in ("GOOGLE_EMAIL", "GOOGLE_PASSWORD", "GOOGLE_AAS_TOKEN", "GOOGLE_OAUTH_TOKEN"):
            self._environment.pop(name, None)
        self._environment["PLAYFETCH_CREDENTIALS"] = str(self.credentials_path)
        self._environment["XDG_CACHE_HOME"] = str(Path(self._temporary.name) / "cache")

    @staticmethod
    def _private_open(path: str, flags: int) -> int:
        return os.open(path, flags, 0o600)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._temporary.cleanup()

    def _run(self, operation: str, package: str, profile: str, extra: list[str]) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+", package):
            raise PlayError("Invalid package name.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", profile):
            raise PlayError("Invalid built-in device profile.")
        session = str(Path(self._temporary.name) / f"session-{profile}.json")
        command = self._binary + [operation, package, "-account", "default", "-profile", profile, "-session", session] + extra
        try:
            result = subprocess.run(command, env=self._environment, capture_output=True, text=True, timeout=1800)
        except subprocess.TimeoutExpired:
            raise PlayError(f"Google Play {operation} timed out.") from None
        except OSError:
            raise PlayError("playfetch could not be started; install the pinned backend.") from None
        if result.returncode:
            # Upstream errors may contain account identifiers, credentials,
            # cookies or download URLs. Never forward them to public CI logs.
            reason = safe_failure_reason(result.stderr)
            raise PlayError(f"Google Play {operation} failed (exit {result.returncode}): {reason}.")
        return result.stdout

    def info(self, package: str, profile: str) -> dict:
        output = self._run("info", package, profile, ["-json"])
        try:
            result = json.loads(output)
        except json.JSONDecodeError:
            raise PlayError("Google Play metadata response was not valid JSON.") from None
        if not isinstance(result, dict) or not isinstance(result.get("app"), dict):
            raise PlayError("Google Play metadata response has an unsupported schema.")
        return result

    def pull(self, package: str, profile: str, version_code: int, output_dir: Path) -> dict:
        if type(version_code) is not int or version_code <= 0:
            raise PlayError("A positive versionCode is required before download.")
        output_dir.mkdir(parents=True, exist_ok=True)
        self._run("pull", package, profile, ["-vc", str(version_code), "-mode", "split", "-out", str(output_dir.resolve())])
        try:
            result = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise PlayError("Downloaded APK manifest is missing or invalid.") from None
        if not isinstance(result, dict):
            raise PlayError("Downloaded APK manifest has an unsupported schema.")
        return result
