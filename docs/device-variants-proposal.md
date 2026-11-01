# Device variants: design history

This document records the original proposal. The approved implementation and
migration contract is [device-variants-contract.md](device-variants-contract.md).
The published feed remains schema 1, with a default Pixel 9a projection for
existing clients and canonical variants added during migration.

## Coverage target

Start by measuring three candidate device classes: modern ARM64 (SDK 35),
older ARM64 (SDK 29), and 32-bit ARM (SDK 26). These are sampling profiles,
not claims of compatibility with every device or guaranteed majority coverage.
Google Play may not offer an older compatible version for every application.
Density and Russian/English resources require separate selection; do not
multiply every combination into a full copy of the application.

## One application, one current release

Each application release contains verified installation variants and shared
files. Deduplicate only byte-identical artifacts by SHA-256. Different base
APKs and versions stay separate. A release represents a publication of the
variant catalog, rather than pretending all variants share one version code.
Keep one stable `<package>-library` release and publish immutable SHA-256-addressed
assets before switching the feed to the new complete catalog.

The approved feed keeps root schema 1, adds `variant_schema: 1`, and groups canonical records by package:

- `package`: stable application identity.
- `variants`: independently verified installation sets, each with its actual
  `version_code`, display version, minimum SDK, supported ABI, density and
  language resources, recorded signing identity and required split constraints.
- `artifacts`: original immutable files addressed by hashes, with sizes and
  direct download URLs. Variants reference these records to share identical files.
- `publication`: identity of the complete per-application release.

The client filters compatible variants before comparing versions, then selects
the newest compatible version and its required configuration files. It must
never combine base or feature splits from different versions or delivery sets.
Density scaling can be allowed where Android supports it; ABI incompatibility
cannot be repaired by scaling. The installer receives one complete coherent set.

## Deployment evidence

Probe representative applications under all candidate classes: a standalone
APK, an ABI-split app, an app with required configuration splits, and Copilot's
feature/asset splits. Record actual SDK/ABI requirements, delivery differences,
shared file hashes and availability failures. Install complete selected sets
on matching disposable emulators. Record any unavailable environment or variant without assuming broader coverage.

Schema migration must preserve the existing schema 1 consumer contract until
Wy Store supports variant selection. Adding multiple profiles to the present
publisher without changing retention would create multiple releases per app,
so that is not the implementation plan.
