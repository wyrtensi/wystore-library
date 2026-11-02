# Client installation and service checks

These observations were recorded on 2026-11-02 using an unreleased Wy Store
client build. Both applications were downloaded and installed through the
library source, preserving the publisher's APK signatures and complete split
sets. Android recorded Wy Store as installer and update owner.

The disposable test environment was Android 15 with Google Play Store enabled,
an x86_64 emulator with ARM64 translation, and English resources. Emulator
results do not establish behaviour on every physical ARM device or in every
country.

| Application | Tested version | Installation | Service observation |
| --- | --- | --- | --- |
| ChatGPT | `1.2026.293` / `2629319` | Base APK and three configuration splits installed | Guest chat opened without sign-in and returned `OK` to one neutral test request |
| Grok | `1.2.53-release.00` / `11253200` | Base APK and three configuration splits installed | Launch was blocked by a **Get this app from Play** screen; having Play Store installed was insufficient in this environment |

No ChatGPT or Grok account was used for these checks. Account sign-in, paid
features, other service functions and physical devices remain unverified.
An earlier Grok launch on an Android 14 image without Play Store instead asked
for Google Play to be enabled or updated.

An installable, correctly signed APK is not a guarantee that its online service
accepts installation through another store. The Grok result records the observed
screen, not a proven explanation for its distribution, account or device checks.
The library does not bypass those checks or modify the publisher's application.
