import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from wystore_library.sync_batches import plan_batches


class SyncBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / 'apps.json'
        self.packages = [f'org.example.app{i}' for i in range(19)]
        self.config.write_text(json.dumps({'schema': 1, 'apps': [
            {'package': package, 'profiles': ['px_9a']} for package in self.packages
        ]}), encoding='utf-8')

    def test_each_package_is_in_one_bounded_batch(self):
        batches = plan_batches(self.config)['include']
        self.assertEqual(len(batches), 8)
        actual = [package for batch in batches for package in batch['packages'].split(',')]
        self.assertCountEqual(actual, self.packages)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertLessEqual(max(len(batch['packages'].split(',')) for batch in batches), 3)

    def test_subset_uses_no_empty_jobs_and_rejects_unknown_or_duplicate_packages(self):
        self.assertEqual(plan_batches(self.config, 'org.example.app2, org.example.app0'), {
            'include': [{'batch': 0, 'packages': 'org.example.app0'}, {'batch': 1, 'packages': 'org.example.app2'}]
        })
        for selected in ['org.unknown.app', 'org.example.app0,org.example.app0', ',']:
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                plan_batches(self.config, selected)
