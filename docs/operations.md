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

Each `apps.json` entry may set `"foreign_category": false` to exclude it from
Wy Store's Foreign category. The default is `true`. This editorial flag changes
only category membership: the app remains in search, details and APK updates.
Only boolean values are accepted. A failed metadata refresh keeps cached artwork
while applying the current editorial flag. Discovery cards publish the resolved
`foreign_category` and compact `locales` title/summary fields for local search;
existing top-level discovery fields remain available to older consumers.

Both translations use the **US Google Play market** (`gl=us`), with `hl=ru`
or `hl=en` selecting the language independently. The existing `ru_RU` and
`en_US` keys identify translations, not service-availability countries.
The catalog and each successfully refreshed app record expose `market: us`.
A Russian-language card therefore does not imply availability in Russia;
similarly, a US listing does not establish service availability elsewhere.
There is no silent market fallback when a listing cannot be fetched.

## Public data

- [Application catalog](../library/catalog.json): card metadata and artwork paths.
- [APK index](../library/index.json): current verified variants and the schema-1 default projection.
- [APK releases](https://github.com/wyrtensi/wystore-library/releases).

Wy Store's single-request update endpoint and field contract are documented in
the [client feed guide](client-feed.md). Clients compare numeric version codes
from `library/index.json`; release titles are presentation only.

The APK index references complete verified releases and their public manifests.
Authenticated version checks and APK publication are separate stages. A populated
metadata card does not imply that an APK has been downloaded or published.

The variant pipeline samples six profiles: ARM64 SDK 35 at 420 dpi, ARM64
SDK 29 at 420 dpi, and ARMv7 SDK 26 at 320 dpi, each requested in English and
Russian. Pixel 9a (`px_9a`) remains the default English SDK 35 profile. These
samples do not guarantee universal device coverage or the availability of any
particular translated resources. Both older samples use the conservative `op_3`
hardware-feature cohort, which does not represent every device of the same SDK
and ABI. The base APK and all delivered required splits
must be installed together; publisher APKs are never merged or re-signed.
Regional service availability remains separate from APK delivery availability.
See the [device variants contract](device-variants-contract.md).

## Workflows

- **Refresh Play metadata**: daily at 02:43 UTC and manually; no Google credentials.
- **Sync Google Play APKs**: daily at 03:17 UTC and manually. Its manual `check_only`
  option reads native versions without downloading APKs. Its optional `packages`
  input limits a manual run to comma-separated configured package names.
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

The synchronization reads native `versionCode` first. For already migrated,
unchanged profiles, equal or older versions do not trigger APK downloads;
unknown or paid responses are rejected. Initial migration and changed sampling
profiles require independent delivery verification even at the same version.
If Play currently offers an older default during initial migration, the library
requests the exact already-published default version and verifies it without
lowering the published version. An unavailable pinned delivery fails visibly
and preserves the previous publication. Display versions from web metadata
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

Each migrated application uses one stable `<package>-library` release. Verified
APK bytes are immutable assets named by their SHA-256 hash; identical artifacts
can be shared between independently verified variants. Catalog and compatibility
manifests are also content-addressed. Assets are uploaded and checked before the
complete feed is switched atomically after each fully verified application.
Each checkpoint preserves all other applications, including pending legacy
entries. A later failure retains earlier checkpoints; retries resume from them.
Subsequent writes reread and compare the index and use GitHub's blob SHA to
reject concurrent changes. The root feed remains schema 1 and projects each
migrated application's default variant into `entries` for existing clients;
untouched legacy entries remain available during migration. See the
[device variants contract](device-variants-contract.md) for the canonical feed
and migration details.

## Current-version retention

After each successful application checkpoint, all retained assets of that
application must pass preflight before its unreferenced managed assets and
obsolete managed releases are removed. Other applications are untouched. At
startup, cleanup of already-committed applications is retried once. Cleanup failures remain visible and retryable; unrelated manual releases
are preserved. A stale client encountering a removed asset refreshes the feed once
and retries only if the publication changed. `check_only` does not publish or
clean up. The workflow concurrency group serializes library writes.

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
[`patches/playfetch-certificate-sets.patch`](../patches/playfetch-certificate-sets.patch)
and [`patches/playfetch-pinned-version.patch`](../patches/playfetch-pinned-version.patch).
The latter keeps manifest version metadata tied to the delivery request while
APK verification independently checks the actual package version. The certificate
patch includes regression tests and adds SHA-256 signing-certificate hashes
from Google's `AppDetails.certificateSet` field alongside the legacy certificate
list. Package, delivery-hash, APK-signature, split and signer-continuity checks
remain mandatory. Both verification and synchronization apply the same patch
and run the backend tests before building.

For local backend builds, apply both patches to the pinned source before running
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
