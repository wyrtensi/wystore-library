"""Readable release metadata built only from public, verified app information."""
import re


def text(value):
    if not isinstance(value, str):
        return ''
    return ' '.join(re.sub(r'[\x00-\x1f\x7f]', ' ', value).split())


def markdown(value):
    return re.sub(r'([\\`|*_\[\]<>])', r'\\\1', text(value))


def code(value):
    fence = '`' * (max((len(run) for run in re.findall(r'`+', value)), default=0) + 1)
    padding = ' ' if value.startswith(('`', ' ')) or value.endswith(('`', ' ')) else ''
    return fence + padding + value.replace('|', r'\|') + padding + fence


def release_presentation(app, profile, device, verified):
    package = app['package']
    name = text(app.get('title')) or package
    version = text(app.get('version_name')) or str(app['version_code'])
    model = text(device.get('model')) or profile
    title = f'{name} {version} ({model})'
    lines = [
        f'Original publisher-signed APKs for **{markdown(name)}** from Google Play.',
        '',
        f'- Version: **{markdown(version)}** (`versionCode {app["version_code"]}`).',
        f'- Package: `{package}`.',
        f'- Device profile: **{markdown(model)}** (`{profile}`).',
    ]
    if device.get('release'):
        lines.append(f'- Android: **{markdown(device["release"])}** (SDK {device["sdk"]}).')
    if device.get('abis'):
        lines.append('- Architecture: ' + ', '.join(code(abi) for abi in device['abis']) + '.')
    if device.get('density'):
        lines.append(f'- Density: **{device["density"]} dpi**.')
    lines += [
        '',
        f'[Description, screenshots and release notes on Google Play](https://play.google.com/store/apps/details?id={package})',
        '',
        'Install `base.apk` together with all split APKs in this release using a split-APK installer. '
        'These files are device-specific; they are not merged or re-signed.',
        '',
        '### Verified files',
        '',
        '| File | Size | SHA-256 |',
        '| --- | ---: | --- |',
    ]
    for asset in verified['files']:
        lines.append(f'| {code(asset["name"])} | {asset["size"]:,} bytes | `{asset["sha256"]}` |')
    lines += ['', '### Signing certificate SHA-256', '']
    lines += [f'- `{certificate}`' for certificate in verified['certificate_sha256']]
    lines += ['', 'Only the current verified version is retained for this app and device profile.']
    return title, '\n'.join(lines) + '\n'
