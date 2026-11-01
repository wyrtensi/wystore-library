"""Collect compatibility facts from an independently verified APK set."""
import hashlib
import re
import subprocess
import zipfile
from pathlib import Path

from .profiles import validate_profile


class ProfileIncompatible(ValueError):
    def __init__(self, reason, minimum_sdk=None):
        if reason not in ('min_sdk', 'abi') or (minimum_sdk is not None and (type(minimum_sdk) is not int or minimum_sdk <= 0)):
            raise ValueError('Invalid incompatibility')
        self.reason = reason
        self.minimum_sdk = minimum_sdk
        super().__init__('Application minimum Android SDK exceeds device profile' if reason == 'min_sdk' else 'APK native ABI is incompatible with device profile')


def _tool(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
    except OSError as error:
        raise ValueError('APK metadata tool could not be started') from error
    if result.returncode:
        raise ValueError('APK metadata inspection failed')
    return result.stdout


def _xml_attributes(xml, name):
    matches = []
    for line in xml.splitlines():
        if re.search(r'\b' + re.escape(name) + r'(?:\(0x[0-9a-fA-F]+\))?=', line):
            match = re.search(r'\b' + re.escape(name) + r'(?:\(0x[0-9a-fA-F]+\))?="([^"]*)"', line)
            if not match:
                raise ValueError('Malformed APK split metadata')
            matches.append(match.group(1))
    return matches


def _types(values):
    result = set()
    for value in values:
        if not value:
            continue
        parts = value.split(',')
        if any(not re.fullmatch(r'[A-Za-z0-9_.-]+', part) for part in parts):
            raise ValueError('Malformed APK split type')
        result.update(parts)
    return result


def collect_compatibility(directory: Path, publicverifiedmanifest: dict, requestprofile: dict, device: dict) -> dict:
    validate_profile(requestprofile)
    if not isinstance(device, dict) or any(device.get(k) != requestprofile[k] or type(device.get(k)) is not type(requestprofile[k]) for k in ('sdk', 'abis', 'density', 'locale')):
        raise ValueError('Delivered device does not match requested profile')
    if not isinstance(publicverifiedmanifest, dict) or not isinstance(publicverifiedmanifest.get('files'), list) or not publicverifiedmanifest['files']:
        raise ValueError('Invalid verified APK manifest')
    root = Path(directory).resolve()
    files = publicverifiedmanifest['files']
    if any(not isinstance(f, dict) for f in files) or sum(f.get('role') == 'base' for f in files) != 1:
        raise ValueError('Invalid verified APK set')
    names, splits, native, languages, features, required, provided, used = set(), set(), set(), set(), set(), set(), set(), set()
    minimum, gl = None, None
    for record in files:
        name, role, split = record.get('name'), record.get('role'), record.get('split')
        if not isinstance(name, str) or Path(name).name != name or '/' in name or '\\' in name or not name.endswith('.apk') or name in names or role not in ('base', 'split') or not isinstance(split, str) or (role == 'base') != (split == '') or split in splits:
            raise ValueError('Invalid verified APK identity')
        names.add(name); splits.add(split)
        path = root / name
        if path.is_symlink() or not path.is_file() or path.resolve().parent != root:
            raise ValueError('Unsafe or missing APK')
        if type(record.get('size')) is not int or not isinstance(record.get('sha256'), str):
            raise ValueError('Invalid verified APK digest')
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''): digest.update(chunk)
        if path.stat().st_size != record['size'] or digest.hexdigest() != record['sha256']:
            raise ValueError('Verified APK changed')
        try:
            with zipfile.ZipFile(path) as archive:
                for item in archive.infolist():
                    match = re.fullmatch(r'lib/([^/]+)/[^/]+\.so', item.filename)
                    if match:
                        abi = match.group(1)
                        if not re.fullmatch(r'[A-Za-z0-9_-]+', abi): raise ValueError('Invalid APK native ABI')
                        native.add(abi)
        except (OSError, zipfile.BadZipFile) as error:
            raise ValueError('Invalid APK ZIP') from error
        badging = _tool(['aapt2', 'dump', 'badging', str(path)])
        xml = _tool(['aapt2', 'dump', 'xmltree', str(path), '--file', 'AndroidManifest.xml'])
        if not re.search(r'^\s*E: manifest\b', xml, re.M) or not re.search(r'^package: ', badging, re.M):
            raise ValueError('Malformed APK metadata')
        if role == 'base':
            raw_lines = [line.strip() for line in badging.splitlines() if re.match(r"^(?:minSdkVersion|sdkVersion):", line.strip())]
            parsed = [re.fullmatch(r"(?:minSdkVersion|sdkVersion):'([0-9]+)'", line) for line in raw_lines]
            if any(match is None for match in parsed):
                raise ValueError('Invalid minimum Android SDK metadata')
            lines = [match.group(1) for match in parsed]
            if len(set(lines)) > 1 or any(int(x) <= 0 for x in lines):
                raise ValueError('Invalid minimum Android SDK metadata')
            minimum = int(lines[0]) if lines else 1
        for line in badging.splitlines():
            line = line.strip()
            if line.startswith('locales:'):
                rest = line[len('locales:'):]
                values = re.findall(r"'([^']*)'", rest)
                if re.sub(r"'[^']*'", '', rest).strip(): raise ValueError('Malformed locale metadata')
                for value in values:
                    if value == '--_--': continue
                    if not re.fullmatch(r'[A-Za-z0-9_-]+', value): raise ValueError('Malformed locale metadata')
                    languages.add(value)
            elif line.startswith('uses-feature:'):
                match = re.fullmatch(r"uses-feature: name='([^']+)'(?:.*)?", line)
                if not match or not re.fullmatch(r'[A-Za-z0-9_.-]+', match.group(1)): raise ValueError('Malformed feature metadata')
                features.add(match.group(1))
        required.update(_types(_xml_attributes(xml, 'requiredSplitTypes')))
        provided.update(_types(_xml_attributes(xml, 'splitTypes')))
        for match in re.finditer(r'^\s*E: uses-split\b[^\n]*\n((?:\s*A:[^\n]*\n?)*)', xml, re.M):
            attrs = _xml_attributes(match.group(1), 'name')
            if len(attrs) != 1 or not re.fullmatch(r'[A-Za-z0-9_.-]+', attrs[0]): raise ValueError('Malformed uses-split metadata')
            used.add(attrs[0])
        for line in xml.splitlines():
            if re.search(r'\bglEsVersion(?:\(0x[0-9a-fA-F]+\))?=', line):
                match = re.search(r'\bglEsVersion(?:\(0x[0-9a-fA-F]+\))?=(?:\(type 0x11\))?(0x[0-9a-fA-F]+|[0-9]+)(?:\s|$)', line)
                if not match:
                    raise ValueError('Malformed OpenGL ES metadata')
                value = match.group(1)
                current = int(value, 16 if value.startswith('0x') else 10)
                gl = max(gl or 0, current)
    if required - provided or used - splits:
        raise ValueError('Incomplete APK split set')
    if minimum > requestprofile['sdk']:
        raise ProfileIncompatible('min_sdk', minimum_sdk=minimum)
    if native and not native.intersection(requestprofile['abis']):
        raise ProfileIncompatible('abi')
    return {'min_sdk': minimum, 'abis': list(requestprofile['abis']), 'native_abis': sorted(native), 'density': requestprofile['density'], 'locale': requestprofile['locale'], 'languages': sorted(languages), 'required_features': sorted(features), 'gl_es_version': gl, 'required_split_types': sorted(required), 'provided_split_types': sorted(provided), 'uses_splits': sorted(used)}

