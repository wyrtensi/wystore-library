# Wy Store Library

The operator requested a new public `wyrtensi/wystore-library` repository.
The original library-only phase kept the Wy Store Android project unchanged.
Client integration is a separate change in the main application repository.

The library follows an explicit allowlist in `apps.json`. It began with Planfix,
Vivaldi, Brave and Firefox, and now includes additional configured applications.
Its current delivery samples cover modern ARM64, older ARM64 and older 32-bit
ARM, each in English and Russian. A downloaded set is never described as
universal. The [device variants contract](device-variants-contract.md) supersedes
the initial single-profile design.

Two independent scheduled jobs maintain the library:

1. Public Google Play metadata: Russian and English description, title,
   developer, icon, screenshots and the current "What's new" text. Downloaded
   images and JSON live under `library/`; changelog snapshots accumulate from
   the first successful fetch. Metadata version strings are not trusted for
   APK update decisions.
2. APK synchronization: a pinned playfetch CLI uses the operator's own AAS
   token, supplied by GitHub Secrets and selected explicitly. No public
   dispenser or user credentials. Fetch native version metadata before any
   APK download, skip equal/older versions, refuse paid/unknown versions,
   preserve original publisher signatures and split sets, verify manifests,
   hashes, package/version and signatures before publishing versioned release
   assets. Update the public index only after complete release publication.

Original APKs are never committed to Git. Secret-bearing backend output and
raw manifests are never published; exported records contain no account
identity, token, cookies or Google CDN capability URLs. Missing AAS tokens
fail the APK job explicitly and leave existing releases untouched. Metadata
updates remain independently available.

Account bootstrap is a manual workflow, not a password login on every cron.
Google may require interactive sign-in or owner confirmation; this must be
reported honestly and never bypassed. The operator is responsible for each
publisher's distribution terms. The library tooling has its own license;
upstream tool licenses and app licenses remain separate.

Authentication/backend alternatives considered: embedding Android GPlayAPI
would require an Android/JVM wrapper; a permanently hosted dispenser adds
infrastructure. A bounded CLI job with operator credentials fits the chosen
scheduled mirror design. A public metadata-only catalogue is useful on its
own, but cannot provide versionCode or installable artifacts.

## Daily releases and retention

The operator chose one current stable release per application, containing all
of its currently verified variants. Metadata refresh and authenticated APK
checks run once daily. Releases use readable app names, installation guidance
and verified checksums; clients use the canonical index for variant selection
and numeric version comparisons. Unchanged variants do not trigger downloads
or uploads unless their sampling configuration changed.

After each complete application publication and index checkpoint, verify that
application's retained assets and manifests before cleanup. Remove its
unreferenced managed assets and obsolete managed releases and tags. The next
run retries interrupted cleanup without repeating unchanged publication. Manual
and unconfigured releases stay intact. Keep the shared write concurrency group
and index SHA guard. The initial recovery pass checks all committed applications.

Alternatives considered: one combined daily release would mix app lifecycles;
retaining all historical APKs would use storage contrary to the operator's choice.
Changelog history remains in metadata independently of APK retention.
