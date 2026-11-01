"""Render the public catalog inside the README using the published APK index."""
import argparse
import html
import json
import re
from pathlib import Path

from .github import Publisher

START = '<!-- APP_CATALOG:START -->'
END = '<!-- APP_CATALOG:END -->'
PACKAGE = re.compile(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+')
PROFILE = re.compile(r'[A-Za-z0-9_]+')
REPOSITORY = re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+')


def text(value):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise ValueError('Invalid public text')
    return html.escape(value, quote=True).replace('\\', '&#92;').replace('|', '&#124;').replace('[', '&#91;').replace(']', '&#93;').replace('`', '&#96;')


def local_path(value, package, kind):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError('Invalid catalog path')
    pattern = (rf'apps/{re.escape(package)}/metadata\.json' if kind == 'metadata' else
               rf'apps/{re.escape(package)}/images/[a-zA-Z0-9_.-]+')
    if not re.fullmatch(pattern, value) or '..' in value:
        raise ValueError('Invalid catalog path')
    return 'library/' + value


def render_readme(template, config, index, catalog, repository):
    if not isinstance(template, str) or template.count(START) != 1 or template.count(END) != 1 or template.index(START) > template.index(END):
        raise ValueError('Invalid README catalog markers')
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository) or '..' in repository:
        raise ValueError('Invalid repository')
    for data, key in ((config, 'apps'), (index, 'entries'), (catalog, 'apps')):
        if not isinstance(data, dict) or type(data.get('schema')) is not int or data['schema'] != 1 or not isinstance(data.get(key), list):
            raise ValueError('Invalid catalog input')
    entries = {}
    for entry in index['entries']:
        if not isinstance(entry, dict): raise ValueError('Invalid index entry')
        package, profile, code, name = entry.get('package'), entry.get('profile'), entry.get('version_code'), entry.get('version_name')
        if (not isinstance(package, str) or not PACKAGE.fullmatch(package) or not isinstance(profile, str) or not PROFILE.fullmatch(profile)
                or type(code) is not int or code <= 0 or (name is not None and not isinstance(name, str)) or (package, profile) in entries):
            raise ValueError('Invalid index entry')
        entries[package, profile] = entry
    canonical = {}
    applications = index.get('applications', [])
    if not isinstance(applications, list):
        raise ValueError('Invalid canonical applications')
    for application in applications:
        if not isinstance(application, dict):
            raise ValueError('Invalid canonical application')
        package, variants = application.get('package'), application.get('variants')
        if not isinstance(package, str) or not PACKAGE.fullmatch(package) or package in canonical or not isinstance(variants, list) or not variants:
            raise ValueError('Invalid canonical application')
        text(application.get('name'))
        identifiers = set()
        for variant in variants:
            if not isinstance(variant, dict) or not isinstance(variant.get('id'), str) or not PROFILE.fullmatch(variant['id']) or variant['id'] in identifiers:
                raise ValueError('Invalid canonical variant')
            identifiers.add(variant['id'])
        canonical[package] = len(identifiers)
    cards = {}
    for card in catalog['apps']:
        if not isinstance(card, dict) or not isinstance(card.get('package'), str) or not PACKAGE.fullmatch(card['package']) or card['package'] in cards:
            raise ValueError('Invalid catalog entry')
        package = card['package']
        cards[package] = (local_path(card.get('metadataPath'), package, 'metadata'), local_path(card.get('icon'), package, 'icon'))
    apps = []
    packages = set()
    for app in config['apps']:
        if not isinstance(app, dict): raise ValueError('Invalid configured app')
        package, profiles = app.get('package'), app.get('profiles')
        if (not isinstance(package, str) or not PACKAGE.fullmatch(package) or package in packages or not isinstance(profiles, list) or not profiles
                or any(not isinstance(p, str) or not PROFILE.fullmatch(p) for p in profiles) or len(set(profiles)) != len(profiles)):
            raise ValueError('Invalid configured app')
        packages.add(package)
        name = app.get('name', package)
        category = app.get('category', 'Other')
        text(name); text(category)
        apps.append((name, category, package, profiles))
    rows = ['| Application | Collection | Current version | Device variants | Google Play |', '| --- | --- | --- | --- | --- |']
    published = 0
    for name, category, package, profiles in sorted(apps, key=lambda a: (a[0].casefold(), a[2])):
        metadata, icon = cards.get(package, (None, None))
        label = text(name)
        if metadata: label = f'[{label}]({metadata})'
        if icon: label = f'<img src="{icon}" width="32" alt=""> {label}'
        versions = []
        for profile in profiles:
            entry = entries.get((package, profile))
            prefix = text(profile) + ': ' if len(profiles) > 1 else ''
            if entry is None:
                versions.append(prefix + 'Pending')
                continue
            code = entry['version_code']
            value = entry.get('version_name') or str(code)
            value = value[:57] + '...' if len(value) > 60 else value
            url = entry.get('release_url')
            if url is None:
                url = f'https://github.com/{repository}/releases/tag/{package}-{profile}-{code}'
            elif url != f'https://github.com/{repository}/releases/tag/{package}-library':
                raise ValueError('Invalid release URL')
            versions.append(prefix + f'[{text(value)}]({url})')
        has_entry = any((package, profile) in entries for profile in profiles)
        if has_entry and package in canonical:
            count = canonical[package]
            published += count
            variant_label = 'variant' if count == 1 else 'variants'
            variants_cell = f'[{count} {variant_label}](https://github.com/{repository}/releases/tag/{package}-library)'
        elif has_entry:
            published += 1
            variants_cell = 'Default profile'
        else:
            variants_cell = 'Pending'
        rows.append(f'| {label} | {text(category)} | {"<br>".join(versions)} | {variants_cell} | [Google Play](https://play.google.com/store/apps/details?id={package}) |')
    body = f'\n\n**{len(apps)} applications · {published} verified device variants · daily checks**\n\n' + '\n'.join(rows) + '\n\n'
    return template[:template.index(START) + len(START)] + body + template[template.index(END):]


def update_readme(publisher, config, index, catalog):
    original, sha = publisher.read_readme()
    updated = render_readme(original, config, index, catalog, publisher.repository)
    if updated != original:
        publisher.write_readme(updated, sha)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true', required=True)
    parser.add_argument('--repository', required=True)
    args = parser.parse_args()
    def load(path):
        return json.loads(Path(path).read_text(encoding='utf-8'))
    update_readme(Publisher(args.repository), load('apps.json'), load('library/index.json'), load('library/catalog.json'))


if __name__ == '__main__':
    main()
