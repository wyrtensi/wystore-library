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
- [x] Verify Git/GitHub identity, commit and push, run full publication for all
  55 apps, audit all release assets/manifests/index entries, and run again to
  confirm equal versions cause no APK download or upload.
- [x] Reproduce Copilot resource split rejection and verify splits using the
  already authenticated base APK's minimum SDK. Keep the upper SDK bound
  unrestricted and reject invalid signatures, different signers and base SDKs
  exceeding the selected profile.

## Review focus

Malformed annotations cannot hide an extra signer. Both digests belong to one
signer identity. Every split must match the recorded effective signing identity. Missing
SDK and delivery SDK conflicts cannot select a certificate implicitly. Scope
is explicit only when another identity is excluded; legacy assets stay reusable.

## Verified publication

- The Python suite contains 107 passing tests; workflow lint and public-data
  privacy checks pass. Live Google Earth and Copilot APK sets pass complete
  package, delivery-hash, signature and signer-continuity checks.
- Run `41198277231` published the complete 55-app index. Run `41199752331`
  skipped all 55 versions without APK transfers and completed current-only
  cleanup, leaving exactly 55 releases and 55 managed tags.
- Run `41200023750` detected a genuine Meta AI version advance. Its previous
  release was removed, while the other 54 releases retained their IDs, asset
  IDs, sizes and digests. The final audit verified 55 current sets and 186 APKs.
- README workflow runs `41199848135` and `41200136268` completed successfully;
  the latter updated the table from the changed index. The public feed and
  README agree. No Android Wy Store client changes were made.
