# Profile certificate verification implementation plan

> **For agentic workers:** Use native execution for the integration and live checks. A bounded implementer handles the independent APK inspector change.

**Goal:** Publish the configured APK library using the operator-approved Google Play delivery and signer-continuity policy.

**Architecture:** Verify Google delivery hashes and full APK cryptographic signatures, then record SDK-applicable signer identities for update continuity. Listing certificate metadata does not gate publication. Optional scope metadata preserves existing immutable manifests when no other signer identity is excluded.

**Tech stack:** Python standard library, Android apksigner/aapt2, pinned playfetch, GitHub Actions.

**Spec:** `docs/profile-certificate-verification.md`.

## Global constraints

- No Wy Store Android client changes, credential disclosure or repackaging.
- Version checks precede downloads; all existing hash, split and continuity checks remain.
- Existing release assets remain immutable; missing scope means all verified signers are recorded.

## Tasks

- [x] Add `inspect_apk_details(path, sdk=None)` with a structured inspection result;
  retain `inspect_apk(path)` as a thin five-tuple compatibility wrapper. Extend
  `verify_manifest(manifest, directory, package, version, previous, sdk=None)` to validate delivery SDK and return optional
  `certificate_scope`. First run failing tests for SDK selection, wrong key,
  malformed ranges, missing coverage, all-signer default and split continuity.
- [x] Remove the listing certificate prerequisite; wire authenticated device SDK into synchronization before downloads,
  propagate optional scope into the index and release notes, and document
  the guarantee. First run failing integration/presentation tests. Unscoped
  manifests and notes must retain their existing representation.
- [x] Run the full suite, workflow lint, metadata and privacy audits, then verify
  live Google Earth with its recorded profile signer and a deliberately wrong previous key.
  Obtain one independent whole-branch review and resolve material findings.
- [ ] Verify Git/GitHub identity, commit and push, run full publication for all
  55 apps, audit all release assets/manifests/index entries, and run again to
  confirm equal versions cause no APK download or upload.

## Review focus

Malformed annotations cannot hide an extra signer. Both digests belong to one
signer identity. Every split must match the recorded effective signing identity. Missing
SDK and delivery SDK conflicts cannot select a certificate implicitly. Scope
is explicit only when another identity is excluded; legacy assets stay reusable.
