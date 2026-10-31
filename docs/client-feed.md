# Wy Store update feed

Wy Store can check every application with one public JSON request:

```text
https://raw.githubusercontent.com/wyrtensi/wystore-library/main/library/index.json
```

This is the canonical update feed, not a copy assembled by a client from GitHub
release titles. It requires no Google login or GitHub token. GitHub Actions
updates it after downloading, verifying and publishing complete APK sets.
Metadata and screenshots remain separate so version checks do not fetch them.

## Format, schema 1

The root contains `schema: 1` and an `entries` array. One entry identifies a
package and a hardware delivery profile. The current library uses `px_9a`:
Android SDK 35, arm64-v8a, 420 dpi, en_US. A delivery profile is independent of
Android personal/work profiles such as Shelter.

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
2. Select the entry for the package and a compatible delivery profile. The
   Pixel 9a profile is not a universal build for every Android device.
3. Compare `version_code` with Android's installed `longVersionCode`. Equal or
   older entries require no APK download. A release title or `version_name`
   change does not constitute an update.
4. Only for a newer code, download the entry's complete asset set and verify
   each byte size and SHA-256 before installation. Let Android verify the APK
   signatures and installed signing lineage during package installation.
5. If an asset returns 404 during replacement, refresh the feed once and retry
   only if the entry changed. Otherwise surface the failure; do not loop or
   silently accept an incomplete set.

## Publication and retention

The feed changes through an atomic GitHub commit after all referenced release
assets are uploaded and verified. It never advertises a draft or partially
uploaded set. Failed synchronization keeps the previous valid feed available.

Only the release named by the current entry is retained for each configured
package and delivery profile. Cleanup first validates every retained release,
then removes other managed versions. The feed is the authority even when Play
withdraws a rollout; a client already on a higher version still does not
downgrade because version comparison skips equal and older codes.

README version links are rendered from this same feed after successful APK
sync or metadata collection. The Android Wy Store client has not yet been
connected to this library.
