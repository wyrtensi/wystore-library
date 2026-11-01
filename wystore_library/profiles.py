"""Validated, deterministic device sampling profile definitions."""
import hashlib
import json
from pathlib import Path
import re


def validate_profile(profile):
    if not isinstance(profile, dict) or set(profile) != {'id', 'base', 'sdk', 'abis', 'density', 'locale'}:
        raise ValueError('Invalid device profile fields')
    if any(not isinstance(profile[k], str) or not re.fullmatch(r'[a-zA-Z0-9_]+', profile[k]) for k in ('id', 'base')):
        raise ValueError('Invalid device profile identifier')
    if type(profile['sdk']) is not int or profile['sdk'] <= 0 or type(profile['density']) is not int or profile['density'] <= 0:
        raise ValueError('Invalid device profile SDK or density')
    if not isinstance(profile['abis'], list) or not profile['abis'] or any(not isinstance(x, str) or x not in ('arm64-v8a', 'armeabi-v7a', 'x86', 'x86_64') for x in profile['abis']) or len(set(profile['abis'])) != len(profile['abis']):
        raise ValueError('Invalid device profile ABIs')
    if not isinstance(profile['locale'], str) or not re.fullmatch(r'[a-z]{2,3}_[A-Z]{2}', profile['locale']):
        raise ValueError('Invalid device profile locale')
    return profile


def load_profiles(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as error:
        raise ValueError('Invalid device profile registry') from error
    if not isinstance(data, list) or not data:
        raise ValueError('Invalid device profile registry')
    result = {}
    for profile in data:
        validate_profile(profile)
        if profile['id'] in result:
            raise ValueError('Duplicate device profile')
        result[profile['id']] = profile
    return result


def profile_fingerprint(profile):
    validate_profile(profile)
    return hashlib.sha256(json.dumps(profile, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
