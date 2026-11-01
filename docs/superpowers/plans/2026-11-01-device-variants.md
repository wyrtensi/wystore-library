# Device variant implementation plan

**Goal:** Deliver compatible default phone variants through one release per app
and one update feed, without retransferring unchanged variants.

**Spec:** `docs/device-variants-contract.md`.

- [x] Implement validated profile registry, isolated backend overrides and
  verified compatibility collection; prove min-SDK, ABI and split checks.
- [x] Implement stable app release publication, immutable hashed asset reuse,
  all-keeper preflight and current-only cleanup, with failure tests.
- [x] Implement app-level synchronization, per-profile version/configuration
  no-op, coherent-set deduplication and a derived schema-1 projection.
- [ ] Probe representative profiles and install appropriate complete sets on
  disposable emulators before enabling full migration.
- [ ] Review, run full tests and workflow checks, publish a small pilot, then
  migrate the complete library, audit feed/retention/README and rerun no-op.

All code and public documentation are English. No Google credentials or raw
delivery diagnostics may be published. Stop chat work at the operator's 60%
five-hour usage threshold if work has not finished; do not claim deployment
complete while migration or verification remains outstanding.

## Verification evidence

The local suite completed with 155 tests, OK. Actionlint reported no errors.
Kindle installed and launched on API 35 (ARM64) and API 30 (ARMv7) using the
emulator native bridge. API 26 was unavailable. Planfix installed on API 35,
but its React Native loader searched for x86_64 libraries under translation
and failed to launch; behavior on actual ARM hardware remains unverified.

The live two-application migration pilot succeeded: Planfix has two variants
and four unique APKs; Kindle has six variants and three unique APKs. A remote
audit verified both releases, four manifest assets, all eight variants, the
59 preserved default entries and 57 explicitly pending migrations. No old
managed release remains for either migrated application. Full migration and
a production no-download rerun remain required.
