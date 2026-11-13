<div align="center">

<img src="assets/library-banner.png" alt="Wy Store Library: Google Play to GitHub Actions to the library index and Wy Store, with device-specific APK sets" width="760">

**An application library for [Wy Store](https://github.com/wyrtensi/wystore).**

App descriptions, screenshots and release notes from Google Play.<br>
A companion catalog with verified original app packages.

**Available in [Wy Store 0.6.0 and newer](https://github.com/wyrtensi/wystore/releases/tag/v0.6.0).**
Install selected apps unavailable in the Russian Google Play catalog without
signing in to Google. The library is a built-in Wy Store source alongside
RuStore and GitHub; app service availability remains subject to publisher rules.

[![Checks](https://github.com/wyrtensi/wystore-library/actions/workflows/verify.yml/badge.svg)](https://github.com/wyrtensi/wystore-library/actions/workflows/verify.yml)
[![APKs](https://github.com/wyrtensi/wystore-library/actions/workflows/sync.yml/badge.svg)](https://github.com/wyrtensi/wystore-library/actions/workflows/sync.yml)
[![Metadata](https://github.com/wyrtensi/wystore-library/actions/workflows/metadata.yml/badge.svg)](https://github.com/wyrtensi/wystore-library/actions/workflows/metadata.yml)
[![License](https://img.shields.io/badge/orchestration-MIT-A85A38?style=flat-square)](LICENSE)

[**Wy Store**](https://github.com/wyrtensi/wystore) · [**Download Wy Store**](https://github.com/wyrtensi/wystore/releases/latest/download/wystore.apk) · [**Catalog**](library/catalog.json) · [**APK releases**](https://github.com/wyrtensi/wystore-library/releases)

</div>

## Explore the library

**Multiple device variants, one current release per application.**
Click a version to open that application's current APK set. App names lead to
saved descriptions, artwork and release notes.

The registry requests 18 delivery samples across these architectures, each in
English and Russian. The table below describes requested coverage; an app gains
a variant only after synchronization downloads and verifies its complete APK set:

| Device class | Sampling Android version | Architecture | Sampling density |
| --- | --- | --- | --- |
| ARM64 | Android 9, 10, 12, 13, 15, 16 (SDK 28/29/31/33/35/36) | `arm64-v8a` | 320 / 420 dpi |
| 32-bit ARM | Android 8, 12 (SDK 26/31) | `armeabi-v7a` | 320 dpi |
| x86-64 | Android 13 (SDK 33) | `x86_64` | 320 dpi |

These are delivery samples, not phone-model restrictions. A client selects a
complete compatible set using its verified Android, ABI, language, density,
feature and split requirements. Available variants differ by application;
the library does not cover every Android device. See the
[device variants contract](docs/device-variants-contract.md).

<!-- APP_CATALOG:START -->

**63 applications · 704 verified device variants · daily checks**

| Application | Collection | Current version | Device variants | Google Play |
| --- | --- | --- | --- | --- |
| <img src="library/apps/com.abc.abcnews/images/2ee0f1bdeb43abc5e673fe66e7edf180934baee86c115609d6f6320e7c91feb2.png" width="32" alt=""> [ABC News](library/apps/com.abc.abcnews/metadata.json) | News | [8.98.2](https://github.com/wyrtensi/wystore-library/releases/tag/com.abc.abcnews-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.abc.abcnews-library) | [Google Play](https://play.google.com/store/apps/details?id=com.abc.abcnews) |
| <img src="library/apps/com.runtastic.android/images/c1b4c68484b936dbdcb66ab3131f25beca97c24c43c3aef58de69967a9fd8a55.png" width="32" alt=""> [adidas Running](library/apps/com.runtastic.android/metadata.json) | Health &amp; fitness | [14.12.1](https://github.com/wyrtensi/wystore-library/releases/tag/com.runtastic.android-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.runtastic.android-library) | [Google Play](https://play.google.com/store/apps/details?id=com.runtastic.android) |
| <img src="library/apps/com.amazon.dee.app/images/9307d8251ba20b3c1afa61eb0b99f1fd5e5e4ab43ede49bd9a2788b4d6e715e9.png" width="32" alt=""> [Amazon Alexa](library/apps/com.amazon.dee.app/metadata.json) | Smart home | [2.2.730155.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.dee.app-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.dee.app-library) | [Google Play](https://play.google.com/store/apps/details?id=com.amazon.dee.app) |
| <img src="library/apps/com.amazon.storm.lightning.client.aosp/images/83845f516202a023c5c2cd8f899b9101badc764c9b2a2c148e909419ee008e43.png" width="32" alt=""> [Amazon Fire TV](library/apps/com.amazon.storm.lightning.client.aosp/metadata.json) | Entertainment | [4.9.1](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.storm.lightning.client.aosp-library) | [16 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.storm.lightning.client.aosp-library) | [Google Play](https://play.google.com/store/apps/details?id=com.amazon.storm.lightning.client.aosp) |
| <img src="library/apps/com.amazon.flex.rabbit/images/92e2add0e91b5db43e5f9280b6eed3518891de922bb880229b5750c55c0699ef.png" width="32" alt=""> [Amazon Flex](library/apps/com.amazon.flex.rabbit/metadata.json) | Work | [3.145.1.86.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.flex.rabbit-library) | [6 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.flex.rabbit-library) | [Google Play](https://play.google.com/store/apps/details?id=com.amazon.flex.rabbit) |
| <img src="library/apps/com.amazon.kindle/images/6882972f599423717ec82661775747586c780f7659c121602dc3c1b123230ac0.png" width="32" alt=""> [Amazon Kindle](library/apps/com.amazon.kindle/metadata.json) | Books | [8.159.0.100(2.0.115180.0)](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.kindle-library) | [16 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.kindle-library) | [Google Play](https://play.google.com/store/apps/details?id=com.amazon.kindle) |
| <img src="library/apps/com.amazon.mp3/images/a58043d5116ae2118b227eb51728eed5bf807c2bd4ffc82e0c28dbc3a81aca94.png" width="32" alt=""> [Amazon Music](library/apps/com.amazon.mp3/metadata.json) | Music | [26.40.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.mp3-library) | [18 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.mp3-library) | [Google Play](https://play.google.com/store/apps/details?id=com.amazon.mp3) |
| <img src="library/apps/com.amazon.avod.thirdpartyclient/images/a1342a92272a245310904d5c6c2fe8196b032f668f345ef0fdcebded979ef97e.png" width="32" alt=""> [Amazon Prime Video](library/apps/com.amazon.avod.thirdpartyclient/metadata.json) | Video | [3.0.480.847](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.avod.thirdpartyclient-library) | [14 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.avod.thirdpartyclient-library) | [Google Play](https://play.google.com/store/apps/details?id=com.amazon.avod.thirdpartyclient) |
| <img src="library/apps/com.amazon.mShop.android.shopping/images/83e2070daf3d74d2e801286961e2f621bf48ec512502baa9470a8108716fed65.png" width="32" alt=""> [Amazon Shopping](library/apps/com.amazon.mShop.android.shopping/metadata.json) | Shopping | [32.20.2.100](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.mShop.android.shopping-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.amazon.mShop.android.shopping-library) | [Google Play](https://play.google.com/store/apps/details?id=com.amazon.mShop.android.shopping) |
| <img src="library/apps/com.avast.android.mobilesecurity/images/6b6d09e26751ef51c1c0363ab96c94f4adafd33cb4cac75a9fe1e59af4656361.png" width="32" alt=""> [Avast One](library/apps/com.avast.android.mobilesecurity/metadata.json) | Security | [26.21.0.261104066](https://github.com/wyrtensi/wystore-library/releases/tag/com.avast.android.mobilesecurity-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.avast.android.mobilesecurity-library) | [Google Play](https://play.google.com/store/apps/details?id=com.avast.android.mobilesecurity) |
| <img src="library/apps/com.antivirus/images/b25c8b4127d74cb9e42c07e20c8d6277a315666f5351a304a8d298702ec5693f.png" width="32" alt=""> [AVG AntiVirus](library/apps/com.antivirus/metadata.json) | Security | [26.18.0.261002870](https://github.com/wyrtensi/wystore-library/releases/tag/com.antivirus-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.antivirus-library) | [Google Play](https://play.google.com/store/apps/details?id=com.antivirus) |
| <img src="library/apps/com.badoo.mobile/images/73f9fda2ef5ee8fbf53468910df5c61572789e4f15d0da14a6cad52059e2bea7.png" width="32" alt=""> [Badoo](library/apps/com.badoo.mobile/metadata.json) | Dating | [5.492.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.badoo.mobile-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.badoo.mobile-library) | [Google Play](https://play.google.com/store/apps/details?id=com.badoo.mobile) |
| <img src="library/apps/com.bilibili.app.in/images/604e84a2f691f1d909c84d9a732eeb480ceba945968f2d3ba7684365c8f2a7fc.png" width="32" alt=""> [Bilibili](library/apps/com.bilibili.app.in/metadata.json) | Video | [6.8.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.bilibili.app.in-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.bilibili.app.in-library) | [Google Play](https://play.google.com/store/apps/details?id=com.bilibili.app.in) |
| <img src="library/apps/com.brave.browser/images/5a5c283664afc841640a88263733c0fc525ac3810e2a7d4490bede874e5b02e8.png" width="32" alt=""> [Brave](library/apps/com.brave.browser/metadata.json) | Browsers | [1.99.56](https://github.com/wyrtensi/wystore-library/releases/tag/com.brave.browser-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.brave.browser-library) | [Google Play](https://play.google.com/store/apps/details?id=com.brave.browser) |
| <img src="library/apps/com.bumble.app/images/9fd17b015964d02c470f422e58a9dda7609331dd571b284906744fabc3f689d4.png" width="32" alt=""> [Bumble](library/apps/com.bumble.app/metadata.json) | Dating | [5.492.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.bumble.app-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.bumble.app-library) | [Google Play](https://play.google.com/store/apps/details?id=com.bumble.app) |
| <img src="library/apps/com.canva.editor/images/e39c9effe0dece99936bd241d1b9dcc0f092f248bcbee71d7eb0cce47ff5b695.png" width="32" alt=""> [Canva](library/apps/com.canva.editor/metadata.json) | Creativity | [2.386.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.canva.editor-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.canva.editor-library) | [Google Play](https://play.google.com/store/apps/details?id=com.canva.editor) |
| <img src="library/apps/com.squareup.cash/images/0476d81de14b01f5631859076959ef4a7e545e3181ab84415cb3558325a6e3eb.png" width="32" alt=""> [Cash App](library/apps/com.squareup.cash/metadata.json) | Finance | [5.77.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.squareup.cash-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.squareup.cash-library) | [Google Play](https://play.google.com/store/apps/details?id=com.squareup.cash) |
| <img src="library/apps/com.openai.chatgpt/images/4e2fd1df4ed6e215262bdfff54c272c83176ba8bf58e0392b2123d6acb762d14.png" width="32" alt=""> [ChatGPT](library/apps/com.openai.chatgpt/metadata.json) | AI assistants | [1.2026.307](https://github.com/wyrtensi/wystore-library/releases/tag/com.openai.chatgpt-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.openai.chatgpt-library) | [Google Play](https://play.google.com/store/apps/details?id=com.openai.chatgpt) |
| <img src="library/apps/com.anthropic.claude/images/f06c8dd977118107909fd81a376fed319f134df8674bfc329b9dd7a4d8b01098.png" width="32" alt=""> [Claude](library/apps/com.anthropic.claude/metadata.json) | AI assistants | [1.261111.19](https://github.com/wyrtensi/wystore-library/releases/tag/com.anthropic.claude-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.anthropic.claude-library) | [Google Play](https://play.google.com/store/apps/details?id=com.anthropic.claude) |
| <img src="library/apps/com.deepl.mobiletranslator/images/95f700c7309e9dc214673e0814db05f7c7fc14ecb76920fc3aae991f8950d793.png" width="32" alt=""> [DeepL Translate](library/apps/com.deepl.mobiletranslator/metadata.json) | Productivity | [26.45](https://github.com/wyrtensi/wystore-library/releases/tag/com.deepl.mobiletranslator-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.deepl.mobiletranslator-library) | [Google Play](https://play.google.com/store/apps/details?id=com.deepl.mobiletranslator) |
| <img src="library/apps/deezer.android.app/images/8b98d7f3ceacfaebd0085a05bd3c1f22ef8f44d55a7e1de01d68708288716900.png" width="32" alt=""> [Deezer](library/apps/deezer.android.app/metadata.json) | Music | [9.0.26.3](https://github.com/wyrtensi/wystore-library/releases/tag/deezer.android.app-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/deezer.android.app-library) | [Google Play](https://play.google.com/store/apps/details?id=deezer.android.app) |
| <img src="library/apps/com.disney.disneyplus/images/e4050d289d79d300debcf072a210482469404102a88243242766e87c9bdcde2a.png" width="32" alt=""> [Disney+](library/apps/com.disney.disneyplus/metadata.json) | Video | [26.20.0+rc3-2026.11.02](https://github.com/wyrtensi/wystore-library/releases/tag/com.disney.disneyplus-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.disney.disneyplus-library) | [Google Play](https://play.google.com/store/apps/details?id=com.disney.disneyplus) |
| <img src="library/apps/com.facebook.katana/images/732a151d7754325188bcd70b56475b6c88deccf2fd40c5d4982f00081539ad0c.png" width="32" alt=""> [Facebook](library/apps/com.facebook.katana/metadata.json) | Social | [587.0.0.39.55](https://github.com/wyrtensi/wystore-library/releases/tag/com.facebook.katana-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.facebook.katana-library) | [Google Play](https://play.google.com/store/apps/details?id=com.facebook.katana) |
| <img src="library/apps/com.funcamerastudio.videomaker/images/1be59de58dabfd51fbc74d1454a005f39e31f1d2a47a03df0c9b2ab3e6425331.jpg" width="32" alt=""> [Filmigo](library/apps/com.funcamerastudio.videomaker/metadata.json) | Creativity | [6.7.9.2](https://github.com/wyrtensi/wystore-library/releases/tag/com.funcamerastudio.videomaker-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.funcamerastudio.videomaker-library) | [Google Play](https://play.google.com/store/apps/details?id=com.funcamerastudio.videomaker) |
| <img src="library/apps/org.mozilla.firefox/images/f8a1c9c8fe396386fb02f632f929884ad2d3e47fc7b9a961d1e72ffce9528989.png" width="32" alt=""> [Firefox](library/apps/org.mozilla.firefox/metadata.json) | Browsers | [160.0](https://github.com/wyrtensi/wystore-library/releases/tag/org.mozilla.firefox-library) | [18 variants](https://github.com/wyrtensi/wystore-library/releases/tag/org.mozilla.firefox-library) | [Google Play](https://play.google.com/store/apps/details?id=org.mozilla.firefox) |
| <img src="library/apps/com.fitbit.FitbitMobile/images/21c56453b3a6b7f214186a7def365223623f92414a957b739ecdd6ba8c94330c.png" width="32" alt=""> [Fitbit](library/apps/com.fitbit.FitbitMobile/metadata.json) | Health &amp; fitness | [5.12.1.health-mobile-1104141583-1017635139](https://github.com/wyrtensi/wystore-library/releases/tag/com.fitbit.FitbitMobile-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.fitbit.FitbitMobile-library) | [Google Play](https://play.google.com/store/apps/details?id=com.fitbit.FitbitMobile) |
| <img src="library/apps/com.google.earth/images/ea19697e082f9531fff13756d4f5787afe7c0f5c8384a1efd51112eed6364973.png" width="32" alt=""> [Google Earth](library/apps/com.google.earth/metadata.json) | Maps | [10.125.82.01](https://github.com/wyrtensi/wystore-library/releases/tag/com.google.earth-library) | [18 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.google.earth-library) | [Google Play](https://play.google.com/store/apps/details?id=com.google.earth) |
| <img src="library/apps/com.google.android.apps.bard/images/a666127dfa4818971e09696bfca63227811465d7b9f5fb77c26c5774ea939876.png" width="32" alt=""> [Google Gemini](library/apps/com.google.android.apps.bard/metadata.json) | AI assistants | [1.0.995038376](https://github.com/wyrtensi/wystore-library/releases/tag/com.google.android.apps.bard-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.google.android.apps.bard-library) | [Google Play](https://play.google.com/store/apps/details?id=com.google.android.apps.bard) |
| <img src="library/apps/com.google.android.apps.chromecast.app/images/91461ebf3ce079e88764a70f8eda5f8c67745c95e28b6ae6fdcb323d18fbcb2e.png" width="32" alt=""> [Google Home](library/apps/com.google.android.apps.chromecast.app/metadata.json) | Smart home | [4.37.27.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.google.android.apps.chromecast.app-library) | [18 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.google.android.apps.chromecast.app-library) | [Google Play](https://play.google.com/store/apps/details?id=com.google.android.apps.chromecast.app) |
| <img src="library/apps/com.google.android.apps.walletnfcrel/images/118a5d4b6385d3900a34b40eb4c3aea7e40e503d829887c2d2100c15fe6ffb66.png" width="32" alt=""> [Google Wallet](library/apps/com.google.android.apps.walletnfcrel/metadata.json) | Finance | [26.45.1018379642](https://github.com/wyrtensi/wystore-library/releases/tag/com.google.android.apps.walletnfcrel-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.google.android.apps.walletnfcrel-library) | [Google Play](https://play.google.com/store/apps/details?id=com.google.android.apps.walletnfcrel) |
| <img src="library/apps/ai.x.grok/images/c53cae41965132aa41d2a43a4369b46c556af751389b21b8b45d01ad550f9198.png" width="32" alt=""> [Grok](library/apps/ai.x.grok/metadata.json) | AI assistants | [1.2.56-release.00](https://github.com/wyrtensi/wystore-library/releases/tag/ai.x.grok-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/ai.x.grok-library) | [Google Play](https://play.google.com/store/apps/details?id=ai.x.grok) |
| <img src="library/apps/com.wbd.stream/images/eccb94511a3b6682c8590572bc068bda2e230b6bda5372ce4e64f513c1a273e3.png" width="32" alt=""> [HBO Max](library/apps/com.wbd.stream/metadata.json) | Video | [22.0.0.321](https://github.com/wyrtensi/wystore-library/releases/tag/com.wbd.stream-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.wbd.stream-library) | [Google Play](https://play.google.com/store/apps/details?id=com.wbd.stream) |
| <img src="library/apps/com.instagram.android/images/9061a0ab3d22c72ff59756bb7b49da075692256ccb6fba5263b09c54b75b10f0.png" width="32" alt=""> [Instagram](library/apps/com.instagram.android/metadata.json) | Social | [455.0.0.51.72](https://github.com/wyrtensi/wystore-library/releases/tag/com.instagram.android-library) | [14 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.instagram.android-library) | [Google Play](https://play.google.com/store/apps/details?id=com.instagram.android) |
| <img src="library/apps/com.myklarnamobile/images/4ceaef5213bad0a883a72fbd9cd71a6742d2198b28a90396bce4242d3e109e9e.png" width="32" alt=""> [Klarna](library/apps/com.myklarnamobile/metadata.json) | Shopping | [26.46.334](https://github.com/wyrtensi/wystore-library/releases/tag/com.myklarnamobile-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.myklarnamobile-library) | [Google Play](https://play.google.com/store/apps/details?id=com.myklarnamobile) |
| <img src="library/apps/com.kwai.video/images/dfbe5bc1a404ab2e5ffdd2d0c57fc25f2278abe8fd79058cf298b4f67786b2f5.jpg" width="32" alt=""> [Kwai](library/apps/com.kwai.video/metadata.json) | Video | [13.10.10.647103](https://github.com/wyrtensi/wystore-library/releases/tag/com.kwai.video-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.kwai.video-library) | [Google Play](https://play.google.com/store/apps/details?id=com.kwai.video) |
| <img src="library/apps/jp.naver.line.android/images/d7e22f6d6996a0157e41e27123e146f4c32551cb8581a5a91a2818c6e8c14409.png" width="32" alt=""> [LINE](library/apps/jp.naver.line.android/metadata.json) | Messaging | [26.17.1](https://github.com/wyrtensi/wystore-library/releases/tag/jp.naver.line.android-library) | [16 variants](https://github.com/wyrtensi/wystore-library/releases/tag/jp.naver.line.android-library) | [Google Play](https://play.google.com/store/apps/details?id=jp.naver.line.android) |
| <img src="library/apps/com.linkedin.android/images/e19482101a384f7fba6539527831180181ff5b1c0905b490adaa74de5a51a80d.png" width="32" alt=""> [LinkedIn](library/apps/com.linkedin.android/metadata.json) | Social | [4.1.1270](https://github.com/wyrtensi/wystore-library/releases/tag/com.linkedin.android-library) | [14 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.linkedin.android-library) | [Google Play](https://play.google.com/store/apps/details?id=com.linkedin.android) |
| <img src="library/apps/com.mcdonalds.mobileapp/images/318232a446974da3f70fe1e91e626158c3ffbfa686461c86a57152d953f89124.png" width="32" alt=""> [McDonald&#x27;s](library/apps/com.mcdonalds.mobileapp/metadata.json) | Food &amp; drink | [3.53.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.mcdonalds.mobileapp-library) | [14 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.mcdonalds.mobileapp-library) | [Google Play](https://play.google.com/store/apps/details?id=com.mcdonalds.mobileapp) |
| <img src="library/apps/com.facebook.stella/images/7b4d803d79c67ac392b3ee2e97af47032b10b8afcf41883d0d7dfdab3a1a06dd.png" width="32" alt=""> [Meta AI](library/apps/com.facebook.stella/metadata.json) | AI assistants | [298.0.0.28.160](https://github.com/wyrtensi/wystore-library/releases/tag/com.facebook.stella-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.facebook.stella-library) | [Google Play](https://play.google.com/store/apps/details?id=com.facebook.stella) |
| <img src="library/apps/com.microsoft.office.officehubrow/images/40a798be0d88075c0bfb49e3576e74303d1e873ed214209a20a982eff98b6e77.png" width="32" alt=""> [Microsoft Copilot](library/apps/com.microsoft.office.officehubrow/metadata.json) | AI assistants | [16.0.20625.20022](https://github.com/wyrtensi/wystore-library/releases/tag/com.microsoft.office.officehubrow-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.microsoft.office.officehubrow-library) | [Google Play](https://play.google.com/store/apps/details?id=com.microsoft.office.officehubrow) |
| <img src="library/apps/com.gm.chevrolet.nomad.ownership/images/ec40a6725e404556e320110136fc7d6a042fc0f0eb73cff94b76a3b4c2c9163a.png" width="32" alt=""> [myChevrolet](library/apps/com.gm.chevrolet.nomad.ownership/metadata.json) | Auto &amp; vehicles | [8.21.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.gm.chevrolet.nomad.ownership-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.gm.chevrolet.nomad.ownership-library) | [Google Play](https://play.google.com/store/apps/details?id=com.gm.chevrolet.nomad.ownership) |
| <img src="library/apps/com.myfitnesspal.android/images/8ce1d74ede5fad08fdb38862cadde44a99967b3b2674fdae31c54df5c18b0738.jpg" width="32" alt=""> [MyFitnessPal](library/apps/com.myfitnesspal.android/metadata.json) | Health &amp; fitness | [26.45.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.myfitnesspal.android-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.myfitnesspal.android-library) | [Google Play](https://play.google.com/store/apps/details?id=com.myfitnesspal.android) |
| <img src="library/apps/com.netflix.mediaclient/images/e07a41e8afc91b3ff66ddd02e6b8378e786034721acfa948e43de85449c7971b.png" width="32" alt=""> [Netflix](library/apps/com.netflix.mediaclient/metadata.json) | Video | [9.92.0 build 9 74772](https://github.com/wyrtensi/wystore-library/releases/tag/com.netflix.mediaclient-library) | [16 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.netflix.mediaclient-library) | [Google Play](https://play.google.com/store/apps/details?id=com.netflix.mediaclient) |
| <img src="library/apps/com.particlenews.newsbreak/images/c2d40ad103aff2528d6d90eba568748070f721a5cb72e2599de3544954309c8c.png" width="32" alt=""> [NewsBreak](library/apps/com.particlenews.newsbreak/metadata.json) | News | [26.46.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.particlenews.newsbreak-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.particlenews.newsbreak-library) | [Google Play](https://play.google.com/store/apps/details?id=com.particlenews.newsbreak) |
| <img src="library/apps/com.symantec.mobilesecurity/images/b85f1f14f6324c3cb678f8526b582e38473be12c3d24d88979ac76c78f98b3f3.jpg" width="32" alt=""> [Norton 360](library/apps/com.symantec.mobilesecurity/metadata.json) | Security | [26.21.0.261103359](https://github.com/wyrtensi/wystore-library/releases/tag/com.symantec.mobilesecurity-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.symantec.mobilesecurity-library) | [Google Play](https://play.google.com/store/apps/details?id=com.symantec.mobilesecurity) |
| <img src="library/apps/ai.perplexity.app.android/images/5bda56d5f6d22466ccb1e0c5fad7fff02ac749d1971d7dc0a0e76b8f8f709789.png" width="32" alt=""> [Perplexity](library/apps/ai.perplexity.app.android/metadata.json) | AI assistants | [2.104.0](https://github.com/wyrtensi/wystore-library/releases/tag/ai.perplexity.app.android-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/ai.perplexity.app.android-library) | [Google Play](https://play.google.com/store/apps/details?id=ai.perplexity.app.android) |
| <img src="library/apps/com.planfixng/images/cb5fb1cd1554835a10e4c26e70c506dd85f6a9eaab9c295408238b1c0abed8dd.png" width="32" alt=""> [Planfix](library/apps/com.planfixng/metadata.json) | Productivity | [0.74.2](https://github.com/wyrtensi/wystore-library/releases/tag/com.planfixng-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.planfixng-library) | [Google Play](https://play.google.com/store/apps/details?id=com.planfixng) |
| <img src="library/apps/com.thomsonreuters.reuters/images/1151b3b8ec25c3e3ec32cd1da6e51560b3b5070171b0bf3098c9db85b3292d30.png" width="32" alt=""> [Reuters](library/apps/com.thomsonreuters.reuters/metadata.json) | News | [7.51.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.thomsonreuters.reuters-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.thomsonreuters.reuters-library) | [Google Play](https://play.google.com/store/apps/details?id=com.thomsonreuters.reuters) |
| <img src="library/apps/com.joytunes.simplyguitar/images/36f9e3fccf7ddcbdd9fd078a06d058cef6253aa7b4d6df05496200645682b982.png" width="32" alt=""> [Simply Guitar](library/apps/com.joytunes.simplyguitar/metadata.json) | Music education | [9.8.1](https://github.com/wyrtensi/wystore-library/releases/tag/com.joytunes.simplyguitar-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.joytunes.simplyguitar-library) | [Google Play](https://play.google.com/store/apps/details?id=com.joytunes.simplyguitar) |
| <img src="library/apps/com.joytunes.simplypiano/images/f2372ad98a0e53157a7114d34295ea7e7e4b16d50ec2de2a40737c48735baf2b.png" width="32" alt=""> [Simply Piano](library/apps/com.joytunes.simplypiano/metadata.json) | Music education | [7.33.11](https://github.com/wyrtensi/wystore-library/releases/tag/com.joytunes.simplypiano-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.joytunes.simplypiano-library) | [Google Play](https://play.google.com/store/apps/details?id=com.joytunes.simplypiano) |
| <img src="library/apps/jp.gocro.smartnews.android/images/41164742a6d2778144efe6012905074753f9727a3debceee3213b3c21b3f472c.png" width="32" alt=""> [SmartNews](library/apps/jp.gocro.smartnews.android/metadata.json) | News | [26.10.41](https://github.com/wyrtensi/wystore-library/releases/tag/jp.gocro.smartnews.android-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/jp.gocro.smartnews.android-library) | [Google Play](https://play.google.com/store/apps/details?id=jp.gocro.smartnews.android) |
| <img src="library/apps/com.spotify.music/images/07d50e3c8417774c57f097f1e5cf44c9c1d0b45b2b711122a18b266155d172ae.jpg" width="32" alt=""> [Spotify](library/apps/com.spotify.music/metadata.json) | Music | [9.2.0.2053](https://github.com/wyrtensi/wystore-library/releases/tag/com.spotify.music-library) | [18 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.spotify.music-library) | [Google Play](https://play.google.com/store/apps/details?id=com.spotify.music) |
| <img src="library/apps/com.starbucks.mobilecard/images/ca4d44f7868fd788da84199e6e0c57cc8ccd5fa10b16d696d575f41da4b83e4e.png" width="32" alt=""> [Starbucks (US)](library/apps/com.starbucks.mobilecard/metadata.json) | Food &amp; drink | [6.135](https://github.com/wyrtensi/wystore-library/releases/tag/com.starbucks.mobilecard-library) | [14 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.starbucks.mobilecard-library) | [Google Play](https://play.google.com/store/apps/details?id=com.starbucks.mobilecard) |
| <img src="library/apps/com.strava/images/5eca650ebfcece7b35f881f1fa5531a6ea274fbc6b84584c6b7560121b19198c.png" width="32" alt=""> [Strava](library/apps/com.strava/metadata.json) | Health &amp; fitness | [489.9](https://github.com/wyrtensi/wystore-library/releases/tag/com.strava-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.strava-library) | [Google Play](https://play.google.com/store/apps/details?id=com.strava) |
| <img src="library/apps/com.einnovation.temu/images/151c37762af271f7bab259c0ffbc3f88fa774fdac9ed687cd2d4f71f97fdbfe4.png" width="32" alt=""> [Temu](library/apps/com.einnovation.temu/metadata.json) | Shopping | [4.97.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.einnovation.temu-library) | [16 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.einnovation.temu-library) | [Google Play](https://play.google.com/store/apps/details?id=com.einnovation.temu) |
| <img src="library/apps/com.zhiliaoapp.musically/images/f1460d10ef1929d8494b8e049aa045ab8b913f193a39fcf6a25e1c5afdfb0d5d.png" width="32" alt=""> [TikTok](library/apps/com.zhiliaoapp.musically/metadata.json) | Social | [47.7.3](https://github.com/wyrtensi/wystore-library/releases/tag/com.zhiliaoapp.musically-library) | [16 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.zhiliaoapp.musically-library) | [Google Play](https://play.google.com/store/apps/details?id=com.zhiliaoapp.musically) |
| <img src="library/apps/com.tinder/images/a3b20e898bb52dfd761f9d0330e7bce28641834317cde4c83fd7cca5ece9694e.png" width="32" alt=""> [Tinder](library/apps/com.tinder/metadata.json) | Dating | [17.42.1](https://github.com/wyrtensi/wystore-library/releases/tag/com.tinder-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.tinder-library) | [Google Play](https://play.google.com/store/apps/details?id=com.tinder) |
| <img src="library/apps/com.vivaldi.browser/images/1d8bc7c7ed087bde30c84a41b84fafe81f0e8c9ada29922ad974f1656800f981.png" width="32" alt=""> [Vivaldi](library/apps/com.vivaldi.browser/metadata.json) | Browsers | [8.3.4192.71](https://github.com/wyrtensi/wystore-library/releases/tag/com.vivaldi.browser-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.vivaldi.browser-library) | [Google Play](https://play.google.com/store/apps/details?id=com.vivaldi.browser) |
| <img src="library/apps/com.walmart.android/images/71f13be4f74f59b77f3836746b0e3504e7d318d75b0758a5fb84b1b1ac2712da.png" width="32" alt=""> [Walmart](library/apps/com.walmart.android/metadata.json) | Shopping | [26.42.2](https://github.com/wyrtensi/wystore-library/releases/tag/com.walmart.android-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.walmart.android-library) | [Google Play](https://play.google.com/store/apps/details?id=com.walmart.android) |
| <img src="library/apps/com.weightwatchers.mobile/images/e59fbcb83b113f7526a21b2059aa263f466c0807cbb5b9cf7a1df030e66432c9.png" width="32" alt=""> [WeightWatchers](library/apps/com.weightwatchers.mobile/metadata.json) | Health &amp; fitness | [11.32.0](https://github.com/wyrtensi/wystore-library/releases/tag/com.weightwatchers.mobile-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.weightwatchers.mobile-library) | [Google Play](https://play.google.com/store/apps/details?id=com.weightwatchers.mobile) |
| <img src="library/apps/com.whatsapp/images/b29a53a5ca9e2e6516a21210d43e7489cba6dad0cfba2df98e976affafd2e391.png" width="32" alt=""> [WhatsApp](library/apps/com.whatsapp/metadata.json) | Messaging | [2.26.44.90](https://github.com/wyrtensi/wystore-library/releases/tag/com.whatsapp-library) | [10 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.whatsapp-library) | [Google Play](https://play.google.com/store/apps/details?id=com.whatsapp) |
| <img src="library/apps/com.contextlogic.wish/images/8a8aab0bcb435b72d75452af15748c0d4729a91b0ad010b3b659aaf04addd96e.png" width="32" alt=""> [Wish](library/apps/com.contextlogic.wish/metadata.json) | Shopping | [26.7.9](https://github.com/wyrtensi/wystore-library/releases/tag/com.contextlogic.wish-library) | [8 variants](https://github.com/wyrtensi/wystore-library/releases/tag/com.contextlogic.wish-library) | [Google Play](https://play.google.com/store/apps/details?id=com.contextlogic.wish) |
| <img src="library/apps/cn.xender/images/925b07ea6cbc8583fc6a008ef18580f25bc7521552bb65f9e1dea26df5d9babd.png" width="32" alt=""> [Xender](library/apps/cn.xender/metadata.json) | Tools | [19.0.0.prime](https://github.com/wyrtensi/wystore-library/releases/tag/cn.xender-library) | [18 variants](https://github.com/wyrtensi/wystore-library/releases/tag/cn.xender-library) | [Google Play](https://play.google.com/store/apps/details?id=cn.xender) |

<!-- APP_CATALOG:END -->

The table follows the [update feed](library/index.json) and refreshes automatically
after successful checks. Descriptions and available release notes are saved in
Russian and English; screenshot collections are stored alongside each app.

<details>
<summary><strong>Browse app screenshots</strong></summary>

<table>
<tr>
<td width="50%" align="center" valign="top"><strong>Planfix</strong><br><br>
<a href="library/apps/com.planfixng/images/65ff548ff13a5456c04b49d007c0ec83381961b3c0527305d35b23a2ad1e4ebb.png"><img src="library/apps/com.planfixng/images/65ff548ff13a5456c04b49d007c0ec83381961b3c0527305d35b23a2ad1e4ebb.png" alt="Planfix: screenshot 1" width="150"></a>
<a href="library/apps/com.planfixng/images/1c86159b24b25d3ecee31b5071c6a6e08b8dde23c3eb5ee83d1c506b5da03baf.png"><img src="library/apps/com.planfixng/images/1c86159b24b25d3ecee31b5071c6a6e08b8dde23c3eb5ee83d1c506b5da03baf.png" alt="Planfix: screenshot 2" width="150"></a>
</td>
<td width="50%" align="center" valign="top"><strong>Vivaldi</strong><br><br>
<a href="library/apps/com.vivaldi.browser/images/4c835cf1e3b7226ae0a204c6fedf7cfa618adcd658d21a7006bf7b59bb8585fc.png"><img src="library/apps/com.vivaldi.browser/images/4c835cf1e3b7226ae0a204c6fedf7cfa618adcd658d21a7006bf7b59bb8585fc.png" alt="Vivaldi: screenshot 1" width="150"></a>
<a href="library/apps/com.vivaldi.browser/images/e172bd20f21c9e2918f2c3a1368a7b97eae9348aa03c89dad45304deb421c26a.png"><img src="library/apps/com.vivaldi.browser/images/e172bd20f21c9e2918f2c3a1368a7b97eae9348aa03c89dad45304deb421c26a.png" alt="Vivaldi: screenshot 2" width="150"></a>
</td>
</tr>
<tr>
<td width="50%" align="center" valign="top"><strong>Brave</strong><br><br>
<a href="library/apps/com.brave.browser/images/298dcbe233f6045dd05ecdef1ada1a6d4557403520449826d9cbce0c1262313d.png"><img src="library/apps/com.brave.browser/images/298dcbe233f6045dd05ecdef1ada1a6d4557403520449826d9cbce0c1262313d.png" alt="Brave: screenshot 1" width="150"></a>
<a href="library/apps/com.brave.browser/images/67adb1f60186228ca5eaa3ead67eaba6a5874028a68f483a0dc540fa5f34d1d6.png"><img src="library/apps/com.brave.browser/images/67adb1f60186228ca5eaa3ead67eaba6a5874028a68f483a0dc540fa5f34d1d6.png" alt="Brave: screenshot 2" width="150"></a>
</td>
<td width="50%" align="center" valign="top"><strong>Firefox</strong><br><br>
<a href="library/apps/org.mozilla.firefox/images/9be8e6584968ab0d7de9a82fb08498e8a061e4f576da72702e783585524afa01.jpg"><img src="library/apps/org.mozilla.firefox/images/9be8e6584968ab0d7de9a82fb08498e8a061e4f576da72702e783585524afa01.jpg" alt="Firefox: screenshot 1" width="150"></a>
<a href="library/apps/org.mozilla.firefox/images/e603e5d1d51b89166ff3d79dadf8e96fd5b27b987a1534d63fa6f4e3bd84cc31.jpg"><img src="library/apps/org.mozilla.firefox/images/e603e5d1d51b89166ff3d79dadf8e96fd5b27b987a1534d63fa6f4e3bd84cc31.jpg" alt="Firefox: screenshot 2" width="150"></a>
</td>
</tr>
</table>

Screenshots and icons come from the app publishers on Google Play. Full image sets are saved alongside each app’s metadata.

</details>

## Where the apps come from

This library uses **Google Play** as its source. Scheduled GitHub Actions collect metadata and publish verified original app packages. Wy Store reads the catalog for discovery, checks the shared index for updates, and downloads complete compatible APK sets from the application's release.

```mermaid
flowchart TB
    Publisher["App publishers"] --> Play["Google Play"]
    Play -->|"Descriptions, artwork and release notes"| Metadata["Collect metadata"]
    Play -->|"New versions and original APKs"| Verify["Download and verify APK sets"]
    subgraph Library["Wy Store Library · GitHub"]
        Metadata --> Catalog["Catalog and artwork<br/>library/"]
        Verify --> Releases["Current verified APK sets<br/>GitHub Releases"]
        Releases --> Index["Versions and device variants<br/>library/index.json"]
    end
    Catalog -->|"Search and app details"| WyStore["Wy Store 0.6.0+<br/>Install and update apps"]
    Index -->|"Update checks and variant selection"| WyStore
    Releases -->|"Complete APK downloads"| WyStore
    RuStore["RuStore"] --> WyStore
    GitHub["App publishers on GitHub"] --> WyStore
    classDef source fill:#242b34,stroke:#66788f,color:#f0f3f7
    classDef ready fill:#23352e,stroke:#688e7a,color:#eef6f1
    classDef store fill:#433026,stroke:#d88e6c,color:#fff0e7
    class Play,RuStore,GitHub,Publisher source
    class Metadata,Catalog,Verify,Releases,Index ready
    class WyStore store
```

All arrows show implemented flows. The library is a dedicated Wy Store source;
ordinary GitHub repositories keep their existing release-based behavior.

### Using the library in Wy Store

- Enable the Wy Store source in app source settings, then use the **Wy Store** search filter or the **Wy Store** category (**Зарубежные** in Russian) directly after GitHub on Home.
- Where the same package exists in several sources, its app card offers source selection. Compatible signatures allow updates; an incompatible signature requires an explicitly confirmed reinstall that can remove local app data.
- Wy Store checks native version codes before downloading and selects a complete APK set for the device's Android version, architecture and other compatibility requirements. One index checks the whole library without parsing every release page.

### Current availability

| Component | Status |
| --- | --- |
| Metadata, artwork and release notes | Scheduled refresh once daily; see the [catalog](library/catalog.json) for collected apps |
| Verified APKs | Checked once daily; see the [APK index](library/index.json) for published sets |
| Library integration with Wy Store | Available since [0.6.0](https://github.com/wyrtensi/wystore/releases/tag/v0.6.0): discovery, source selection, compatible APK installation and updates |

The [app catalog](library/catalog.json) and [APK index](library/index.json) are separate. The APK index points to complete verified releases and their public manifests. Descriptions, screenshots and release notes can also be browsed independently.

## How updates are prepared

1. **Check the version first.** The pipeline reads `versionCode` before downloading. Equal and older versions are skipped.
2. **Verify the package set.** Every base and split APK is checked for hashes, package name, version and signing certificate. Signing-key changes require review.
3. **Publish complete variants.** Verified files go into the application's stable release before the index is updated. Published assets are never overwritten.

Each app has one stable `<package>-library` release containing its current
verified variants and shared APK files. Variants can have different version
codes. Unchanged variants reuse their verified files; changing the sampling
configuration requires fresh verification even when the version is unchanged.
After publishing complete sets and committing the index, cleanup removes
unreferenced assets and obsolete managed releases. If cleanup is interrupted,
the next run resumes it without downloading or uploading unchanged sets again.

Metadata refresh runs daily at **02:43 UTC** and APK checks at **03:17 UTC**
(07:43 and 08:17 in Yekaterinburg). GitHub schedules can be delayed; manual runs
remain available.

The pipeline preserves original publisher signatures and split packages without
merging or re-signing them. Install the base APK and every split listed in one
selected variant together; do not mix variants or assume the base APK works
alone. Sampling Android versions are not minimum-version promises: use the
verified requirements of the actual delivered set. x86 variants are not currently
sampled. Regional availability, login, licensing and Google Play services
requirements remain separate from APK delivery. See
[split APKs](docs/split-apks.md) and
[Android device compatibility](https://developer.android.com/guide/topics/manifest/uses-sdk-element).
See [client validation](docs/client-validation.md) for the separate installation
and service results recorded for ChatGPT, Grok and Planfix.

## For Wy Store and other clients

**One request checks the whole library:** [public update feed](https://raw.githubusercontent.com/wyrtensi/wystore-library/main/library/index.json).
It contains package IDs, numeric version codes, complete APK URLs, sizes and
SHA-256 hashes. GitHub Actions updates this same file after publication; clients
do not need to parse release pages or titles. See the [feed contract](docs/client-feed.md).

| Data | Location |
| --- | --- |
| App list and metadata paths | [`library/catalog.json`](library/catalog.json) |
| Descriptions, artwork and release-note history | `library/apps/<package>/metadata.json` |
| Latest complete APK sets | [`library/index.json`](library/index.json) |
| Verified files for each published version | [GitHub Releases](https://github.com/wyrtensi/wystore-library/releases) |
| Configured apps and device profiles | [`apps.json`](apps.json) |

Built as a companion source for Wy Store. Visit the main application: **[wyrtensi/wystore](https://github.com/wyrtensi/wystore)** · [project website](https://wystore.ru).

<details>
<summary><strong>Development and maintenance</strong></summary>

Setup, authentication, publication formats and schedule limitations are documented in the [operations guide](docs/operations.md).

The [banner source](assets/library-banner.html) keeps the delivery flow editable.
Its bundled Manrope font is covered by the [SIL Open Font License](assets/fonts/OFL.txt).

Library clients receive app data only. Source credentials stay in GitHub Secrets and are excluded from public metadata and manifests.

</details>

---

Python orchestration is licensed under [MIT](LICENSE); the backend compatibility patch is [GPL-3.0-or-later](patches/LICENSE). Apps, trademarks, descriptions and artwork retain their publishers’ rights and distribution terms. Wy Store Library is independent of Google and the listed app publishers.
