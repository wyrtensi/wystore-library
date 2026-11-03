# Play device coverage validation

Run **Validate Play device coverage** manually from GitHub Actions. The workflow uses the configured Google credentials and the same pinned, patched Play backend and APK verification tools as synchronization. It requires only read access to repository contents and never publishes or changes the library index.

Eight deterministic package batches run one at a time. Every configured app is checked against every registered device profile, and every available APK set is downloaded and independently verified, including unchanged published variants. The existing certificate for the same published profile is checked when available; a new profile has no previous profile-specific certificate. Each job has a six-hour limit. The complete run can take many hours and downloads substantial data. The workflow shares a concurrency group with synchronization; do not run other Play operations against the same account concurrently.

Each batch uploads only a sanitized JSON report, retained for 14 days. APKs and backend sessions are temporary and are not uploaded. A report records the package, profile fingerprint, version and status for each completed check; `verified` means signature, hashes, split completeness and compatibility were checked, `play_unavailable` means Play returned version zero, and `incompatible` identifies an authenticated delivery that does not fit the profile; it is not a complete compatibility pass. Authentication, rate limits, timeouts, malformed data and verification failures stop the run with an unsuccessful status and a partial report. A cancelled or timed-out job might not upload its report. Missing reports or `complete: false` mean that coverage is incomplete; unavailable versions are not verification failures.

The workflow reads the current published index after acquiring the shared lock,
so a dispatch queued behind a sync checks against the certificates that sync
actually published. A local run uses its explicitly selected index snapshot;
refresh the checkout first or supply `--index` with a current index file.

For a local batch, configure the same private environment variables used by the normal sync, install the pinned backend and Android build tools, then run:

```sh
python -m wystore_library.coverage_validation --batch-index 0 --batch-count 8 --report coverage-report.json
```

Batch indices run from zero through seven. Reports contain no credentials, raw backend diagnostics, download URLs, APKs, or account identifiers. They describe the current Play response and do not assert that previously published variants were removed.
