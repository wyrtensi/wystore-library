# Why the library preserves split APKs

`base.apk` is not necessarily a standalone application. Google Play can deliver
native libraries, screen-density resources, translations and feature modules
as additional APKs for the selected device. Changing device settings does not
reconstruct missing native code or resources inside the base file.

Keep the complete delivered set for installation. Some features can be fetched
on demand by the application, but that does not make required configuration
splits optional or guarantee that a sideloaded app will download them itself.

## Observed packages

The initial 55-app index contained four standalone sets (Kindle, Prime Video,
international McDonald's and Starbucks US) and 51 sets with splits. This is an
observation for the Pixel 9a delivery profile, not a universal promise for other
devices or future versions.

Two published base APKs were downloaded, checked against their indexed SHA-256
and inspected with Android `aapt2 dump xmltree`:

| Package | Version code | Base manifest evidence |
| --- | --- | --- |
| `com.google.android.apps.bard` | 345 | `requiredSplitTypes="base__abi,base__density"`; `com.android.vending.splits.required=true` |
| `com.kwai.video` | 646902 | `requiredSplitTypes="base__abi,base__density"`; `com.android.vending.splits.required=true` |

Neither package was installed or launched during this inspection. Absence of
one particular manifest flag in another APK would not prove it works alone.
The feed's `assets` array remains the authoritative complete delivered set.

A publisher-supplied universal APK is a different artifact. Creating one from
splits generally requires rebuilding and signing; the library preserves original
packages and does not merge or re-sign them.

## Primary references

The four additions published on 2026-11-01 also arrived as sets for this profile:

| Application | Delivered APK files | Additional delivered parts |
| --- | ---: | --- |
| TikTok 47.6.3 | 9 | ABI, language, density and feature modules |
| Instagram 453.0.0.57.79 | 2 | Density configuration |
| Facebook 585.0.0.47.54 | 2 | Density configuration |
| WhatsApp 2.26.42.74 | 4 | ABI, density and English resources |

These counts describe the verified delivery, not a claim that every optional
module is essential at launch. Base-only installation of these four packages
was not tested; removing delivered parts is not enabled.

- [Android App Bundle format](https://developer.android.com/guide/app-bundle/app-bundle-format): base, configuration and feature APKs.
- [About App Bundles](https://developer.android.com/guide/app-bundle): incomplete sideloaded split installations.
- [bundletool](https://developer.android.com/tools/bundletool): device-specific APK sets and the distinct universal mode.
