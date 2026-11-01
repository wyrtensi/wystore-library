import unittest
from unittest.mock import Mock
import base64
import json
from wystore_library.readme import render_readme, update_readme
from wystore_library.github import Publisher

class ReadmeTests(unittest.TestCase):
    def setUp(self):
        self.config = {'schema': 1, 'apps': [{'package': 'org.example.app', 'name': 'Example', 'category': 'Tools', 'profiles': ['px_9a']}]}
        self.index = {'schema': 1, 'entries': [{'package':'org.example.app', 'profile':'px_9a', 'version_code':42, 'version_name':'2.0'}]}
        self.catalog = {'schema':1, 'apps':[{'package':'org.example.app', 'metadataPath':'apps/org.example.app/metadata.json', 'icon':'apps/org.example.app/images/abc.png'}]}
        self.template = 'Before\n<!-- APP_CATALOG:START -->\nstale org.example.app-px_9a-41\n<!-- APP_CATALOG:END -->\nAfter\n'
    def test_regenerates_current_version_preserving_outside(self):
        result = render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
        self.assertTrue(result.startswith('Before\n<!-- APP_CATALOG:START -->'))
        self.assertTrue(result.endswith('<!-- APP_CATALOG:END -->\nAfter\n'))
        self.assertIn('org.example.app-px_9a-42', result)
        self.assertNotIn('org.example.app-px_9a-41', result)
        self.assertIn('2.0', result)
        self.assertIn('width="32"', result)
    def test_current_release_url_is_used_and_restricted_to_repository(self):
        self.index['entries'][0]['release_url'] = 'https://github.com/owner/repo/releases/tag/org.example.app-library'
        result = render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
        self.assertIn('(https://github.com/owner/repo/releases/tag/org.example.app-library)', result)
        for url in ('https://evil.test/', 'https://github.com/owner/repo/releases/tag/x)bad', 'https://github.com/other/repo/releases/tag/x'):
            self.index['entries'][0]['release_url'] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')

    def test_pending_and_multiple_profiles(self):
        self.config['apps'][0]['profiles'].append('other')
        result = render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
        self.assertIn('Pending', result)
        self.assertIn('other', result)
        self.assertEqual(result.count('org.example.app-px_9a-42'), 1)
    def test_profile_scope_does_not_change_link_and_apps_sort_by_name(self):
        self.index['entries'][0]['certificate_scope'] = {'mode':'android-sdk', 'sdk':35}
        self.config['apps'].append({'package':'org.example.zed', 'name':'Aardvark', 'category':'Other', 'profiles':['px_9a']})
        result = render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
        self.assertLess(result.index('Aardvark'), result.index('Example'))
        self.assertIn('org.example.app-px_9a-42', result)
        self.assertIn('Pending', result)
    def test_invalid_markers_and_duplicate_pairs_rejected(self):
        for template in ('none', self.template + '<!-- APP_CATALOG:START -->'):
            with self.subTest(template=template), self.assertRaises(ValueError):
                render_readme(template, self.config, self.index, self.catalog, 'owner/repo')
        self.index['entries'].append(dict(self.index['entries'][0]))
        with self.assertRaises(ValueError): render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
    def test_escapes_untrusted_text_and_rejects_unsafe_paths(self):
        self.config['apps'][0]['name'] = '<b>X|Y</b>'
        self.index['entries'][0]['version_name'] = '1|<script>'
        result = render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
        self.assertNotIn('<script>', result)
        self.assertNotIn('<b>', result)
        self.catalog['apps'][0]['icon'] = '../bad.png'
        with self.assertRaises(ValueError): render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
    def test_trailing_markdown_backslash_cannot_escape_link_closing_bracket(self):
        self.config['apps'][0]['name'] = 'Example' + chr(92)
        self.index['entries'][0]['version_name'] = '1.0' + chr(92)
        result = render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
        self.assertNotIn(chr(92) + '](', result)
        self.assertIn('org.example.app-px_9a-42', result)
    def test_remote_content_is_preserved_and_noop_avoids_write(self):
        publisher = Mock()
        publisher.repository = 'owner/repo'
        publisher.read_readme.return_value = (self.template, 'abc')
        update_readme(publisher, self.config, self.index, self.catalog)
        self.assertEqual(publisher.write_readme.call_args.args[1], 'abc')
        updated = publisher.write_readme.call_args.args[0]
        self.assertIn('Before', updated)
        publisher.reset_mock()
        publisher.read_readme.return_value = (updated, 'newsha')
        update_readme(publisher, self.config, self.index, self.catalog)
        publisher.write_readme.assert_not_called()

    def test_readme_write_uses_remote_sha_and_owner_identity(self):
        publisher = Publisher('owner/repo')
        publisher._gh = Mock(return_value=json.dumps({'encoding':'base64', 'sha':'remote-sha', 'content':base64.b64encode(self.template.encode()).decode()}))
        update_readme(publisher, self.config, self.index, self.catalog)
        body = json.loads(publisher._gh.call_args.kwargs['input_data'])
        self.assertEqual(body['sha'], 'remote-sha')
        self.assertEqual(body['author'], {'name':'wyrtensi', 'email':'wyrtensi@gmail.com'})
        self.assertEqual(body['committer'], body['author'])
        self.assertIn('After', base64.b64decode(body['content']).decode())

    def test_write_conflict_is_not_retried(self):
        publisher = Publisher('owner/repo')
        payload = json.dumps({'encoding':'base64', 'sha':'old', 'content':base64.b64encode(self.template.encode()).decode()})
        publisher._gh = Mock(side_effect=[payload, RuntimeError('conflict')])
        with self.assertRaises(RuntimeError):
            update_readme(publisher, self.config, self.index, self.catalog)
        self.assertEqual(publisher._gh.call_count, 2)

    def test_counts_variants_for_migrated_apps_and_defaults_for_legacy(self):
        self.config['apps'].append({'package': 'org.example.legacy', 'name': 'Legacy', 'profiles': ['px_9a']})
        self.index['entries'].append({'package': 'org.example.legacy', 'profile': 'px_9a', 'version_code': 1, 'version_name': '1'})
        self.index['applications'] = [{'package': 'org.example.app', 'name': 'Example', 'variants': [{'id': 'px_9a'}, {'id': 'arm64_ru'}, {'id': 'armv7_en'}, {'id': 'armv7_ru'}]}]
        result = render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
        self.assertIn('2 applications · 5 verified device variants · daily checks', result)
        self.assertIn('[4 variants](https://github.com/owner/repo/releases/tag/org.example.app-library)', result)
        self.assertIn('Default profile', result)
        self.assertEqual(result.count('[Example](library/apps/org.example.app/metadata.json)'), 1)

    def test_rejects_invalid_canonical_apps_and_duplicate_variants(self):
        for apps in ([{'package': 'org.example.app', 'name': 'Example', 'variants': [{'id': 'px_9a'}, {'id': 'px_9a'}]}], [{'package': 'org.example.app', 'name': '', 'variants': [{'id': 'px_9a'}]}], [{'package': 'org.example.app', 'name': 'Example', 'variants': []}], [{'package': 'org.example.app', 'name': 'Example', 'variants': [{'id': 'bad|id'}]}]):
            self.index['applications'] = apps
            with self.subTest(apps=apps), self.assertRaises(ValueError):
                render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')

    def test_empty_canonical_list_supports_legacy_index(self):
        self.index['applications'] = []
        result = render_readme(self.template, self.config, self.index, self.catalog, 'owner/repo')
        self.assertIn('1 verified device variants', result)
        self.assertIn('Default profile', result)
