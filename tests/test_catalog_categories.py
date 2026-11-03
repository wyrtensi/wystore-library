import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from wystore_library.metadata import refresh_catalog

class CatalogCategoriesTests(unittest.TestCase):
    def test_app_category_is_exported_separately_from_shelf_membership(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = root / 'apps.json'
            cfg.write_text(json.dumps({'apps':[{'package':'com.example.browser','category':'Browsers','foreign_category':False}]}))
            with patch('wystore_library.metadata.fetch_app', return_value={'title':'Browser','developer':'Developer'}):
                refresh_catalog(cfg, root/'library')
            card = json.loads((root/'library/catalog.json').read_text())['apps'][0]
            self.assertEqual(card.get('categories'), ['browsers'])
            self.assertFalse(card['foreign_category'])

    def test_editorial_category_changes_even_when_play_metadata_is_unavailable(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = root/'apps.json'
            cfg.write_text(json.dumps({'apps':[{'package':'com.example.browser','category':'Browsers'}]}))
            out = root/'library'; out.mkdir()
            old = {'package':'com.example.browser','title':'Saved','categories':['tools']}
            (out/'catalog.json').write_text(json.dumps({'schema':1,'apps':[old]}))
            with patch('wystore_library.metadata.fetch_app', side_effect=RuntimeError('offline')):
                refresh_catalog(cfg,out)
            card = json.loads((out/'catalog.json').read_text())['apps'][0]
            self.assertEqual(card['categories'], ['browsers'])
            self.assertEqual(card['title'], 'Saved')

    def test_removing_a_category_also_clears_cached_offline_cards(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg=root/'apps.json';cfg.write_text(json.dumps({'apps':[{'package':'com.example.browser'}]}))
            out=root/'library';out.mkdir()
            (out/'catalog.json').write_text(json.dumps({'schema':1,'apps':[{'package':'com.example.browser','categories':['browsers']}]}))
            with patch('wystore_library.metadata.fetch_app', side_effect=RuntimeError('offline')):
                refresh_catalog(cfg,out)
            card=json.loads((out/'catalog.json').read_text())['apps'][0]
            self.assertNotIn('categories',card)
