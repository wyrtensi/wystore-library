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
