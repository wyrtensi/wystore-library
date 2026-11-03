# Wy Store update feed

Wy Store can check every application with one public JSON request:

```text
https://raw.githubusercontent.com/wyrtensi/wystore-library/main/library/index.json
```

This is the canonical update feed, not a copy assembled by a client from GitHub
release titles. It requires no Google login or GitHub token. GitHub Actions
updates it after downloading, verifying and publishing complete APK sets.
Metadata and screenshots remain separate so version checks do not fetch them.

## Canonical device variants

The root retains `schema: 1` and adds `variant_schema: 1`, `delivery_profiles`
and `applications`. New clients use `applications` to select from complete
independently verified delivery sets. A delivery profile is an APK sampling
configuration, independent of Android personal/work profiles such as Shelter.

The registry samples modern ARM64 SDK 35, older ARM64 SDK 29 and 32-bit ARM
SDK 26, each requested in English and Russian. These are not phone-model
restrictions or universal compatibility guarantees. The actual delivered
requirements determine which other devices a variant supports.

| Field | Meaning |
| --- | --- |
| `applications[].package` | Stable Android application ID |
| `default_variant` | Default variant for the older-client projection |
| `variants` | Complete verified sets, each with its own version, compatibility, signer identity and files |
| `variants[].compatibility` | Actual Android, ABI, locale, density, feature, graphics and split requirements |
| `variants[].files` | Complete coherent set; each member references an artifact hash and preserves its role and split identity |
| `artifacts` | Shared immutable APK records with SHA-256, size and direct URL |
| `publication` | Stable application release and content-addressed catalog/manifest descriptors |
| `unavailable` | Explicit sampling outcomes; missing samples are not fabricated |

Never mix files from different variants, even when they share a version code.
Artifacts may be shared only when their full hashes match. Details and
publication guarantees are specified in the
[device variants contract](device-variants-contract.md).

## Legacy schema-1 projection

The `entries` array remains for older consumers. One entry identifies a package
and its default delivery profile. For migrated applications it is derived from
the canonical default variant, not maintained independently. The historical
`px_9a` identifier means the default modern ARM64 English sample; it is retained
to avoid breaking existing clients. It does not provide the library's full
device coverage. `migration_pending` identifies any remaining legacy packages.

| Field | Meaning |
| --- | --- |
| `package` | Android application ID; the app identity |
| `profile` | Hardware delivery profile used by Google Play |
| `version_code` | Positive integer Android version code; compare as a 64-bit integer |
| `version_name` | Display version, or null; never use it for update ordering |
| `assets` | Complete verified APK set, including base and required splits |
| `certificate_sha256` | Recorded signing certificate fingerprints for continuity |
| `certificate_scope` | Optional `{mode: "android-sdk", sdk: N}` describing the recorded signer identity |
| `manifest_url` | Public verification manifest for this exact version |
| `manifest_size`, `manifest_sha256` | Manifest byte size and SHA-256 |
| `metadata_url` | Description, icon, screenshots and changelog; fetch only when needed |

Each asset contains `name`, `role` (`base` or `split`), `split`, `size` in bytes,
lowercase hex `sha256`, and its direct HTTPS download `url`. Use every required
asset in the entry as one package-installation session. APKs are original and
retain their signatures; they are not merged or re-signed by this library.

Absence of `certificate_scope` means all cryptographically verified signer
identities are recorded. Its presence identifies the Android SDK used for
effective signing identity and continuity. Listing certificate metadata is not
a publication prerequisite. See the [verification contract](profile-certificate-verification.md).

Consumers should reject unsupported schema versions and duplicate
`(package, profile)` entries. Unknown additional fields may be ignored.

## Checking for updates

1. Fetch this JSON once for the whole library, using normal HTTP caching where
   available. Preserve the last valid feed if a network or parsing error occurs;
   report the error rather than treating it as an empty library.
2. Find the canonical application and filter complete variants using the
   device's SDK, supported ABIs, languages, density, required features, graphics
   capabilities and split constraints. Choose the newest compatible native
   version, then rank suitable language and density samples. A profile's name
   alone does not prove compatibility. If none fits, report incompatibility.
3. Compare `version_code` with Android's installed `longVersionCode`. Equal or
   older entries require no APK download. A release title or `version_name`
   change does not constitute an update.
4. Only for a newer code, download the selected variant's complete set and verify
   each byte size and SHA-256 before installation. Let Android verify the APK
   signatures and installed signing lineage during package installation.
5. If an asset returns 404 or 410 during replacement, refresh the feed once and retry
   only if the publication changed. Otherwise surface the failure; do not loop or
   silently accept an incomplete set.

## Publication and retention

The feed changes through an atomic GitHub commit after all referenced release
assets are uploaded and verified. It never advertises a draft or partially
uploaded set. Failed synchronization keeps the previous valid feed available.

One stable `<package>-library` release is retained per configured application,
containing all its current variants and their shared immutable APK files.
Cleanup validates the committed application's retained assets, then removes
unreferenced managed assets and obsolete managed releases. The feed is the authority even when Play
withdraws a rollout; a client already on a higher version still does not
downgrade because version comparison skips equal and older codes.

README version links are rendered from this same feed after successful APK
sync or metadata collection. Wy Store 0.6.0 and newer consume this feed through
the dedicated library source, independently of the ordinary GitHub source.
The Android client is published by the main Wy Store repository, not this library.


## Application categories and editorial shelves

A `library/catalog.json` card may contain `categories`, a list of stable category
identifiers such as `browsers`, `health`, `maps` or `ai`. These describe the app
and are localized by the Android client for both search rows and app details.
The optional `foreign_category` flag controls only membership in the library
shelf; it must never replace the app category. The shelf is named `Wy Store`
in every client language except Russian, where it is `Зарубежные`.
Older cards without `categories` remain valid and display no invented category.
