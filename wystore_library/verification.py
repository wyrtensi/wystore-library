"""Verify downloaded APK sets before they can be published."""
import base64
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


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


def inspect_apk(path):
    tool_output = {}
    def invoke(args):
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        if result.returncode:
            raise ValueError('APK inspection failed: ' + args[0])
        tool_output[args[0]] = result
        return result.stdout
    signature = invoke(['apksigner', 'verify', '--verbose', '--print-certs', str(path)])
    badging = invoke(['aapt', 'dump', 'badging', str(path)])
    header = next((line for line in badging.splitlines() if line.startswith('package: ')), '')
    def field(name):
        found = re.search(r"(?:^|\s)" + name + r"='([^']*)'", header)
        return found.group(1) if found else ''
    # Build-tools 37 names APK signers by scheme. Source Stamp signers and
    # public-key fingerprints describe different identities and must not match.
    signer = r'^[ \t]*(?:Signer #\d+:?|V(?:1|2|3\.[01]) Signer(?: #\d+)?:)[ \t]+certificate '
    sha256 = {m.lower() for m in re.findall(signer + r'SHA-256 digest:[ \t]+([0-9a-fA-F]{64})[ \t]*$', signature, re.MULTILINE)}
    sha1 = {m.lower() for m in re.findall(signer + r'SHA-1 digest:[ \t]+([0-9a-fA-F]{40})[ \t]*$', signature, re.MULTILINE)}
    if not sha256 or len(sha256) != len(sha1) or not field('versionCode').isdigit():
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
                         f'signer labels: {", ".join(labels) or "none"}; aapt fields: {", ".join(fields) or "none"}; '
                         f'tool output: {json.dumps(details)})')
    return field('name'), int(field('versionCode')), field('split'), sha256, sha1


def verify_manifest(manifest, directory, package, version, expected, previous):
    if not isinstance(manifest, dict) or manifest.get('schema') != 'playfetch/v1':
        raise ValueError('Unsupported downloaded manifest schema')
    app = manifest.get('app')
    if not isinstance(app, dict):
        raise ValueError('Invalid downloaded manifest app')
    if app.get('package') != package or app.get('version_code') != version:
        raise ValueError('Downloaded manifest package or version differs from Play metadata')
    records = manifest.get('files')
    if not isinstance(records, list) or not records or manifest.get('bundle'):
        raise ValueError('Unsupported or empty delivery')
    directory = Path(directory).resolve()
    names, splits, certs = set(), set(), None
    public_files = []
    trusted = {v for h in expected for v in (digest(h, 32), digest(h, 20)) if v}
    if not trusted:
        raise ValueError('Play did not provide a usable publisher certificate')
    for record in records:
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
        actual_package, actual_version, split, signing256, signing1 = inspect_apk(path)
        if actual_package != package or actual_version != version:
            raise ValueError('APK package or version mismatch')
        if (role == 'base' and split) or (role == 'split' and (not split or record.get('split') != split)) or split in splits:
            raise ValueError('APK split identity mismatch')
        splits.add(split)
        if not (signing256 <= trusted or signing1 <= trusted):
            raise ValueError('APK certificate does not match Play')
        if certs is not None and certs != signing256:
            raise ValueError('APK split signatures differ')
        certs = signing256
        public_files.append({'name': name, 'role': role, 'split': split, 'size': path.stat().st_size, 'sha256': sha256})
    if '' not in splits or sum(f['role'] == 'base' for f in public_files) != 1:
        raise ValueError('APK set must contain one base')
    if previous is not None and set(previous) != certs:
        raise ValueError('Publisher signing certificate changed; manual review required')
    return {'package': package, 'version_code': version, 'certificate_sha256': sorted(certs), 'files': public_files}
