"""Validate Play deliveries without publishing or retaining downloaded APKs."""
import argparse
import json
import tempfile
from pathlib import Path

from .compatibility import ProfileIncompatible, collect_compatibility
from .play import PlayClient, PlayError
from .profiles import load_profiles, profile_fingerprint
from .sync import read_config
from .verification import verify_manifest


class ValidationFailed(RuntimeError):
    """The validation stopped after recording a sanitized failure."""


def partition_packages(packages, batch_index, batch_count):
    if type(batch_index) is not int or type(batch_count) is not int or batch_count <= 0 or not 0 <= batch_index < batch_count:
        raise ValueError('Invalid batch')
    return list(packages)[batch_index::batch_count]


def _save(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    tmp.replace(path)


def _play_status(error):
    message = str(error).lower()
    if 'http 429' in message:
        return 'rate_limited'
    if 'authentication' in message or 'authorization' in message or 'configured private account' in message or 'google_email and google_aas_token are required' in message:
        return 'authentication_error'
    if 'timed out' in message:
        return 'network_timeout'
    return 'play_error'


def validate_batch(config, profiles, index, client, report_path, batch_index, batch_count):
    pairs = read_config(config)
    packages = list(dict.fromkeys(package for package, _ in pairs))
    selected = partition_packages(packages, batch_index, batch_count)
    if not selected:
        raise ValueError('Empty batch')
    if not isinstance(index, dict) or not isinstance(index.get('applications', []), list):
        raise ValueError('Invalid index')
    apps = {app['package']: app for app in index.get('applications', [])}
    report = {'schema': 1, 'published': False, 'batch_index': batch_index, 'batch_count': batch_count,
              'packages': selected, 'profile_ids': list(profiles), 'complete': False, 'records': []}
    _save(report_path, report)
    for package in selected:
        old = {v['id']: v for v in apps.get(package, {}).get('variants', [])}
        for pid, profile in profiles.items():
            record = {'package': package, 'profile': pid, 'profile_fingerprint': profile_fingerprint(profile)}
            stage = 'metadata'
            try:
                result = client.info(package, pid)
                info = result.get('app') if isinstance(result, dict) else None
                if (not isinstance(info, dict) or info.get('package') != package or type(info.get('version_code')) is not int
                        or info['version_code'] < 0 or info.get('free') is not True
                        or (info.get('version_name') is not None and not isinstance(info.get('version_name'), str))):
                    raise ValueError('Invalid Play metadata')
                version = info['version_code']
                record['version_code'] = version
                if version == 0:
                    if info.get('version_name') != '':
                        raise ValueError('Invalid unavailable metadata')
                    record['status'] = 'play_unavailable'
                else:
                    previous = old.get(pid)
                    certs = previous.get('certificate_sha256') if previous else None
                    if previous and (not isinstance(certs, list) or not certs):
                        raise ValueError('Previous certificate unavailable')
                    with tempfile.TemporaryDirectory(prefix='coverage-apks-') as temp:
                        folder = Path(temp)
                        stage = 'download'
                        manifest = client.pull(package, pid, version, folder)
                        stage = 'verification'
                        try:
                            verified = verify_manifest(manifest, folder, package, version, certs, sdk=profile['sdk'])
                            facts = collect_compatibility(folder, verified, profile, manifest.get('device'))
                            record.update(status='verified', file_count=len(verified['files']),
                                          previous_certificate_checked=certs is not None,
                                          min_sdk=facts['min_sdk'])
                        except ProfileIncompatible as error:
                            record.update(status='incompatible', reason=error.reason)
                            if error.minimum_sdk is not None:
                                record['minimum_sdk'] = error.minimum_sdk
            except PlayError as error:
                record.update(status=_play_status(error), stage=stage)
                report['records'].append(record)
                _save(report_path, report)
                raise ValidationFailed('Play validation failed; see the sanitized report') from None
            except Exception:
                record.update(status='verification_error' if stage == 'verification' else 'validation_error', stage=stage)
                report['records'].append(record)
                _save(report_path, report)
                raise ValidationFailed('Validation failed; see the sanitized report') from None
            report['records'].append(record)
            _save(report_path, report)
            print(f'{package} {pid}: {record["status"]}', flush=True)
    report['complete'] = True
    _save(report_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='apps.json')
    parser.add_argument('--profiles', default='delivery-profiles.json')
    parser.add_argument('--index', default='library/index.json')
    parser.add_argument('--report', required=True)
    parser.add_argument('--batch-index', required=True, type=int)
    parser.add_argument('--batch-count', required=True, type=int)
    args = parser.parse_args()
    try:
        profiles = load_profiles(args.profiles)
        index = json.loads(Path(args.index).read_text(encoding='utf-8-sig'))
        with PlayClient(profiles=profiles) as client:
            validate_batch(args.config, profiles, index, client, args.report, args.batch_index, args.batch_count)
    except ValidationFailed as error:
        raise SystemExit(str(error)) from None
    except PlayError as error:
        _save(args.report, {'schema': 1, 'published': False, 'complete': False, 'records': [], 'status': _play_status(error)})
        raise SystemExit('Play setup failed; see the sanitized report') from None
    except Exception:
        _save(args.report, {'schema': 1, 'published': False, 'complete': False, 'records': [], 'status': 'setup_error'})
        raise SystemExit('Validation setup failed; see the sanitized report') from None


if __name__ == '__main__':
    main()
