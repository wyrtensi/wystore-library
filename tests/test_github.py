import unittest
from unittest.mock import patch
from subprocess import CompletedProcess
from wystore_library.github import Publisher

class GitHubTests(unittest.TestCase):
    @patch('wystore_library.github.subprocess.run')
    def test_command_failure_does_not_expose_output(self, run):
        run.return_value = CompletedProcess([], 1, '', 'secret token')
        with self.assertRaises(RuntimeError) as error: Publisher('owner/repo')._gh('release', 'view', 'x')
        self.assertNotIn('secret', str(error.exception))
    def test_release_assets_require_exact_digest_and_complete_state(self):
        expected = {'base.apk': {'sha256': 'a'*64, 'size': 3}}
        good = {'draft': False, 'assets': [{'name': 'base.apk', 'digest': 'sha256:' + 'a'*64, 'size': 3, 'state': 'uploaded'}]}
        Publisher._check_assets(good, expected, False)
        good['assets'][0]['digest'] = 'sha256:' + 'b'*64
        with self.assertRaises(RuntimeError): Publisher._check_assets(good, expected, False)
    def test_draft_never_counts_as_published(self):
        with self.assertRaises(RuntimeError):
            Publisher._check_assets({'draft': True, 'assets': []}, {}, False)
    def test_index_update_uses_existing_sha_and_identity(self):
        import base64, json, tempfile
        from pathlib import Path
        publisher = Publisher('owner/repo')
        publisher._gh = unittest.mock.Mock(side_effect=[json.dumps({'sha':'oldsha','encoding':'base64','content':base64.b64encode(b'{"schema":1,"entries":[]}').decode()}), '{}'])
        publisher.read_index()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'index.json'; path.write_text('{"schema":1,"entries":[]}', encoding='utf-8')
            publisher.publish_index(path)
        args, kwargs = publisher._gh.call_args
        self.assertEqual(args[:3], ('api', '--method', 'PUT'))
        body = json.loads(kwargs['input_data'])
        self.assertEqual(body['sha'], 'oldsha')
        self.assertEqual(body['author']['email'], 'wyrtensi@gmail.com')
        self.assertEqual(body['committer']['email'], 'wyrtensi@gmail.com')
    def test_draft_reuses_valid_assets_and_uploads_only_missing(self):
        from unittest.mock import Mock
        from pathlib import Path
        publisher = Publisher('owner/repo')
        base = {'name':'base.apk','digest':'sha256:'+'a'*64,'size':3,'state':'uploaded','browser_download_url':'base-url'}
        manifest = {'name':'manifest-public.json','digest':'sha256:'+'b'*64,'size':4,'state':'uploaded','browser_download_url':'manifest-url'}
        publisher.release = Mock(side_effect=[{'draft':True,'assets':[base]}, {'draft':True,'assets':[base,manifest]}, {'draft':False,'assets':[base,manifest]}])
        publisher._gh = Mock(return_value='')
        expected = {'base.apk':{'sha256':'a'*64,'size':3},'manifest-public.json':{'sha256':'b'*64,'size':4}}
        publisher.publish_release('tag', [Path('base.apk'), Path('manifest-public.json')], expected)
        uploads = [c.args for c in publisher._gh.call_args_list if c.args[:2] == ('release', 'upload')]
        self.assertEqual(uploads, [('release','upload','tag','manifest-public.json','--repo','owner/repo')])
    def test_draft_conflicting_assets_rejected_before_upload(self):
        from unittest.mock import Mock
        from pathlib import Path
        publisher = Publisher('owner/repo')
        publisher.release = Mock(return_value={'draft':True,'assets':[{'name':'base.apk','digest':'sha256:'+'b'*64,'size':3,'state':'uploaded'}]})
        publisher._gh = Mock()
        with self.assertRaises(RuntimeError): publisher.publish_release('tag',[Path('base.apk')],{'base.apk':{'sha256':'a'*64,'size':3}})
        publisher._gh.assert_not_called()
    def test_initial_index_creation_has_no_sha(self):
        import json, tempfile
        from pathlib import Path
        from unittest.mock import Mock
        publisher = Publisher('owner/repo'); publisher._gh = Mock(side_effect=[None, '{}'])
        self.assertEqual(publisher.read_index(), {'schema':1,'entries':[]})
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'index.json'; path.write_text('{}')
            publisher.publish_index(path)
        self.assertNotIn('sha', json.loads(publisher._gh.call_args.kwargs['input_data']))
    def test_index_conflict_does_not_retry_or_erase_old_sha(self):
        import json, tempfile
        from pathlib import Path
        from unittest.mock import Mock
        publisher = Publisher('owner/repo'); publisher.index_read = True; publisher.index_sha = 'old'
        publisher._gh = Mock(side_effect=RuntimeError('GitHub operation failed'))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'index.json'; path.write_text('{}')
            with self.assertRaises(RuntimeError): publisher.publish_index(path)
        self.assertEqual(publisher.index_sha, 'old'); publisher._gh.assert_called_once()

class ReleaseCleanupTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import Mock
        self.publisher = Publisher('owner/repo')
        self.entry = {'package': 'org.example.app', 'profile': 'px_9a', 'version_code': 10,
                      'assets': [{'name': 'base.apk', 'size': 3, 'sha256': 'a' * 64, 'url': 'https://example.test/base'}],
                      'manifest_url': 'https://example.test/manifest', 'manifest_size': 4, 'manifest_sha256': 'b' * 64}
        self.keeper = {'tag_name': 'org.example.app-px_9a-10', 'draft': False, 'assets': [
            {'name': 'base.apk', 'size': 3, 'digest': 'sha256:' + 'a' * 64, 'state': 'uploaded', 'browser_download_url': 'https://example.test/base'},
            {'name': 'manifest-public.json', 'size': 4, 'digest': 'sha256:' + 'b' * 64, 'state': 'uploaded', 'browser_download_url': 'https://example.test/manifest'}]}
        self.publisher.release = Mock(return_value=self.keeper)

    def test_prune_paginates_and_only_deletes_older_managed_versions(self):
        import json
        from unittest.mock import Mock
        pages = [[{'tag_name': 'org.example.app-px_9a-9'}, {'tag_name': 'org.example.app-px_9a-10'}, {'tag_name': 'org.example.app-px_9a-11'}],
                 [{'tag_name': 'org.example.app-px_9a-1', 'draft': True}, {'tag_name': 'org.example.app-px_9a-0'}, {'tag_name': 'manual-1'}, {'tag_name': 'other.app-px_9a-2'}, {'tag_name': 'org.example.app-px_9a-09'}]]
        self.publisher._gh = Mock(return_value=json.dumps(pages))
        self.publisher.prune_releases([self.entry])
        self.publisher._gh.assert_any_call('api', 'repos/owner/repo/releases', '--paginate', '--slurp')
        deletes = [c.args for c in self.publisher._gh.call_args_list if c.args[:2] == ('release', 'delete')]
        self.assertEqual(deletes, [('release', 'delete', 'org.example.app-px_9a-9', '--yes', '--cleanup-tag', '--repo', 'owner/repo'), ('release', 'delete', 'org.example.app-px_9a-1', '--yes', '--cleanup-tag', '--repo', 'owner/repo')])

    def test_all_keepers_are_verified_before_any_delete(self):
        from unittest.mock import Mock
        second = {**self.entry, 'package': 'org.example.other'}
        self.publisher.release = Mock(side_effect=[self.keeper, {'draft': False, 'assets': []}])
        self.publisher._gh = Mock()
        with self.assertRaises((ValueError, RuntimeError)): self.publisher.prune_releases([self.entry, second])
        self.publisher._gh.assert_not_called()

    def test_bad_index_or_keeper_never_deletes(self):
        import copy
        from unittest.mock import Mock
        for case in ('missing_manifest', 'bad_sha', 'bad_size', 'duplicate_name', 'wrong_url', 'draft', 'wrong_digest', 'missing_asset'):
            with self.subTest(case=case):
                entry, keeper = copy.deepcopy(self.entry), copy.deepcopy(self.keeper)
                if case == 'missing_manifest': del entry['manifest_sha256']
                if case == 'bad_sha': entry['assets'][0]['sha256'] = 'x' * 64
                if case == 'bad_size': entry['manifest_size'] = True
                if case == 'duplicate_name': entry['assets'].append(copy.deepcopy(entry['assets'][0]))
                if case == 'wrong_url': keeper['assets'][0]['browser_download_url'] = 'https://example.test/wrong'
                if case == 'draft': keeper['draft'] = True
                if case == 'wrong_digest': keeper['assets'][0]['digest'] = 'sha256:' + 'c' * 64
                if case == 'missing_asset': keeper['assets'].pop()
                self.publisher.release = Mock(return_value=keeper)
                self.publisher._gh = Mock()
                with self.assertRaises((ValueError, RuntimeError)): self.publisher.prune_releases([entry])
                self.publisher._gh.assert_not_called()

    def test_partial_failure_is_reported_and_next_run_deletes_remaining(self):
        import json
        from unittest.mock import Mock
        remaining = ['org.example.app-px_9a-2', 'org.example.app-px_9a-3']
        fail = [True]
        def gh(*args, **kwargs):
            if args[0] == 'api': return json.dumps([[{'tag_name': t} for t in remaining]])
            if args[2].endswith('-3') and fail[0]:
                fail[0] = False
                raise RuntimeError('delete failed')
            remaining.remove(args[2])
            return ''
        self.publisher._gh = Mock(side_effect=gh)
        with self.assertRaises(RuntimeError): self.publisher.prune_releases([self.entry])
        self.assertEqual(remaining, ['org.example.app-px_9a-3'])
        self.publisher.prune_releases([self.entry])
        self.assertEqual(remaining, [])

    def test_new_draft_uses_requested_metadata(self):
        from unittest.mock import Mock
        self.publisher.release = Mock(side_effect=[None, {'draft': True, 'assets': []}, {'draft': False, 'assets': []}])
        self.publisher._gh = Mock(return_value='')
        self.publisher.publish_release('tag', [], {}, title='Friendly', notes='Details')
        self.publisher._gh.assert_any_call('release', 'create', 'tag', '--repo', 'owner/repo', '--draft', '--title', 'Friendly', '--notes', 'Details')

    def test_public_release_is_never_uploaded_over(self):
        from unittest.mock import Mock
        self.publisher.release = Mock(return_value=self.keeper)
        self.publisher._gh = Mock()
        expected = {'base.apk': {'size': 3, 'sha256': 'a' * 64}, 'manifest-public.json': {'size': 4, 'sha256': 'b' * 64}}
        self.publisher.publish_release('org.example.app-px_9a-10', [], expected)
        self.publisher._gh.assert_not_called()

    def test_bad_pagination_response_never_deletes(self):
        import json
        from unittest.mock import Mock
        self.publisher._gh = Mock(return_value=json.dumps([[{'tag_name': 'org.example.app-px_9a-2'}], [{'invalid': True}]]))
        with self.assertRaises(ValueError): self.publisher.prune_releases([self.entry])
        self.assertFalse(any(c.args[:2] == ('release', 'delete') for c in self.publisher._gh.call_args_list))

class ReleaseLookupTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import Mock
        self.publisher = Publisher('owner/repo')
        self.publisher._gh = Mock()
        self.tag = 'org.example.app-px_9a-10'

    def test_404_finds_exact_draft_on_later_page(self):
        import json
        draft = {'tag_name': self.tag, 'draft': True, 'assets': []}
        self.publisher._gh.side_effect = [None, json.dumps([[{'tag_name': self.tag + '-other'}], [draft]])]
        self.assertEqual(self.publisher.release(self.tag), draft)
        self.assertEqual(self.publisher._gh.call_args_list[1].args, ('api', 'repos/owner/repo/releases', '--paginate', '--slurp'))

    def test_public_release_lookup_does_not_list(self):
        import json
        release = {'tag_name': self.tag, 'draft': False}
        self.publisher._gh.return_value = json.dumps(release)
        self.assertEqual(self.publisher.release(self.tag), release)
        self.publisher._gh.assert_called_once()

    def test_404_without_matching_release_returns_none(self):
        import json
        self.publisher._gh.side_effect = [None, json.dumps([[{'tag_name': 'different'}], []])]
        self.assertIsNone(self.publisher.release(self.tag))
        self.assertEqual(self.publisher._gh.call_count, 2)

    def test_ambiguous_or_malformed_listing_never_creates_release(self):
        import json
        for pages in ([[{'tag_name': self.tag}], [{'tag_name': self.tag}]], [[{'tag_name': ''}]], [[{'tag_name': None}]], [None], {'tag_name': self.tag}):
            with self.subTest(pages=pages):
                self.publisher._gh.reset_mock()
                self.publisher._gh.side_effect = [None, json.dumps(pages)]
                with self.assertRaises((ValueError, RuntimeError)): self.publisher.publish_release(self.tag, [], {})
                self.assertFalse(any(c.args[:2] == ('release', 'create') for c in self.publisher._gh.call_args_list))

    def test_existing_draft_is_resumed_and_reloaded_after_upload(self):
        import json
        draft = {'tag_name': self.tag, 'draft': True, 'assets': []}
        asset = {'name': 'base.apk', 'size': 3, 'digest': 'sha256:' + 'a' * 64, 'state': 'uploaded', 'browser_download_url': 'https://example.test/base'}
        uploaded = {**draft, 'assets': [asset]}
        published = {**uploaded, 'draft': False}
        self.publisher._gh.side_effect = [None, json.dumps([[draft]]), '', None, json.dumps([[uploaded]]), '', json.dumps(published)]
        result = self.publisher.publish_release(self.tag, ['base.apk'], {'base.apk': {'size': 3, 'sha256': 'a' * 64}})
        self.assertEqual(result, {'base.apk': 'https://example.test/base'})
        self.assertFalse(any(c.args[:2] == ('release', 'create') for c in self.publisher._gh.call_args_list))
        self.publisher._gh.assert_any_call('release', 'upload', self.tag, 'base.apk', '--repo', 'owner/repo')
