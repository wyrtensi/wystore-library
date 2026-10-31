import json
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from wystore_library import metadata


class MetadataTests(unittest.TestCase):
    def test_translations_use_one_catalog_market_without_changing_language(self):
        fixture = Path(__file__).parent / 'fixtures' / 'metadata' / 'planfix-play.html'
        queries = []

        class Opener:
            def open(self, request, timeout):
                queries.append(parse_qs(urlsplit(request.full_url).query))
                return io.BytesIO(fixture.read_bytes())

        with patch.object(metadata, 'build_opener', return_value=Opener()):
            metadata.fetch_app('org.example.app', 'ru_RU')
            metadata.fetch_app('org.example.app', 'en_US')
        self.assertEqual([query['hl'] for query in queries], [['ru'], ['en']])
        self.assertEqual([query['gl'] for query in queries], [['us'], ['us']])
        self.assertEqual([query['id'] for query in queries], [['org.example.app'], ['org.example.app']])

    def test_normalizes_missing_version_and_date(self):
        result = metadata.normalize_locale({'title': ' Name ', 'developer': ' Dev ', 'description': ' Long ', 'summary': ' Short ', 'version': None, 'updated': 0, 'recentChanges': None}, 'com.example.app')
        self.assertEqual(result['title'], 'Name')
        self.assertIsNone(result['versionName'])
        self.assertIsNone(result['updatedDate'])
        self.assertIsNone(result['changelog'])
        self.assertEqual(result['playUrl'], 'https://play.google.com/store/apps/details?id=com.example.app')

    def test_rejects_untrusted_image_and_redirect_hosts(self):
        for url in ('http://lh3.googleusercontent.com/x', 'https://googleusercontent.com.evil.test/x', 'https://user@lh3.googleusercontent.com/x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                metadata.validate_image_url(url)
        handler = metadata.SafeRedirectHandler()
        with self.assertRaises(ValueError):
            handler.redirect_request(None, None, 302, '', {}, 'https://evil.test/image')

    def test_image_cache_reuses_existing_content_addressed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            url = 'https://lh3.googleusercontent.com/test'
            with patch.object(metadata, 'download_image', return_value=(b'image', 'image/png')) as download:
                first = metadata.cache_image(url, root, {})
                second = metadata.cache_image(url, root, {url: first})
            self.assertEqual(first, second)
            self.assertEqual(download.call_count, 1)
            self.assertTrue((root / first).exists())

    def test_history_retains_previous_text_when_version_missing(self):
        old = [{'versionName': None, 'updatedDate': '2024-01-01', 'text': 'old'}]
        self.assertEqual(metadata.update_history(old, {'versionName': None, 'updatedDate': '2024-01-01', 'changelog': 'old'}), old)
        result = metadata.update_history(old, {'versionName': None, 'updatedDate': '2024-01-01', 'changelog': 'new'})
        self.assertEqual([x['text'] for x in result], ['old', 'new'])
        self.assertEqual(metadata.update_history(result, {'versionName': None, 'updatedDate': None, 'changelog': None}), result)

    def test_failure_preserves_existing_card_and_continues(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'apps.json'
            config.write_text(json.dumps({'apps': [{'package': 'com.example.bad'}, {'package': 'com.example.good'}]}), encoding='utf-8')
            output = root / 'library'
            output.mkdir()
            old_card = {'package': 'com.example.bad', 'metadataPath': 'apps/com.example.bad/metadata.json', 'title': 'Existing'}
            (output / 'catalog.json').write_text(json.dumps({'apps': [old_card]}), encoding='utf-8')
            def fetch(package, locale):
                if package.endswith('bad'):
                    raise RuntimeError('unavailable')
                return {'title': 'Good', 'developer': 'Dev', 'description': 'Description', 'summary': 'Summary'}
            with patch.object(metadata, 'fetch_app', side_effect=fetch):
                result = metadata.refresh_catalog(config, output)
            self.assertEqual(result['failures'][0]['package'], 'com.example.bad')
            cards = json.loads((output / 'catalog.json').read_text(encoding='utf-8'))['apps']
            self.assertEqual(cards[0], old_card)
            self.assertEqual(cards[1]['package'], 'com.example.good')


if __name__ == '__main__':
    unittest.main()

class PlayPageTests(unittest.TestCase):
    def test_extracts_changelog_and_other_fields(self):
        data = [None] * 146
        data[0] = ['Example']
        data[68] = ['Developer']
        data[72] = [[None, 'Description &amp; details']]
        data[73] = [[None, 'Summary']]
        data[140] = [[['1.2']]]
        data[145] = [[None, [1704067200]]]
        data[144] = [None, [None, 'Changes &amp; fixes']]
        data[95] = [[None, None, None, [None, None, 'https://lh3.googleusercontent.com/icon']]]
        data[78] = [[ [None, None, None, [None, None, 'https://lh3.googleusercontent.com/screen']] ]]
        payload = [None, [None, None, data]]
        html = '<script>AF_initDataCallback(' + json.dumps({'key': 'ds:5', 'data': payload}) + ');</script>'
        parsed = metadata.parse_play_page(html)
        self.assertEqual(parsed['recentChanges'], 'Changes & fixes')
        self.assertEqual(parsed['description'], 'Description & details')
        self.assertEqual(parsed['screenshots'], ['https://lh3.googleusercontent.com/screen'])
        self.assertEqual(parsed['version'], '1.2')

    def test_rejects_missing_or_malformed_critical_data(self):
        for html in ('<html></html>', 'AF_initDataCallback({key: "ds:5", data: [broken]});', 'AF_initDataCallback({"key":"ds:5","data":[]});'):
            with self.subTest(html=html), self.assertRaises(ValueError):
                metadata.parse_play_page(html)

    def test_real_play_fixture_contains_changelog(self):
        fixture = Path(__file__).parent / 'fixtures' / 'metadata' / 'firefox-play.html'
        result = metadata.parse_play_page(fixture.read_text(encoding='utf-8'))
        self.assertEqual(result['developer'], 'Mozilla')
        self.assertIn('Fixed', result['recentChanges'])
        self.assertTrue(result['icon'].startswith('https://'))
        self.assertTrue(result['screenshots'])

    def test_real_sparse_play_fixture_contains_version_and_changelog(self):
        fixture = Path(__file__).parent / 'fixtures' / 'metadata' / 'planfix-play.html'
        result = metadata.parse_play_page(fixture.read_text(encoding='utf-8'))
        self.assertEqual(result['developer'], 'Planfix Inc.')
        self.assertIn('Minor bug fixes', result['recentChanges'])
        self.assertEqual(result['version'], '0.74.2')
        self.assertEqual(result['updated'], 1792357153)
