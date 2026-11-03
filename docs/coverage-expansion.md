# Device coverage expansion

The six existing sampling profiles and fingerprints remain unchanged. Twelve
additional samples cover Android 9, 12, 13 and 16 on ARM64, Android 12 on ARMv7,
and Android 13 on x86-64, with English and Russian resources for each.

The Android 12/13 samples bridge the large gap between SDK 29 and 35. Android 9
samples ask for builds supporting Wy Store's oldest OS. The newer 32-bit sample
can discover a newer compatible branch than the SDK 26 sample. x86-64 is requested
explicitly; an ARM build is never advertised as native x86 support.

Profiles do not guarantee availability: Google Play may no longer offer an older
build or may not publish the requested architecture. Keep APK signature, split,
minimum Android, feature and graphics checks. Do not rewrite existing verified
compatibility facts to make unsupported devices appear compatible.

The daily sync populates new samples after deployment; changing the profile
registry alone does not make a build available. All variants remain assets of the
same stable application release, deduplicated by SHA-256. Check versions before
downloading and retain only the current complete set for each sample.


## Rollout cost

With 63 configured applications, a full check grows from 378 to 1,134 profile
metadata requests. Download and verification work grows only for new or changed
compatible sets. Before enabling a full initial population, use the workflow's
`packages` input for a small batch and inspect its duration and availability
results. The sync now divides the configured applications into at most eight
independent sequential jobs, each with a 180-minute limit. All library writers
share one workflow lock. Each job reads the current remote index; per-application
checkpoints preserve completed work if a later application fails. A rerun checks
versions first and skips already published verified sets. A check-only preflight
confirms Play responses but does not prove downloaded splits are compatible.

The separate [coverage validator](coverage-validation.md) re-downloads every
available set without publishing. Run it when a full audit is needed; normal
publication already verifies every new APK set and does not need a duplicate
download first.
