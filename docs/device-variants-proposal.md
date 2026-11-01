# Device variants: proposed library contract

Status: design proposal, not implemented. The current published feed remains
schema 1 and the current delivery profile remains Pixel 9a.

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
Replace the previous application release only after the new complete catalog
and its files are verified and the update feed is switched.

The proposed schema 2 feed keeps one endpoint and groups records by package:

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

## Evidence required before implementation

Probe representative applications under all candidate classes: a standalone
APK, an ABI-split app, an app with required configuration splits, and Copilot's
feature/asset splits. Record actual SDK/ABI requirements, delivery differences,
shared file hashes and availability failures. Install complete selected sets
on matching disposable emulators. Choose the final defaults from those results.

Schema migration must preserve the existing schema 1 consumer contract until
Wy Store supports variant selection. Adding multiple profiles to the present
publisher without changing retention would create multiple releases per app,
so that is not the implementation plan.
