# Wy Store Library

Scheduled Google Play application metadata and verified original APK sets.
This repository is independent of the Wy Store Android application.

## Applications

| Application | Play package | Saved metadata and artwork |
| --- | --- | --- |
| Planfix | `com.planfixng` | [Metadata](library/apps/com.planfixng/metadata.json) / [Images](library/apps/com.planfixng/images) |
| Vivaldi | `com.vivaldi.browser` | [Metadata](library/apps/com.vivaldi.browser/metadata.json) / [Images](library/apps/com.vivaldi.browser/images) |
| Brave | `com.brave.browser` | [Metadata](library/apps/com.brave.browser/metadata.json) / [Images](library/apps/com.brave.browser/images) |
| Firefox | `org.mozilla.firefox` | [Metadata](library/apps/org.mozilla.firefox/metadata.json) / [Images](library/apps/org.mozilla.firefox/images) |

Descriptions, short descriptions, publisher names, icons, up to eight screenshots
per locale, and the current Google Play release notes are stored in Russian and
English. Missing upstream values remain null. Release-note history accumulates
from the first successful fetch; it is not a complete historical Play archive.
Artwork and metadata remain attributed to the respective app publishers.

## Public data

- [Application catalog](library/catalog.json): card metadata and artwork paths.
- [APK index](library/index.json): latest complete verified set per package/profile.
- [Versioned APK releases](https://github.com/wyrtensi/wystore-library/releases).

The APK index starts empty until Google account verification and the first
authenticated synchronization succeed. A populated metadata card does not imply
that an APK has been downloaded or published.

The initial device profile is Pixel 9a: Android SDK 35, arm64-v8a, 420 dpi.
These are device-specific APK sets, not universal APKs. Other profiles can be
added explicitly in [apps.json](apps.json). Split APKs must be installed together.
Publisher APKs are never merged, modified or re-signed.

## Workflows

- **Refresh Play metadata**: every six hours and manually; no Google credentials.
- **Sync Google Play APKs**: every six hours and manually. Its manual `check_only`
  option reads native versions without downloading APKs.
- **Verify library tooling**: Python tests and the pinned upstream backend build.
  Pull-request checks never receive Google account secrets.

If one metadata fetch fails, successful updates for the other apps are still
committed, the old failed card is retained, and the workflow remains failed so
the operator sees the problem. Failed preliminary tests prevent publication.

GitHub schedules can run late or be dropped under load, and schedules in public
repositories can be disabled after 60 days without repository activity. These
jobs are periodic checks, not an availability or update-time guarantee.

## Authentication

Only the operator's dedicated Google account is used. Library users do not sign
in to Google. No public Aurora or third-party account dispenser is used.

The APK workflow requires repository secrets `GOOGLE_EMAIL` and
`GOOGLE_AAS_TOKEN`. A missing token fails explicitly before backend invocation.
Direct password login may be refused even when the password is correct; Google
can require interactive phone/device verification.

For one-time local setup:

```sh
python -m venv .venv
python -m pip install -r requirements.txt
python -m wystore_library.bootstrap --repository wyrtensi/wystore-library
```

The helper accepts `GOOGLE_EMAIL`, `GOOGLE_PASSWORD`, `GOOGLE_ANDROID_ID` and,
when needed, a one-time `GOOGLE_OAUTH_TOKEN` through the environment. Without
environment credentials it prompts locally, hiding password entry. It stores
the resulting AAS token through `gh secret set`, never in Git or console output.
See the [gpsoauth sign-in flow](https://github.com/simon-weber/gpsoauth#alternative-flow)
for obtaining a one-time token after Google verification. Do not paste tokens
into issues, workflow inputs, logs, release assets or commits.

Password/bootstrap secrets are never supplied to scheduled jobs. The APK job
uses a private temporary credentials file, explicitly selects the stored account,
captures backend output, and removes temporary credentials and session caches
on exit. Only trusted main-branch code receives the token. A workflow with access
to secrets can use them; GitHub Secrets is not protection against malicious
workflow code or a compromised dependency.

## Verification and publication

The synchronization reads native `versionCode` first. Equal, older, unknown and
paid versions do not trigger APK downloads. Display versions from web metadata
are never used for this decision.

Before publishing, every base/split APK is checked against Google delivery hashes,
its package/version and its cryptographic signature using Android `aapt` and
`apksigner`. Signers must match Google metadata, all splits must agree, and later
updates must retain the previously recorded signer. Signing-key rotation requires
manual review. Unsupported expansion files are rejected rather than silently
omitted. Account information and temporary Google CDN URLs are excluded from
public manifests.

Complete versioned APK sets are published as GitHub release assets. A failed draft
can resume only when its existing files match the verified expected set. Published
files are never overwritten. The index is updated afterwards through GitHub's
Contents API with the previous SHA, so failed or conflicting writes retain the
old index. A later package failure may leave a complete release not yet referenced
by the index; the next run can recover it.

## Development

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m wystore_library.metadata --config apps.json --output library
```

APK synchronization additionally requires `gh`, Android build-tools (`aapt` and
`apksigner`) and the pinned [playfetch](https://github.com/Exmeaning/playfetch)
commit `8bf14e52133d9609ad91ff830252414716d79017` in PATH. GitHub Actions builds
that commit from source. It is used as an external GPL-3.0-or-later tool; it is
not bundled into the Wy Store Android app.

The operator must have permission to redistribute each APK and comply with
publisher licenses and Google Play terms. A free download does not itself grant
redistribution permission. Access may change with account region, device profile,
publisher policy or Google's unofficial protocol.

The MIT license covers this repository's tooling only. Third-party applications,
artwork and external tools retain their own licenses and terms.
