"""Synchronize the allowlisted Play APK sets to immutable GitHub releases."""
import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from .github import Publisher
from .verification import verify_manifest

PACKAGE = re.compile(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+')
PROFILE = re.compile(r'[A-Za-z0-9_]+')
REPOSITORY = re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+')


def read_config(path):
    config = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if config.get('schema') != 1 or not isinstance(config.get('apps'), list) or not config['apps']:
        raise ValueError('Invalid allowlist')
    pairs = []
    for app in config['apps']:
        package, profiles = app.get('package'), app.get('profiles')
        if not isinstance(package, str) or not PACKAGE.fullmatch(package) or not isinstance(profiles, list) or not profiles:
            raise ValueError('Invalid allowlist entry')
        for profile in profiles:
            if not isinstance(profile, str) or not PROFILE.fullmatch(profile) or (package, profile) in pairs:
                raise ValueError('Invalid or duplicate profile')
            pairs.append((package, profile))
    return pairs


def run(config, repository, output, client, publisher, check_only=False):
    if not REPOSITORY.fullmatch(repository):
        raise ValueError('Invalid repository')
    pairs = read_config(config)
    index = publisher.read_index()
    entries = {}
    for entry in index['entries']:
        key = (entry.get('package'), entry.get('profile'))
        if key in entries or not isinstance(entry.get('version_code'), int) or isinstance(entry['version_code'], bool) or entry['version_code'] <= 0:
            raise ValueError('Invalid published index entry')
        entries[key] = entry
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    changed = False
    with tempfile.TemporaryDirectory(prefix='sync-', dir=output) as temp:
        for package, profile in pairs:
            result = client.info(package, profile)
            app = result.get('app', result)
            version = app.get('version_code')
            if app.get('package') != package or type(version) is not int or version <= 0 or app.get('free') is not True:
                raise ValueError('Play returned an unknown, paid or invalid version')
            old = entries.get((package, profile))
            if old and version <= old['version_code']:
                continue
            if check_only:
                print(f'{package} {profile}: update available ({version})')
                continue
            previous = None
            if old:
                previous = old.get('certificate_sha256')
                if not isinstance(previous, list) or not previous:
                    raise ValueError('Previous publisher certificate is unavailable')
            expected = app.get('certificate_hashes')
            if not isinstance(expected, list) or not expected:
                raise ValueError('Play did not provide publisher certificates')
            folder = Path(temp) / f'{package}-{profile}-{version}'
            folder.mkdir()
            manifest = client.pull(package, profile, version, folder)
            public = verify_manifest(manifest, folder, package, version, expected, previous)
            version_name = app.get('version_name')
            if version_name is not None and not isinstance(version_name, str):
                raise ValueError('Invalid Play version name')
            public['version_name'] = version_name
            public['profile'] = profile
            metadata = folder / 'manifest-public.json'
            metadata.write_text(json.dumps(public, indent=2, sort_keys=True) + '\n', encoding='utf-8')
            files = [folder / f['name'] for f in public['files']] + [metadata]
            expected_assets = {f['name']: {'size': f['size'], 'sha256': f['sha256']} for f in public['files']}
            expected_assets[metadata.name] = {'size': metadata.stat().st_size, 'sha256': hashlib.sha256(metadata.read_bytes()).hexdigest()}
            tag = f'{package}-{profile}-{version}'
            urls = publisher.publish_release(tag, files, expected_assets)
            entries[(package, profile)] = {'package': package, 'profile': profile, 'version_code': version,
                'certificate_sha256': public['certificate_sha256'], 'version_name': version_name,
                'assets': [{**f, 'url': urls[f['name']]} for f in public['files']],
                'manifest_url': urls[metadata.name],
                'metadata_url': f'https://raw.githubusercontent.com/{repository}/main/library/apps/{package}/metadata.json'}
            changed = True
        if changed:
            index_path = Path(temp) / 'index.json'
            index_path.write_text(json.dumps({'schema': 1, 'entries': sorted(entries.values(), key=lambda e: (e['package'], e['profile']))}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
            publisher.publish_index(index_path)
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    from .play import PlayClient
    try:
        with PlayClient() as client:
            run(args.config, args.repository, args.output, client, Publisher(args.repository), args.check_only)
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from None
    except OSError:
        raise SystemExit('A required file or executable could not be accessed') from None

if __name__ == '__main__':
    main()
