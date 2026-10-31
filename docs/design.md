# Wy Store Library

The operator requested a new public `wyrtensi/wystore-library` repository.
The existing Wy Store Android project must remain unchanged.

The library follows an explicit allowlist in `apps.json`: Planfix, Vivaldi,
Brave, and Firefox, initially using the pinned Pixel 9a profile. Other profiles
may be added explicitly; a downloaded set is never described as universal.

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
