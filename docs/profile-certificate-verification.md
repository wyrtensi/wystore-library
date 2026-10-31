# APK verification and profile signer continuity

The library trusts authenticated Google Play delivery. Listing certificate
metadata is not used as a publication prerequisite. APKs can carry different
signing certificates for different Android SDK ranges; the selected device SDK
determines which identity is recorded for future update continuity.

## Contract

- Continue running full `apksigner verify --verbose --print-certs` without
  reducing its Android SDK verification range. Tool failure rejects the APK.
- Parse each APK signer certificate as one identity with paired SHA-256 and
  SHA-1 digests. Exclude Source Stamp and public-key fingerprints. Reject
  malformed or unsupported signer annotations, incomplete identities and
  invalid SDK ranges, even if another signer is readable.
- A positive integer SDK from authenticated `info.device.sdk` selects the
  applicable signer identities. The downloaded manifest must declare the same
  SDK. Missing or conflicting SDK data rejects the download before publication.
- Verify the downloaded bytes against Google delivery hashes and the local
  manifest, then check package name, version, split identities and signatures.
- Every split must have the same applicable signer set. An empty applicable
  set or changed previously recorded signer rejects the set. Signing-key changes
  still require manual review; a missing listing certificate is not a failure.
- Without an SDK, record all cryptographically verified signer identities.
- Add `certificate_scope: {"mode": "android-sdk", "sdk": N}` to the public
  manifest and index only when another verified signer identity was excluded
  by its SDK range. Release notes explain which SDK the recorded signing
  identity covers, while APK cryptographic verification remains complete.
- Absence of `certificate_scope` means the recorded fingerprints cover the full
  cryptographically verified signer set. Existing immutable releases retain that meaning and
  remain reusable without changing their files or forcing equal-version
  downloads. A matching signer used in multiple SDK ranges does not by itself
  narrow the recorded identity's scope.

Descriptions and screenshots remain separate. The Android Wy Store client is
unchanged. Version checks must continue to precede APK downloads.
