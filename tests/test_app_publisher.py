import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from wystore_library.app_publisher import AppPublisher

PACKAGE = 'org.example.app'
TAG = PACKAGE + '-library'
DATA = b'abc'
SHA = hashlib.sha256(DATA).hexdigest()
NAME = SHA + '.apk'
URL = f'https://github.com/owner/repo/releases/download/{TAG}/{NAME}'


def asset(name=NAME, sha=SHA, size=3, number=1):
    return {'id': number, 'name': name, 'size': size, 'digest': 'sha256:' + sha,
            'state': 'uploaded', 'browser_download_url': f'https://github.com/owner/repo/releases/download/{TAG}/{name}'}


def release(assets):
    return {'id': 10, 'tag_name': TAG, 'draft': False, 'html_url': f'https://github.com/owner/repo/releases/tag/{TAG}', 'assets': assets}


def application():
    catalog_sha = 'b' * 64
    manifest_sha = 'c' * 64
    def descriptor(prefix, sha):
        name = prefix + '-' + sha + '.json'
        return {'name': name, 'sha256': sha, 'size': 4, 'url': f'https://github.com/owner/repo/releases/download/{TAG}/{name}'}
    return {'package': PACKAGE, 'name': 'Example', 'variants': [{'id': 'phone', 'version_code': 1, 'version_name': '1', 'compatibility': {'min_sdk': 26, 'abis': ['arm64-v8a'], 'density': 420, 'languages': ['en']}, 'files': [{'artifact': SHA, 'original_name': 'base.apk', 'role': 'base', 'split': None}]}],
            'artifacts': [{'name': NAME, 'sha256': SHA, 'size': 3, 'url': URL}],
            'publication': {'tag': TAG, 'release_url': f'https://github.com/owner/repo/releases/tag/{TAG}', 'catalog': descriptor('catalog', catalog_sha), 'compat_manifest': descriptor('manifest', manifest_sha)}}


def keeper(app):
    descriptors = app['artifacts'] + [app['publication']['catalog'], app['publication']['compat_manifest']]
    return release([asset(x['name'], x['sha256'], x['size'], i + 1) for i, x in enumerate(descriptors)])


class AppPublisherTests(unittest.TestCase):
    def setUp(self):
        self.pub = AppPublisher('owner/repo')
        self.pub._gh = Mock()
        self.pub.release = Mock()

    def test_reuses_expected_asset_and_tolerates_old_managed_asset(self):
        self.pub.release.return_value = release([asset(), asset('d' * 64 + '.apk', 'd' * 64, 5, 2)])
        result = self.pub.publish_application(PACKAGE, [], {NAME: {'sha256': SHA, 'size': 3}}, title='Name', notes='Notes')
        self.assertEqual(result, {NAME: URL})
        self.pub._gh.assert_not_called()

    def test_rejects_unknown_or_corrupt_existing_assets_before_upload(self):
        for broken in ({**asset(), 'digest': None}, {**asset(), 'digest': 'sha256:' + 'e' * 64}, {**asset(), 'browser_download_url': 'https://evil.test/a'}, {**asset(), 'name': 'manual.apk'}):
            with self.subTest(broken=broken):
                self.pub.release.return_value = release([broken])
                with self.assertRaises((ValueError, RuntimeError)):
                    self.pub.publish_application(PACKAGE, [], {NAME: {'sha256': SHA, 'size': 3}}, title='Name', notes='Notes')
                self.pub._gh.assert_not_called()

    def test_all_keepers_preflight_before_mutation(self):
        app = application()
        other = copy.deepcopy(app)
        other['package'] = 'org.example.other'
        other['publication']['tag'] = 'org.example.other-library'
        self.pub.release.side_effect = [keeper(app), None]
        with self.assertRaises((ValueError, RuntimeError)):
            self.pub.cleanup_applications([app, other], ['px_9a'])
        self.pub._gh.assert_not_called()

    def test_uploads_only_missing_then_verifies_without_changing_public_presentation(self):
        self.pub.release.return_value = release([])
        self.pub._gh.side_effect = ['{}', json.dumps(release([asset()]))]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / NAME
            path.write_bytes(DATA)
            result = self.pub.publish_application(PACKAGE, [path], {NAME: {'sha256': SHA, 'size': 3}}, title='Name', notes='Notes')
        self.assertEqual(result, {NAME: URL})
        self.assertEqual(self.pub._gh.call_args_list[0].args[3], f'https://uploads.github.com/repos/owner/repo/releases/10/assets?name={NAME}')
        self.assertEqual(len(self.pub._gh.call_args_list), 2)

    def test_draft_is_published_only_after_uploaded_assets_are_verified(self):
        draft = {**release([]), 'draft': True}
        completed = {**release([asset()]), 'draft': True}
        self.pub.release.return_value = None
        self.pub._gh.side_effect = [json.dumps(draft), '{}', json.dumps(completed), json.dumps(release([asset()]))]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / NAME
            path.write_bytes(DATA)
            self.assertEqual(self.pub.publish_application(PACKAGE, [path], {NAME: {'sha256': SHA, 'size': 3}}, title='Name', notes='Notes'), {NAME: URL})
        self.assertEqual(self.pub._gh.call_args_list[-1].args[:3], ('api', '--method', 'PATCH'))
        self.assertEqual(json.loads(self.pub._gh.call_args_list[-1].kwargs['input_data']), {'draft': False})

    def test_cleanup_removes_only_unreferenced_assets_and_exact_legacy_tags_across_pages(self):
        app = application()
        old = asset('d' * 64 + '.apk', 'd' * 64, 5, 99)
        self.pub.release.return_value = keeper(app)
        self.pub.release.return_value['assets'].append(old)
        pages = [[{'tag_name': PACKAGE + '-px_9a-3'}, {'tag_name': PACKAGE + '-px_9a-0'}], [{'tag_name': PACKAGE + '-px_9a-4'}, {'tag_name': PACKAGE + '-other-5'}, {'tag_name': 'manual'}]]
        self.pub._gh.side_effect = [json.dumps(pages), '{}', '', '', '']
        self.pub.cleanup_applications([app], ['px_9a'])
        calls = [call.args for call in self.pub._gh.call_args_list]
        self.assertIn(('api', '--method', 'DELETE', 'repos/owner/repo/releases/assets/99'), calls)
        self.assertEqual([args[2] for args in calls if args[:2] == ('release', 'delete')], [PACKAGE + '-px_9a-3', PACKAGE + '-px_9a-4'])
        body = json.loads(self.pub._gh.call_args_list[1].kwargs['input_data'])['body']
        self.assertIn('ONE compatible variant', body)
        self.assertIn('arm64-v8a', body)
        self.assertIn(NAME, body)

    def test_cleanup_rejects_bad_url_missing_digest_and_unknown_asset_before_mutations(self):
        app = application()
        for broken in ({**asset(), 'digest': None}, {**asset(), 'browser_download_url': 'https://evil.test/file'}, {**asset(), 'name': 'manual.apk'}):
            with self.subTest(broken=broken):
                actual = keeper(app)
                actual['assets'][0] = broken
                self.pub.release.return_value = actual
                with self.assertRaises((ValueError, RuntimeError)):
                    self.pub.cleanup_applications([app], ['px_9a'])
                self.pub._gh.assert_not_called()

    def test_cleanup_failure_can_retry_with_remaining_assets(self):
        app = application()
        state = keeper(app)
        state['assets'].extend([asset('d' * 64 + '.apk', 'd' * 64, 5, 99), asset('e' * 64 + '.apk', 'e' * 64, 5, 100)])
        self.pub.release.side_effect = lambda tag: copy.deepcopy(state)
        fail = [True]
        def gh(*args, **kwargs):
            if args == ('api', 'repos/owner/repo/releases', '--paginate', '--slurp'):
                return '[]'
            if args[:3] == ('api', '--method', 'DELETE'):
                number = int(args[3].split('/')[-1])
                if number == 100 and fail[0]:
                    fail[0] = False
                    raise RuntimeError('delete failed')
                state['assets'] = [a for a in state['assets'] if a['id'] != number]
            return '{}'
        self.pub._gh.side_effect = gh
        with self.assertRaises(RuntimeError):
            self.pub.cleanup_applications([app], [])
        self.assertIn(100, [a['id'] for a in state['assets']])
        self.pub.cleanup_applications([app], [])
        self.assertEqual({a['id'] for a in state['assets']}, {1, 2, 3})

    def test_cleanup_rejects_variant_reference_absent_from_artifacts(self):
        app = application()
        app['variants'][0]['files'][0]['artifact'] = 'f' * 64
        self.pub.release.return_value = keeper(app)
        with self.assertRaises((ValueError, RuntimeError)):
            self.pub.cleanup_applications([app], [])
        self.pub._gh.assert_not_called()

    def test_rejects_expected_existing_size_mismatch(self):
        self.pub.release.return_value = release([asset(size=5)])
        with self.assertRaises(RuntimeError):
            self.pub.publish_application(PACKAGE, [], {NAME: {'sha256': SHA, 'size': 3}}, title='Name', notes='Notes')
        self.pub._gh.assert_not_called()

    def test_failed_post_upload_verification_keeps_draft_unpublished(self):
        draft = {**release([]), 'draft': True}
        invalid = {**release([{**asset(), 'digest': None}]), 'draft': True}
        self.pub.release.return_value = None
        self.pub._gh.side_effect = [json.dumps(draft), '{}', json.dumps(invalid)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / NAME
            path.write_bytes(DATA)
            with self.assertRaises(RuntimeError):
                self.pub.publish_application(PACKAGE, [path], {NAME: {'sha256': SHA, 'size': 3}}, title='Name', notes='Notes')
        self.assertFalse(any(call.args[:3] == ('api', '--method', 'PATCH') for call in self.pub._gh.call_args_list))

    def test_cleanup_preserves_legacy_tags_for_unconfigured_canonical_applications(self):
        app = application()
        self.pub.release.return_value = keeper(app)
        self.pub._gh.side_effect = [json.dumps([[{'tag_name': PACKAGE + '-px_9a-3'}]]), '{}']
        self.pub.cleanup_applications([app], ['px_9a'], configured_packages=[])
        self.assertFalse(any(call.args[:2] == ('release', 'delete') for call in self.pub._gh.call_args_list))

    def test_cleanup_does_not_mutate_unconfigured_release(self):
        app = application()
        state = keeper(app)
        state['assets'].append(asset('d' * 64 + '.apk', 'd' * 64, 5, 99))
        self.pub.release.return_value = state
        self.pub._gh.side_effect = [json.dumps([[{'tag_name': PACKAGE + '-px_9a-3'}]])]
        self.pub.cleanup_applications([app], ['px_9a'], configured_packages=[])
        self.assertFalse(any(call.args[:3] in [('api', '--method', 'PATCH'), ('api', '--method', 'DELETE')] for call in self.pub._gh.call_args_list))

    def test_draft_untagged_url_is_accepted_only_until_publication(self):
        draft = {**release([]), 'draft': True}
        draft_asset = {**asset(), 'browser_download_url': f'https://github.com/owner/repo/releases/download/untagged-a485f209157fb834415d/{NAME}'}
        completed = {**release([draft_asset]), 'draft': True}
        self.pub.release.return_value = None
        self.pub._gh.side_effect = [json.dumps(draft), '{}', json.dumps(completed), json.dumps(release([asset()]))]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / NAME
            path.write_bytes(DATA)
            result = self.pub.publish_application(PACKAGE, [path], {NAME: {'sha256': SHA, 'size': 3}}, title='Name', notes='Notes')
        self.assertEqual(result, {NAME: URL})

    def test_draft_rejects_wrong_temporary_url_and_public_release_rejects_untagged(self):
        wrong = f'https://github.com/other/repo/releases/download/untagged-a485f209157fb834415d/{NAME}'
        temporary = f'https://github.com/owner/repo/releases/download/untagged-a485f209157fb834415d/{NAME}'
        for draft, url in ((True, wrong), (False, temporary), (True, temporary.replace('untagged-a485', 'untagged-XYZ'))):
            with self.subTest(draft=draft, url=url):
                self.pub.release.return_value = {**release([{**asset(), 'browser_download_url': url}]), 'draft': draft}
                with self.assertRaises((ValueError, RuntimeError)):
                    self.pub.publish_application(PACKAGE, [], {NAME: {'sha256': SHA, 'size': 3}}, title='Name', notes='Notes')
                self.pub._gh.assert_not_called()

    def test_cleanup_avoids_unchanged_release_writes(self):
        app = application()
        state = keeper(app)
        state.update(name=app['name'], body=self.pub._presentation(app, {SHA}))
        self.pub.release.return_value = state
        self.pub._gh.side_effect = ['[]']
        self.pub.cleanup_applications([app], ['px_9a'])
        self.assertEqual(len(self.pub._gh.call_args_list), 1)
