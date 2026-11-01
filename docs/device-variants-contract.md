# Device variants implementation contract

The operator approved implementation on 2026-11-01. One stable release tagged
`<package>-library` holds immutable content-addressed APKs and publication
manifests. Changing one variant must not download unchanged variants again.

## Profiles and verification

Six initial sampling profiles represent ARM64 API 35, ARM64 API 29 and ARMv7
API 26, each requested in English and Russian. The existing `px_9a` identifier
remains the default English API 35 profile. A registry records the built-in
device, SDK, ABI list, density and locale for each identifier. Sampling profiles
do not prove majority market coverage. Both older classes use the `op_3`
built-in device as a conservative hardware-feature cohort, with the listed SDK,
ABI, density and locale overrides. Availability in that cohort does not establish
availability across all devices with the same SDK and ABI.

Each complete delivered set is independently checked for Google delivery
hashes, signatures, package/version, split identities and signer continuity.
Compatibility includes the actual minimum SDK, native ABIs, resource locales,
required device features and required/provided split types. A request locale
alone does not prove that translated resources exist. Incompatible variants
are explicit outcomes; network, authentication and verification errors fail.

Deduplication is only by full SHA-256 after verification. Artifacts are named
`<sha256>.apk`; members retain their original name, role and split identity.
Variants never mix files from different independently verified sets.

## One canonical feed with a compatibility projection

Keep root `schema: 1` and the existing `entries` projection for old consumers.
Add `variant_schema: 1`, `delivery_profiles` and canonical `applications`.
For migrated applications, default entries are derived from applications,
never maintained independently. During migration, untouched legacy entries
remain usable; `migration_pending` explicitly lists those packages.

An application contains `package`, `name`, `default_variant`, `variants`,
`artifacts`, `unavailable` and `publication`. Variants contain `id`,
`profile_fingerprint`, `version_code`, `version_name`, `certificate_sha256`,
optional `certificate_scope`, `compatibility`, and `files`. Each file contains
`artifact` (SHA-256), `original_name`, `role`, and `split`. Each artifact contains
`name`, `sha256`, `size`, and `url`.

Publication contains `tag`, `release_url`, `catalog` and `compat_manifest`.
Each manifest descriptor contains `name`, `sha256`, `size`, and `url`.
The catalog is serialized without its own publication descriptor to avoid a
circular digest. The compatibility manifest uses the established manifest
shape for the default variant, with content-addressed asset filenames.

## Publication transaction

Publish missing immutable assets first; check their uploaded sizes and GitHub
digests before switching the feed. Existing assets with a matching digest and
size are reused without download or upload. A digest absence or mismatch fails.
Never overwrite an existing named asset. Add `catalog-<sha256>.json` and
`manifest-<sha256>.json` as immutable manifest assets.

Commit the complete feed after each fully prepared application, preserving
all pending legacy entries. A failure in a later application must not discard
earlier checkpoints. Before each subsequent commit, reread the feed, require
it to match the previous checkpoint and use its blob SHA for compare-and-swap.
Retry outstanding cleanup against the committed feed before new Play queries.

After each atomic feed commit, preflight every retained application and its full
referenced asset set. Only then update release presentation and remove
unreferenced managed assets and obsolete managed legacy releases. Manual and
unconfigured releases remain untouched. Partial failure preserves current
referenced assets; cleanup failures remain visible and retryable.

The current feed always points to complete assets. Clients holding a stale
feed can encounter removed previous assets: refresh the feed once on 404 and
retry only when the publication changed. Do not silently loop. No previous
version retention is added against the operator's current-only requirement.

## Deployment

Probe a small representative set before migration, including a standalone
application, native/configuration splits and Copilot. Verify installations
on disposable emulators with actual matching ABI support. Report unavailable
old Android or ARM translation environments precisely. Preserve Google login
data and never use the real phone for these tests.

Initial migration re-downloads and verifies Google delivery rather than
inventing delivery hashes from old public file hashes. Thereafter unchanged
variants reuse their previously committed verified artifact records, checked
against actual release digests. Version and profile configuration checks occur
before every download. Keep a legacy default if a migration cannot preserve
its published version; never silently downgrade it.

When initial migration encounters a lower version in Play details, request the
exact published legacy default version. The backend manifest must describe
the delivery version rather than unrelated current details. All independent
APK and delivery checks remain mandatory, including previous signer continuity.
Use the previous default's version name for that pinned version. If redelivery
fails, leave its legacy entry and release intact and report the failure.
