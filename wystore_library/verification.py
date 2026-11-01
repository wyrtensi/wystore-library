"""Verify downloaded APK sets before they can be published."""
import base64
import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .compatibility import ProfileIncompatible


def digest(value, size):
    if not isinstance(value, str):
        return None
    value = value.strip().replace(':', '')
    if re.fullmatch(r'[0-9a-fA-F]{%d}' % (size * 2), value):
        return value.lower()
    try:
        decoded = base64.b64decode(value + '=' * (-len(value) % 4), altchars=b'-_', validate=True)
        return decoded.hex() if len(decoded) == size else None
    except (ValueError, TypeError):
        return None


@dataclass
class ApkInspection:
    package: str
    version_code: int
    split: str
    certificate_sha256: set
    certificate_sha1: set
    certificate_scope: dict | None = None
    min_sdk: int = 1


def inspect_apk_details(path, sdk=None, verification_min_sdk=None):
    if sdk is not None and (type(sdk) is not int or sdk <= 0):
        raise ValueError('Invalid Android SDK')
    if verification_min_sdk is not None and (type(verification_min_sdk) is not int or verification_min_sdk <= 0):
        raise ValueError('Invalid verification minimum Android SDK')
    tool_output = {}
    def invoke(args):
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        if result.returncode:
            raise ValueError('APK inspection failed: ' + args[0])
        tool_output[args[0]] = result
        return result.stdout
    command = ['apksigner', 'verify', '--verbose', '--print-certs']
    if verification_min_sdk is not None:
        command += ['--min-sdk-version', str(verification_min_sdk)]
    signature = invoke(command + [str(path)])
    badging = invoke(['aapt2', 'dump', 'badging', str(path)])
    header = next((line for line in badging.splitlines() if line.startswith('package: ')), '')
    def field(name):
        found = re.search(r"(?:^|\s)" + name + r"='([^']*)'", header)
        return found.group(1) if found else ''
    minimum_lines = [line.strip() for line in badging.splitlines()
                     if re.match(r'^(?:minSdkVersion|sdkVersion):', line.strip())]
    minimum_values = [re.fullmatch(r"(?:minSdkVersion|sdkVersion):'([0-9]+)'", line)
                      for line in minimum_lines]
    if any(value is None for value in minimum_values):
        raise ValueError('Invalid minimum Android SDK metadata')
    minimums = {int(value.group(1)) for value in minimum_values}
    if len(minimums) > 1 or any(value <= 0 for value in minimums):
        raise ValueError('Conflicting or invalid minimum Android SDK metadata')
    minimum = next(iter(minimums), 1)
    # Build-tools 37 names APK signers by scheme. Source Stamp signers and
    # public-key fingerprints describe different identities and must not match.
    # Rotated signing keys can apply to different Android SDK ranges.
    sdk_range = r'\(minSdkVersion=([0-9]+), maxSdkVersion=([0-9]+)\)'
    signer = re.compile(r'^(?P<label>(?:Signer #[0-9]+:?|V(?:1|2|3\.[01]) Signer(?: #[0-9]+)?:)(?:[ \t]+' + sdk_range + r')?|Signer[ \t]+' + sdk_range + r')[ \t]+certificate SHA-(?P<kind>256|1) digest:[ \t]+(?P<value>[0-9a-fA-F]+)[ \t]*$')
    identities = {}
    malformed = False
    for line in signature.splitlines():
        line = line.strip()
        if line.startswith('Source Stamp ') or ' public key ' in line:
            continue
        if not re.search(r'\bcertificate SHA-(?:256|1) digest:', line):
            continue
        match = signer.fullmatch(line)
        if not match or len(match['value']) != (64 if match['kind'] == '256' else 40):
            malformed = True
            continue
        bounds = (match.group(2), match.group(3)) if match.group(2) is not None else (match.group(4), match.group(5))
        limits = tuple(map(int, bounds)) if bounds[0] is not None else None
        if limits and (limits[0] <= 0 or limits[0] > limits[1]):
            malformed = True
            continue
        entry = identities.setdefault(match['label'], {'limits': limits})
        value = match['value'].lower()
        if match['kind'] in entry and entry[match['kind']] != value:
            malformed = True
        entry[match['kind']] = value
    malformed |= any('256' not in item or '1' not in item for item in identities.values())
    complete = [item for item in identities.values() if '256' in item and '1' in item]
    all_pairs = {(item['256'], item['1']) for item in complete}
    selected = {(item['256'], item['1']) for item in complete
                if sdk is None or item['limits'] is None or item['limits'][0] <= sdk <= item['limits'][1]}
    sha256 = {pair[0] for pair in selected}
    sha1 = {pair[1] for pair in selected}
    if (not malformed and complete and len({pair[0] for pair in all_pairs}) == len({pair[1] for pair in all_pairs})
            and field('name') and field('versionCode').isdigit() and sdk is not None
            and verification_min_sdk is None and not field('split') and minimum > sdk):
        raise ProfileIncompatible("min_sdk", minimum_sdk=minimum)
    if malformed or not selected or len(sha256) != len(sha1) or not field('versionCode').isdigit():
        # Tool versions can change labels. Report their structure, never raw
        # certificate values or other output that may contain private data.
        labels = sorted({line.partition(':')[0].strip() for line in signature.splitlines()
                         if 'SHA-' in line.partition(':')[0]
                         and re.fullmatch(r'Signer [A-Za-z0-9 #()=,._/\-]{1,160}', line.partition(':')[0].strip())})
        fields = sorted(set(re.findall(r'([A-Za-z]+)=', header)))
        def shape(output):
            output = output or ''
            prefixes = {line.rpartition(':')[0].strip()[:160] for line in output.splitlines()
                        if ':' in line and re.search(r'\bSHA[- ]?(?:256|1)\b', line.rpartition(':')[0])}
            return {'bytes': len(output.encode('utf-8')), 'lines': len(output.splitlines()),
                    'sha256_mentions': len(re.findall(r'\bSHA[- ]?256\b', output)),
                    'sha1_mentions': len(re.findall(r'\bSHA[- ]?1\b', output)),
                    'certificate_mentions': output.lower().count('certificate'),
                    'signer_mentions': output.count('Signer'), 'labels': sorted(prefixes)}
        details = {tool: {'executable': shutil.which(tool), 'stdout': shape(result.stdout),
                          'stderr': shape(result.stderr)} for tool, result in tool_output.items()}
        raise ValueError('APK signature or package metadata missing '
                         f'(sha256={len(sha256)}, sha1={len(sha1)}, version_code={field("versionCode").isdigit()}; '
                         f'signer labels: {", ".join(labels) or "none"}; manifest fields: {", ".join(fields) or "none"}; '
                         f'tool output: {json.dumps(details)})')
    scope = {'mode': 'android-sdk', 'sdk': sdk} if sdk is not None and all_pairs - selected else None
    return ApkInspection(field('name'), int(field('versionCode')), field('split'), sha256, sha1, scope, minimum)


def inspect_apk(path):
    result = inspect_apk_details(path)
    return result.package, result.version_code, result.split, result.certificate_sha256, result.certificate_sha1


def verify_manifest(manifest, directory, package, version, previous, sdk=None):
    if not isinstance(manifest, dict) or manifest.get('schema') != 'playfetch/v1':
        raise ValueError('Unsupported downloaded manifest schema')
    if sdk is not None and (type(sdk) is not int or sdk <= 0 or not isinstance(manifest.get('device'), dict) or type(manifest['device'].get('sdk')) is not int or manifest['device']['sdk'] != sdk):
        raise ValueError('Downloaded manifest Android SDK does not match device profile')
    app = manifest.get('app')
    if not isinstance(app, dict):
        raise ValueError('Invalid downloaded manifest app')
    if app.get('package') != package or app.get('version_code') != version:
        raise ValueError('Downloaded manifest package or version differs from Play metadata')
    records = manifest.get('files')
    if not isinstance(records, list) or not records or manifest.get('bundle'):
        raise ValueError('Unsupported or empty delivery')
    if any(not isinstance(record, dict) for record in records):
        raise ValueError('Invalid downloaded file record')
    bases = [record for record in records if record.get('role') == 'base']
    if len(bases) != 1:
        raise ValueError('APK set must contain one base')
    ordered = bases + [record for record in records if record is not bases[0]]
    directory = Path(directory).resolve()
    names, splits, certs, scope = set(), set(), None, None
    public_files = []
    base_minimum = None
    incompatibility = None
    for record in ordered:
        if not isinstance(record, dict) or not isinstance(record.get('local'), dict):
            raise ValueError('Invalid downloaded file record')
        name, role = record.get('name'), record.get('role')
        if not isinstance(name, str) or Path(name).name != name or '/' in name or '\\' in name or name in names or not name.endswith('.apk') or role not in ('base', 'split'):
            raise ValueError('Unsupported or unsafe delivery file')
        names.add(name)
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.resolve().parent != directory:
            raise ValueError('Unsafe or missing APK')
        contents_sha256, contents_sha1 = hashlib.sha256(), hashlib.sha1()
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                contents_sha256.update(chunk); contents_sha1.update(chunk)
        sha256, sha1 = contents_sha256.hexdigest(), contents_sha1.hexdigest()
        if record.get('size') != path.stat().st_size or digest((record.get('local') or {}).get('sha256'), 32) != sha256:
            raise ValueError('APK differs from local manifest hash or size')
        checks = [(record.get('play_sha256'), 32, sha256), (record.get('play_sha1'), 20, sha1)]
        provided = [(v, n, actual) for v, n, actual in checks if v]
        if not provided or any(digest(v, n) != actual for v, n, actual in provided):
            raise ValueError('APK differs from Google delivery hashes')
        # Resource splits can omit uses-sdk. Their standalone default of API 1
        # would incorrectly demand a JAR signature even when the verified base
        # supports only newer Android. Keep the application's full SDK range.
        try:
            inspection = inspect_apk_details(path, None if incompatibility else sdk, verification_min_sdk=base_minimum)
        except ProfileIncompatible as error:
            if role != 'base' or error.reason != 'min_sdk':
                raise
            # No signer may cover an unsupported SDK. Authenticate the entire
            # delivery using all verified signer ranges before reporting it.
            inspection = inspect_apk_details(path, None, verification_min_sdk=base_minimum)
            if inspection.min_sdk != error.minimum_sdk:
                raise ValueError('Inconsistent minimum Android SDK metadata')
            incompatibility = error
        if role == 'base':
            base_minimum = inspection.min_sdk
            if sdk is not None and base_minimum > sdk and incompatibility is None:
                incompatibility = ProfileIncompatible('min_sdk', minimum_sdk=base_minimum)
        actual_package, actual_version, split = inspection.package, inspection.version_code, inspection.split
        signing256 = inspection.certificate_sha256
        if inspection.certificate_scope:
            scope = inspection.certificate_scope
        if actual_package != package or actual_version != version:
            raise ValueError('APK package or version mismatch')
        if (role == 'base' and split) or (role == 'split' and (not split or record.get('split') != split)) or split in splits:
            raise ValueError('APK split identity mismatch')
        splits.add(split)
        if certs is not None and certs != signing256:
            raise ValueError('APK split signatures differ')
        certs = signing256
        public_files.append({'name': name, 'role': role, 'split': split, 'size': path.stat().st_size, 'sha256': sha256})
    if '' not in splits or sum(f['role'] == 'base' for f in public_files) != 1:
        raise ValueError('APK set must contain one base')
    if previous is not None and set(previous) != certs:
        raise ValueError('Publisher signing certificate changed; manual review required')
    if incompatibility is not None:
        raise incompatibility
    order = {record['name']: position for position, record in enumerate(records)}
    public_files.sort(key=lambda record: order[record['name']])
    result = {'package': package, 'version_code': version, 'certificate_sha256': sorted(certs), 'files': public_files}
    if scope:
        result['certificate_scope'] = scope
    return result
