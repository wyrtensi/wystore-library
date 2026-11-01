"""Stage coherent device variants before atomically switching the library feed."""
import copy
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from .compatibility import ProfileIncompatible, collect_compatibility
from .profiles import profile_fingerprint
from .sync import REPOSITORY, read_config
from .verification import verify_manifest


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode('utf-8')


def _descriptor(data, prefix, folder, url):
    digest = hashlib.sha256(data).hexdigest()
    name = f'{prefix}-{digest}.json'
    path = folder / name
    path.write_bytes(data)
    return {'name': name, 'sha256': digest, 'size': len(data), 'url': url(name)}, path


def _projection(app, repository):
    variant = next(v for v in app['variants'] if v['id'] == app['default_variant'])
    artifacts = {a['sha256']: a for a in app['artifacts']}
    assets = []
    for file in variant['files']:
        artifact = artifacts[file['artifact']]
        assets.append({'name': artifact['name'], 'sha256': artifact['sha256'], 'size': artifact['size'], 'url': artifact['url'], 'role': file['role'], 'split': file['split']})
    manifest = app['publication']['compat_manifest']
    result = {'package': app['package'], 'profile': app['default_variant'], 'version_code': variant['version_code'], 'version_name': variant['version_name'], 'certificate_sha256': variant['certificate_sha256'], 'assets': assets, 'manifest_url': manifest['url'], 'manifest_sha256': manifest['sha256'], 'manifest_size': manifest['size'], 'metadata_url': f"https://raw.githubusercontent.com/{repository}/main/library/apps/{app['package']}/metadata.json"}
    result['release_url'] = app['publication']['release_url']
    if 'certificate_scope' in variant:
        result['certificate_scope'] = variant['certificate_scope']
    return result


def run(config, repository, output, client, publisher, profiles, check_only=False, packages=None):
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
        raise ValueError('Invalid repository')
    pairs = read_config(config)
    config_data = json.loads(Path(config).read_text(encoding='utf-8-sig'))
    configured = {item['package']: item for item in config_data['apps']}
    if not isinstance(profiles, dict) or 'px_9a' not in profiles or any(key != value.get('id') for key, value in profiles.items()):
        raise ValueError('Invalid device profile registry')
    fingerprints = {key: profile_fingerprint(value) for key, value in profiles.items()}
    if packages is None:
        selected = list(configured)
    else:
        if not isinstance(packages, (list, tuple, set)) or len(set(packages)) != len(packages) or any(p not in configured for p in packages):
            raise ValueError('Unknown or duplicate selected package')
        selected = [p for p in configured if p in packages]
    index = publisher.read_index()
    if not isinstance(index, dict) or index.get('schema') != 1 or not isinstance(index.get('entries'), list):
        raise ValueError('Invalid published index')
    old_apps = index.get('applications', [])
    if not isinstance(old_apps, list) or any(not isinstance(a, dict) or not isinstance(a.get('package'), str) for a in old_apps):
        raise ValueError('Invalid published applications')
    applications = {a['package']: copy.deepcopy(a) for a in old_apps}
    if len(applications) != len(old_apps):
        raise ValueError('Duplicate published application')
    entries = {}
    for entry in index['entries']:
        if not isinstance(entry, dict) or not isinstance(entry.get('package'), str) or not isinstance(entry.get('profile'), str) or type(entry.get('version_code')) is not int or entry['version_code'] <= 0:
            raise ValueError('Invalid published entry')
        key = (entry['package'], entry['profile'])
        if key in entries:
            raise ValueError('Duplicate published entry')
        entries[key] = copy.deepcopy(entry)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    changed = False
    with tempfile.TemporaryDirectory(prefix='sync-', dir=output) as temp:
        root = Path(temp)
        for package in selected:
            old = applications.get(package)
            old_variants = {v['id']: copy.deepcopy(v) for v in old.get('variants', [])} if old else {}
            variants = dict(old_variants)
            unavailable = {u['id']: copy.deepcopy(u) for u in old.get('unavailable', [])} if old else {}
            artifacts = {a['sha256']: copy.deepcopy(a) for a in old.get('artifacts', [])} if old else {}
            legacy = entries.get((package, 'px_9a')) if not old else None
            new_paths = {}
            dirty = False
            for profile_id, profile in profiles.items():
                print(f'{package} {profile_id}: checking version', flush=True)
                result = client.info(package, profile_id)
                info = result.get('app') if isinstance(result, dict) else None
                if not isinstance(info, dict) or info.get('package') != package or type(info.get('version_code')) is not int or info['version_code'] < 0 or info.get('free') is not True:
                    raise ValueError('Play returned an unknown, paid or invalid version')
                version = info['version_code']
                previous = old_variants.get(profile_id)
                if version == 0:
                    if info.get('version_name') != '':
                        raise ValueError('Play returned an invalid unavailable version')
                    if profile_id == 'px_9a' and not previous:
                        raise ValueError(f'{package}: default px_9a has no available Play version')
                    record = {'id': profile_id, 'version_code': 0, 'profile_fingerprint': fingerprints[profile_id], 'reason': 'play_unavailable'}
                    if unavailable.get(profile_id) != record:
                        unavailable[profile_id] = record
                        dirty = True
                    continue
                if legacy and profile_id == 'px_9a' and version < legacy['version_code']:
                    raise ValueError(f'{package}: Play default version is older than the published legacy version')
                if unavailable.get(profile_id, {}).get('reason') == 'play_unavailable':
                    unavailable.pop(profile_id)
                    dirty = True
                if previous and version < previous['version_code']:
                    continue
                if previous and version == previous['version_code'] and previous['profile_fingerprint'] == fingerprints[profile_id]:
                    continue
                failed = unavailable.get(profile_id)
                if failed and failed.get('version_code') == version and failed.get('profile_fingerprint') == fingerprints[profile_id]:
                    continue
                dirty = True
                if check_only:
                    continue
                cert_source = previous or (legacy if profile_id == 'px_9a' else None)
                certs = cert_source.get('certificate_sha256') if cert_source else None
                if cert_source and (not isinstance(certs, list) or not certs):
                    raise ValueError('Previous publisher certificate is unavailable')
                folder = root / f'{package}-{profile_id}'
                folder.mkdir()
                print(f'{package} {profile_id}: downloading version {version}', flush=True)
                manifest = client.pull(package, profile_id, version, folder)
                try:
                    verified = verify_manifest(manifest, folder, package, version, certs, sdk=profile['sdk'])
                    compatibility = collect_compatibility(folder, verified, profile, manifest.get('device'))
                except ProfileIncompatible as error:
                    unavailable[profile_id] = {'id': profile_id, 'version_code': version, 'profile_fingerprint': fingerprints[profile_id], 'reason': error.reason}
                    if error.minimum_sdk is not None:
                        unavailable[profile_id]['minimum_sdk'] = error.minimum_sdk
                    shutil.rmtree(folder)
                    continue
                version_name = info.get('version_name')
                if version_name is not None and not isinstance(version_name, str):
                    raise ValueError('Invalid Play version name')
                files = []
                for record in verified['files']:
                    digest = record['sha256']
                    name = digest + '.apk'
                    url = f'https://github.com/{repository}/releases/download/{package}-library/{name}'
                    desc = {'name': name, 'sha256': digest, 'size': record['size'], 'url': url}
                    if digest in artifacts and artifacts[digest] != desc:
                        raise ValueError('Conflicting verified artifact')
                    artifacts[digest] = desc
                    if digest not in new_paths:
                        path = root / name
                        if not path.exists():
                            shutil.copyfile(folder / record['name'], path)
                        new_paths[digest] = path
                    files.append({'artifact': digest, 'original_name': record['name'], 'role': record['role'], 'split': record['split']})
                shutil.rmtree(folder)
                variant = {'id': profile_id, 'profile_fingerprint': fingerprints[profile_id], 'version_code': version, 'version_name': version_name or '', 'certificate_sha256': verified['certificate_sha256'], 'compatibility': compatibility, 'files': files}
                if 'certificate_scope' in verified:
                    variant['certificate_scope'] = verified['certificate_scope']
                variants[profile_id] = variant
                unavailable.pop(profile_id, None)
            if check_only:
                changed |= dirty
                continue
            if not dirty:
                continue
            if 'px_9a' not in variants:
                raise ValueError(f'{package}: default px_9a variant is unavailable; migration cannot proceed')
            used = {file['artifact'] for v in variants.values() for file in v['files']}
            if not used.issubset(artifacts):
                raise ValueError('Variant references missing artifact')
            app = {'package': package, 'name': configured[package].get('name') or package, 'default_variant': 'px_9a', 'variants': [variants[k] for k in sorted(variants)], 'artifacts': [artifacts[k] for k in sorted(used)], 'unavailable': [unavailable[k] for k in sorted(unavailable)]}
            tag = package + '-library'
            url = lambda name: f'https://github.com/{repository}/releases/download/{tag}/{name}'
            default = variants['px_9a']
            compat = {'package': package, 'version_code': default['version_code'], 'version_name': default['version_name'], 'profile': 'px_9a', 'certificate_sha256': default['certificate_sha256'], 'files': [{'name': artifacts[f['artifact']]['name'], 'sha256': f['artifact'], 'size': artifacts[f['artifact']]['size'], 'role': f['role'], 'split': f['split']} for f in default['files']]}
            if 'certificate_scope' in default:
                compat['certificate_scope'] = default['certificate_scope']
            manifest_desc, manifest_path = _descriptor(_json_bytes(compat), 'manifest', root, url)
            catalog_desc, catalog_path = _descriptor(_json_bytes(app), 'catalog', root, url)
            app['publication'] = {'tag': tag, 'release_url': f'https://github.com/{repository}/releases/tag/{tag}', 'catalog': catalog_desc, 'compat_manifest': manifest_desc}
            expected = {a['name']: {'sha256': a['sha256'], 'size': a['size']} for a in app['artifacts'] + [catalog_desc, manifest_desc]}
            paths = [new_paths[k] for k in used if k in new_paths] + [catalog_path, manifest_path]
            print(f'{package}: publishing {len(variants)} variants and {len(used)} unique APKs', flush=True)
            actual = publisher.publish_application(package, paths, expected, title=app['name'], notes='Choose one compatible variant from the library index.')
            if actual != {a['name']: a['url'] for a in app['artifacts'] + [catalog_desc, manifest_desc]}:
                raise RuntimeError('Published asset URLs differ from the expected stable URLs')
            for path in [*new_paths.values(), catalog_path, manifest_path]:
                path.unlink()
            applications[package] = app
            for key in [key for key in entries if key[0] == package]:
                del entries[key]
            entries[(package, 'px_9a')] = _projection(app, repository)
            changed = True
        if check_only:
            return changed
        if changed:
            new_index = copy.deepcopy(index)
            new_index.update({'schema': 1, 'variant_schema': 1, 'delivery_profiles': list(profiles.values()), 'applications': sorted(applications.values(), key=lambda a: a['package']), 'entries': sorted(entries.values(), key=lambda e: (e['package'], e['profile'])), 'migration_pending': sorted(set(configured) - set(applications))})
            index_path = root / 'index.json'
            index_path.write_bytes(_json_bytes(new_index))
            publisher.publish_index(index_path)
        publisher.cleanup_applications(sorted(applications.values(), key=lambda a: a['package']), sorted({profile for _, profile in pairs}), configured_packages=set(configured))
    return changed
