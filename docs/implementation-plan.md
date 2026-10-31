# Wy Store Library implementation plan

**Goal:** Publish the requested GitHub-side library without changing Wy Store.
**Architecture:** independent metadata refresh and authenticated APK sync;
Python orchestration and pinned Go playfetch backend.
**Specification:** `docs/design.md`.

## Tasks

- [x] Metadata: write failure tests for normalization, image-host validation,
  changelog retention and missing metadata; implement
  `wystore_library.metadata.refresh_catalog(catalog_path, output_root)`;
  execute tests and a live fetch for all four apps.
- [x] APK sync: write failure tests proving version checks precede downloads,
  reject corrupt/wrong-package/mismatched-signer artifacts and partial
  publication; implement config validation, signature/hash verification,
  GitHub release publication and an index whose entries reference complete
  releases only. Backend interface is `PlayClient.info(package, profile)` and
  `PlayClient.pull(package, profile, version_code, output_dir)`.
- [x] Integration: implement protected credentials bootstrap and PlayClient,
  trusted-branch-only workflows, schedule, documentation and dependency pins.
  Verify secrets are absent from staged files and public outputs.
- [x] Run full unit suite, live metadata refresh, authentication check and
  trusted GitHub Actions runs. Obtain independent final branch review and
  resolve material findings before pushing the finished implementation.
- [x] Schedule both workflows once daily and keep version checks before downloads.
- [x] Add readable per-app releases and verified manifest hashes to the index.
- [x] Add fail-closed cleanup of strictly older managed releases after index commit,
  with keeper preflight and retry without duplicate APK transfers.
- [x] Verify full publication for all four apps and an equal-version live rerun;
  update the public availability status only after successful runs.

## Review focus

Unknown version must never trigger a speculative APK download. Corrupt or
mixed split sets must never enter the public index. Equal versions must not
be downloaded again. Secret-bearing backend diagnostics must never reach
public logs or assets. A failed APK fetch must leave metadata and previously
published releases available. Changelog snapshots must not pretend to be a
historical archive supplied by Play.

## Decisions and evidence

- Git identity and authenticated GitHub account both verified as wyrtensi.
- New repository is isolated from the existing Android project.
- Initial authentication was refused by Google. After the operator completed
  Google Play sign-in, a fresh one-time token exchange succeeded. Credentials
  remain in GitHub Secrets with a local Windows DPAPI backup; no account values
  are included in public artifacts.
- Initial metadata dependency omitted release notes and disabled TLS checks;
  replaced it with a bounded standard-library reader with verified TLS.
- Public index uses atomic GitHub Contents API updates, not mutable release
  asset replacement. Existing index remains available on a failed write.
- Independent final review found one P2: metadata publication was skipped when
  one app failed after other cards had refreshed. The commit step now runs for
  a completed refresh even on failure, retaining the failed job status. Failed
  preliminary tests still prevent refresh/publication.
- Live publication run `41178911537` completed for all four apps. Equal-version
  run `41179129710` skipped all four packages; the index SHA, release IDs and
  every asset ID, size and digest remained unchanged.
- Metadata refresh run `41179193482` and the backend/Python verification passed.
- Public manifests, releases, index and rerun logs were checked for private
  account values. All four public manifests match their indexed digests and
  contain only the intended public fields.
