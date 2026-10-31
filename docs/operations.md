# Library operations

Scheduled Google Play metadata collection and an APK verification/publication pipeline.
This repository is independent of the Wy Store Android application.

## Applications

See the [complete configured application list](applications.md) for package names and official Play listings. The [catalog](../library/catalog.json) shows collected metadata; configuration alone does not imply successful collection or APK publication.

Descriptions, short descriptions, publisher names, icons, up to eight screenshots
per locale, and the current Google Play release notes are stored in Russian and
English. Missing upstream values remain null. Release-note history accumulates
from the first successful fetch; it is not a complete historical Play archive.
Artwork and metadata remain attributed to the respective app publishers.

Both translations use the **US Google Play market** (`gl=us`), with `hl=ru`
or `hl=en` selecting the language independently. The existing `ru_RU` and
`en_US` keys identify translations, not service-availability countries.
The catalog and each successfully refreshed app record expose `market: us`.
A Russian-language card therefore does not imply availability in Russia;
similarly, a US listing does not establish service availability elsewhere.
There is no silent market fallback when a listing cannot be fetched.

## Public data

- [Application catalog](../library/catalog.json): card metadata and artwork paths.
- [APK index](../library/index.json): latest complete verified set per package/profile.
- [Versioned APK releases](https://github.com/wyrtensi/wystore-library/releases).

Wy Store's single-request update endpoint and field contract are documented in
the [client feed guide](client-feed.md). Clients compare numeric version codes
from `library/index.json`; release titles are presentation only.

The APK index references complete verified releases and their public manifests.
Authenticated version checks and APK publication are separate stages. A populated
metadata card does not imply that an APK has been downloaded or published.

The initial device profile is Pixel 9a: Android SDK 35, arm64-v8a, 420 dpi.
This profile is useful for matching devices, but its SDK version is not an app minimum: apps may support older Android versions. ARMv7 and x86 devices, older Android versions, other screen densities and languages may need different APKs. Other profiles can be added explicitly in [apps.json](../apps.json). The base APK and required configuration splits must be installed together. Publisher APKs are never merged, modified or re-signed. See Android documentation on [app bundles and configuration APKs](https://developer.android.com/guide/app-bundle) and [minimum SDK versions](https://developer.android.com/guide/topics/manifest/uses-sdk-element). Regional service availability is separate from APK download availability.

## Workflows

- **Refresh Play metadata**: daily at 02:43 UTC and manually; no Google credentials.
- **Sync Google Play APKs**: daily at 03:17 UTC and manually. Its manual `check_only`
  option reads native versions without downloading APKs.
- **Verify library tooling**: Python tests and the pinned upstream backend build.
  Pull-request checks never receive Google account secrets.
- **Refresh README catalog**: after successful trusted main-branch APK sync or
  metadata refresh, and manually. It renders current version links from the
  same APK index, updates only the marked catalog block, and preserves the rest
  of the remotely read README with a compare-and-swap SHA. No Google secrets
  are passed to this workflow.

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

Run the following commands from the repository root. For one-time local setup:

```sh
python -m venv .venv
python -m pip install -r requirements.txt
python -m wystore_library.bootstrap --repository wyrtensi/wystore-library
```

The helper accepts `GOOGLE_EMAIL`, `GOOGLE_PASSWORD`, `GOOGLE_ANDROID_ID` and,
when needed, a one-time `GOOGLE_OAUTH_TOKEN` through the environment. Without
environment credentials it prompts locally, hiding password entry. It stores
the resulting AAS token through `gh secret set`, never in Git or console output.
When Google returns the account's primary email, the helper stores that address
with the token instead of the sign-in alias. It does not print either value.
See the [gpsoauth sign-in flow](https://github.com/simon-weber/gpsoauth#alternative-flow)
for obtaining a one-time token after Google verification. Do not paste tokens
into issues, workflow inputs, logs, release assets or commits.

After restoring account access and replacing the token, run an authenticated
version check before attempting publication:

```sh
gh workflow run sync.yml --ref main -f check_only=true
```

Only after that run succeeds, start the full synchronization:

```sh
gh workflow run sync.yml --ref main -f check_only=false
```

`BadAuthentication` means Google rejected the saved credentials before the
catalog request. Re-running the job does not renew that token. The account
owner must complete Google's verification and repeat local bootstrap; there
is no automatic fallback to another account or a public token dispenser.

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
its package/version and its cryptographic signature using Android `aapt2` and
`apksigner`. The library trusts authenticated Google Play delivery and does not
compare APK certificates with the listing's certificate metadata. All splits
must agree, and later updates must retain the previously recorded signer.
For APKs with different keys for different Android SDK ranges, the recorded
signing identity uses the authenticated device SDK, which must agree with the
downloaded manifest. The base APK is verified first; its declared minimum SDK
then supplies the verification context for splits that can omit `uses-sdk`.
The upper SDK bound remains unrestricted, so verification covers the
application's supported Android range rather than just the device profile.
The optional `certificate_scope: {"mode": "android-sdk", "sdk": N}` field in
the manifest and index, and the release notes, identify the Android SDK used
for signer continuity. An absent field means the recorded fingerprints cover
all cryptographically verified signers. Existing immutable manifests retain
their recorded signer identities. Changes to the
previously recorded effective signer require manual review. See the
[certificate verification contract](profile-certificate-verification.md).
Unsupported expansion files are rejected rather than silently
omitted. Account information and temporary Google CDN URLs are excluded from
public manifests.

Complete versioned APK sets are published as GitHub release assets. A failed draft
can resume only when its existing files match the verified expected set. Published
files are never overwritten. The index is updated afterwards through GitHub's
Contents API with the previous SHA, so failed or conflicting writes retain the
old index. A later package failure may leave a complete release not yet referenced
by the index; the next run can recover it.

## Current-version retention

One versioned release is kept for each configured app and device profile. Titles
contain the app name, display version and device model; release notes include
the Google Play source, installation instructions, APK hashes and signer hashes.
The index also records `manifest_size` and `manifest_sha256` so the complete
current release can be checked before cleanup.

Cleanup starts after synchronization and any atomic index write succeed. Every
retained release must match the index by tag, uploaded asset names, sizes,
SHA-256 digests and URLs before any deletion occurs. Every other numeric version
tag belonging to configured package/profile pairs is removed with its assets,
including unindexed releases left by interrupted runs. The successfully
published index is authoritative even if Play withdraws a newer rollout.
Unrelated and manual tags are preserved. Missing verification data stops cleanup
without deleting anything.

Cleanup errors fail the job. A subsequent run with equal versions skips APK
downloads and uploads, then retries cleanup. `check_only` does not publish or
delete releases. The shared workflow concurrency group serializes all library
writes; expected index SHAs prevent stale writes from overwriting a newer index.
Release-note history remains available in application metadata.

## Development

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m wystore_library.metadata --config apps.json --output library
```

APK synchronization additionally requires `gh`, Android build-tools (`aapt2` and
`apksigner`) and the pinned [playfetch](https://github.com/Exmeaning/playfetch)
commit `8bf14e52133d9609ad91ff830252414716d79017` in PATH. GitHub Actions builds
that commit from source with
[`patches/playfetch-certificate-sets.patch`](../patches/playfetch-certificate-sets.patch).
The patch includes regression tests and adds SHA-256 signing-certificate hashes
from Google's `AppDetails.certificateSet` field alongside the legacy certificate
list. Package, delivery-hash, APK-signature, split and signer-continuity checks
remain mandatory. Both verification and synchronization apply the same patch
and run the backend tests before building.

For local backend builds, apply that patch to the pinned source before running
`go test ./...` and `go build ./cmd/playfetch`.
The backend and its compatibility patch are GPL-3.0-or-later, with license text in
[`patches/LICENSE`](../patches/LICENSE). The backend is not bundled into the
Wy Store Android app.

The operator must have permission to redistribute each APK and comply with
publisher licenses and Google Play terms. A free download does not itself grant
redistribution permission. Access may change with account region, device profile,
publisher policy or Google's unofficial protocol.

The MIT license covers the Python orchestration. The backend patch, third-party
applications, artwork and external tools retain their own licenses and terms.
