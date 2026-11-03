"""Refresh the public Play metadata catalog without using account credentials."""

import argparse
import hashlib
import html
import json
import os
import re
import ssl
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
from .catalog import foreign_category, category_slugs

MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_SCREENSHOTS = 8
# Language and Play market are independent. Mixing markets can return a stale
# regional card or hide an app even when its translation is available.
CATALOG_MARKET = 'us'
LOCALES = {'ru_RU': 'ru', 'en_US': 'en'}
IMAGE_TYPES = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp', 'image/gif': '.gif'}
PACKAGE = re.compile(r'^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$')


def validate_image_url(url):
    parts = urlsplit(url)
    host = (parts.hostname or '').lower()
    if (parts.scheme != 'https' or parts.username is not None or parts.password is not None
            or parts.port not in (None, 443) or not any(host == domain or host.endswith('.' + domain)
            for domain in ('googleusercontent.com', 'ggpht.com'))):
        raise ValueError('Untrusted image URL')
    return url


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_image_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_image(url):
    validate_image_url(url)
    opener = build_opener(SafeRedirectHandler(), HTTPSHandler(context=ssl.create_default_context()))
    request = Request(url, headers={'User-Agent': 'WyStoreLibrary/1.0'})
    with opener.open(request, timeout=30) as response:
        validate_image_url(response.geturl())
        content_type = response.headers.get_content_type().lower()
        if content_type not in IMAGE_TYPES:
            raise ValueError('Unsupported image content type: ' + content_type)
        length = response.headers.get('Content-Length')
        if length is not None and int(length) > MAX_IMAGE_BYTES:
            raise ValueError('Image exceeds size limit')
        body = response.read(MAX_IMAGE_BYTES + 1)
        if not body or len(body) > MAX_IMAGE_BYTES:
            raise ValueError('Image is empty or exceeds size limit')
        return body, content_type


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == content:
        return
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            name = stream.name
            stream.write(content)
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def write_json(path, value):
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def cache_image(url, image_dir, previous):
    validate_image_url(url)
    old = previous.get(url)
    if isinstance(old, str) and re.fullmatch(r'[0-9a-f]{64}\.(?:png|jpg|webp|gif)', old):
        path = image_dir / old
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == old.split('.')[0]:
            return old
    content, content_type = download_image(url)
    filename = hashlib.sha256(content).hexdigest() + IMAGE_TYPES[content_type]
    atomic_write(image_dir / filename, content)
    return filename


def clean_text(value):
    return value.strip() or None if isinstance(value, str) else None


def normalize_locale(data, package):
    updated = data.get('updated')
    if isinstance(updated, (int, float)) and not isinstance(updated, bool) and updated > 0:
        updated = datetime.fromtimestamp(updated, timezone.utc).date().isoformat()
    else:
        updated = None
    return {'title': clean_text(data.get('title')), 'developer': clean_text(data.get('developer')),
            'description': clean_text(data.get('description')), 'shortDescription': clean_text(data.get('summary')),
            'versionName': clean_text(data.get('version')), 'updatedDate': updated,
            'playUrl': 'https://play.google.com/store/apps/details?id=' + package,
            'changelog': clean_text(data.get('recentChanges'))}


def update_history(history, locale):
    result = list(history)
    if locale['changelog']:
        snapshot = {'versionName': locale['versionName'], 'updatedDate': locale['updatedDate'], 'text': locale['changelog']}
        if not result or result[-1] != snapshot:
            result.append(snapshot)
    return result


def field_at(data, *path):
    for index in path:
        if data is None:
            return None
        if not isinstance(data, list) or index >= len(data):
            raise ValueError('Unexpected Play metadata structure')
        data = data[index]
    return data


def parse_play_page(page):
    match = re.search(r'AF_initDataCallback\(\{\s*["\']?key["\']?\s*:\s*["\']ds:5["\']\s*,.*?["\']?data["\']?\s*:\s*', page, re.DOTALL)
    if not match:
        raise ValueError('Play metadata callback is missing')
    try:
        payload, _ = json.JSONDecoder().raw_decode(page[match.end():])
        data = field_at(payload, 1, 2)
        if isinstance(data, list) and data and isinstance(data[-1], dict):
            sparse = data[-1]
            if not any(key in sparse for key in ('141', '145', '146')):
                raise ValueError('Play release metadata fields are missing')
            expanded = data[:-1] + [None] * max(0, 146 - len(data) + 1)
            for key, value in sparse.items():
                if key.isdecimal() and 0 < int(key) <= len(expanded):
                    expanded[int(key) - 1] = value
            data = expanded
        if not isinstance(data, list) or len(data) <= 145:
            raise ValueError('Play metadata fields are missing')
        description = field_at(data, 72, 0, 1) or field_at(data, 12, 0, 0, 1)
        screenshots = field_at(data, 78, 0)
        if screenshots is not None and not isinstance(screenshots, list):
            raise ValueError('Invalid Play screenshots')
        result = {
            'title': field_at(data, 0, 0), 'developer': field_at(data, 68, 0),
            'description': description, 'summary': field_at(data, 73, 0, 1),
            'version': field_at(data, 140, 0, 0, 0), 'updated': field_at(data, 145, 0, 1, 0),
            'recentChanges': field_at(data, 144, 1, 1), 'icon': field_at(data, 95, 0, 3, 2),
            'screenshots': [field_at(item, 3, 2) for item in (screenshots or [])],
        }
        for key in ('title', 'developer', 'description'):
            if not isinstance(result[key], str) or not result[key].strip():
                raise ValueError('Missing required Play field: ' + key)
        for key in ('title', 'developer', 'description', 'summary', 'version', 'recentChanges'):
            if result[key] is not None:
                if not isinstance(result[key], str):
                    raise ValueError('Invalid Play field: ' + key)
                result[key] = html.unescape(result[key])
        return result
    except (json.JSONDecodeError, IndexError, TypeError) as exc:
        raise ValueError('Malformed Play metadata') from exc


class PlayRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urlsplit(newurl)
        if (parts.scheme != 'https' or parts.hostname != 'play.google.com'
                or parts.username is not None or parts.password is not None or parts.port not in (None, 443)):
            raise ValueError('Untrusted Play redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_app(package, locale):
    if not PACKAGE.fullmatch(package):
        raise ValueError('Invalid package')
    language = LOCALES[locale]
    url = 'https://play.google.com/store/apps/details?' + urlencode({'id': package, 'hl': language, 'gl': CATALOG_MARKET})
    opener = build_opener(PlayRedirectHandler(), HTTPSHandler(context=ssl.create_default_context()))
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with opener.open(request, timeout=30) as response:
        content = response.read(8 * 1024 * 1024 + 1)
        if len(content) > 8 * 1024 * 1024:
            raise ValueError('Play page exceeds size limit')
    return parse_play_page(content.decode('utf-8'))


def read_json(path, default):
    if not path.exists():
        return default
    with path.open(encoding='utf-8') as stream:
        return json.load(stream)


def refresh_catalog(catalog_path: Path, output_root: Path) -> dict:
    config = read_json(Path(catalog_path), None)
    if not isinstance(config, dict) or not isinstance(config.get('apps'), list):
        raise ValueError('Invalid app configuration')
    packages = [entry.get('package') for entry in config['apps'] if isinstance(entry, dict)]
    if (len(packages) != len(config['apps']) or len(packages) != len(set(packages))
            or any(not isinstance(p, str) or not PACKAGE.fullmatch(p) for p in packages)):
        raise ValueError('Invalid or duplicate package in app configuration')
    membership = {entry['package']: foreign_category(entry) for entry in config['apps']}
    categories = {entry['package']: category_slugs(entry) for entry in config['apps']}
    output_root = Path(output_root)
    catalog_file = output_root / 'catalog.json'
    old_catalog = read_json(catalog_file, {'apps': []})
    old_cards = {card['package']: card for card in old_catalog.get('apps', [])}
    cards, failures, successes = [], [], []
    for package in packages:
        try:
            app_dir = output_root / 'apps' / package
            previous = read_json(app_dir / 'metadata.json', {})
            previous_sources = previous.get('imageSources', {})
            sources, locales, history = {}, {}, previous.get('changelogHistory', {})
            for locale in LOCALES:
                data = fetch_app(package, locale)
                normalized = normalize_locale(data, package)
                if not normalized['title'] or not normalized['developer']:
                    raise ValueError('Missing title or developer for ' + locale)
                urls = []
                icon = data.get('icon')
                if icon:
                    urls.append(icon)
                screenshots = data.get('screenshots') or []
                if not isinstance(screenshots, list):
                    raise ValueError('Invalid screenshots for ' + locale)
                urls.extend(screenshots[:MAX_SCREENSHOTS])
                files = []
                for url in urls:
                    filename = cache_image(url, app_dir / 'images', previous_sources)
                    sources[url] = filename
                    files.append('images/' + filename)
                normalized['icon'] = files.pop(0) if icon else None
                normalized['screenshots'] = files
                locales[locale] = normalized
                history[locale] = update_history(history.get(locale, []), normalized)
            record = {'schema': 1, 'package': package, 'market': CATALOG_MARKET, 'locales': locales,
                      'changelogHistory': history, 'imageSources': sources}
            write_json(app_dir / 'metadata.json', record)
            card = {'package': package, 'metadataPath': 'apps/' + package + '/metadata.json',
                    'title': locales['ru_RU']['title'], 'developer': locales['ru_RU']['developer'],
                    'icon': ('apps/' + package + '/' + locales['ru_RU']['icon']) if locales['ru_RU']['icon'] else None,
                    'foreign_category': membership[package],
                    'locales': {locale: {'title': data['title'], 'shortDescription': data['shortDescription']}
                                for locale, data in locales.items()}}
            if categories[package]:
                card['categories'] = categories[package]
            cards.append(card)
            successes.append(package)
        except Exception as exc:
            failures.append({'package': package, 'error': str(exc)})
            if package in old_cards:
                card = {**old_cards[package], 'foreign_category': membership[package]}
                if categories[package]:
                    card['categories'] = categories[package]
                else:
                    card.pop('categories', None)
                cards.append(card)
    write_json(catalog_file, {'schema': 1, 'market': CATALOG_MARKET, 'apps': cards})
    return {'updated': successes, 'failures': failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('apps.json'))
    parser.add_argument('--output', type=Path, default=Path('library'))
    args = parser.parse_args()
    try:
        result = refresh_catalog(args.config, args.output)
    except Exception as exc:
        print('Metadata refresh failed: ' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['failures'] else 0


if __name__ == '__main__':
    sys.exit(main())
