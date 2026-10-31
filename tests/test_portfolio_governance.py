import base64
import json
import http.client
import socket
import subprocess
import urllib.error
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import portfolio_governance as pg

PRIVATE_MARKERS = ('private-repo', 'confidential-description', 'example.test/private', '2031-01-02T03:04:05Z')


def repo(name, private, archived=False, **extra):
    data = {'name': name, 'html_url': f'https://example.test/{name}', 'private': private,
            'archived': archived, 'owner': {'login': pg.OWNER}, 'pushed_at': f'2030-01-01T00:00:00Z-{name}'}
    data.update(extra)
    return data


PUBLIC = repo('public-repo', False)
PRIVATE = repo('private-repo', True, description='confidential-description',
               html_url='https://example.test/private', pushed_at='2031-01-02T03:04:05Z')


def written_body(write):
    return json.loads(write.call_args.kwargs['input'])['body']


def catalog_response(payload):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = payload
    return response


def encoded_catalog(raw):
    return json.dumps({'encoding': 'base64', 'content': base64.b64encode(raw).decode('ascii')}).encode()


class InventoryTests(unittest.TestCase):
    def setUp(self):
        # Hermetic: the scheduled workflow runs these tests with real tokens in the
        # environment. Strip them and refuse any unmocked HTTP or subprocess call.
        env = patch.dict(pg.os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        for key in ('GH_TOKEN', 'GITHUB_TOKEN', 'PORTFOLIO_READ_TOKEN'):
            pg.os.environ.pop(key, None)
        for target, name in ((pg.subprocess, 'run'), (pg.urllib.request, 'urlopen')):
            guard = patch.object(target, name, side_effect=AssertionError('unmocked external call'))
            guard.start()
            self.addCleanup(guard.stop)

    def test_public_report_excludes_private_and_unknown_visibility(self):
        public = {'name': 'public-repo', 'html_url': 'https://example.test/public', 'private': False}
        private = {'name': 'private-repo', 'html_url': 'https://example.test/private', 'private': True,
                   'description': 'confidential-description'}
        unknown = {'name': 'unknown-repo', 'html_url': 'https://example.test/unknown'}
        report = pg.render([public, private, unknown])
        self.assertIn('public-repo', report)
        self.assertIn('Total visível: 1;', report)
        for forbidden in ('private-repo', 'confidential-description', 'example.test/private',
                          'unknown-repo', 'example.test/unknown'):
            self.assertNotIn(forbidden, report)

    def test_non_boolean_or_conflicting_visibility_is_never_published(self):
        hidden = [repo('hidden-str-false', 'false'), repo('hidden-zero', 0), repo('hidden-null', None),
                  repo('hidden-internal-flag', False, visibility='internal'),
                  repo('hidden-private-flag', False, visibility='private'), PRIVATE]
        archived = repo('archived-public', False, archived=True, visibility='public')
        report = pg.render([PUBLIC, archived, *hidden])
        self.assertIn('Total visível: 2; não arquivados: 1; arquivados: 1.', report)
        self.assertIn('[public-repo](https://example.test/public-repo) | Ativo', report)
        self.assertIn('[archived-public](https://example.test/archived-public) | Arquivado', report)
        self.assertIn('2030-01-01T00:00:00Z-archived-public', report)
        for item in hidden:
            self.assertNotIn(str(item['name']), report)
            self.assertNotIn(item['pushed_at'], report)
        for forbidden in PRIVATE_MARKERS:
            self.assertNotIn(forbidden, report)

    def test_private_metadata_absent_from_error_and_auxiliary_sections(self):
        report = pg.render([PRIVATE], {'state': 'UNVERIFIED', 'issues': ['Não foi possível: OSError']},
                           {'status': 'UNVERIFIED'})
        self.assertIn('Total visível: 0; não arquivados: 0; arquivados: 0.', report)
        for forbidden in PRIVATE_MARKERS:
            self.assertNotIn(forbidden, report)

    def test_token_inventory_publishes_only_public_metadata(self):
        repos = [
            {'name': 'public-repo', 'html_url': 'https://example.test/public', 'private': False},
            {'name': 'private-repo', 'html_url': 'https://example.test/private', 'private': True},
        ]
        with patch.dict(pg.os.environ, {'PORTFOLIO_READ_TOKEN': 'synthetic-read'}), \
             patch.object(pg, 'inventory', return_value=repos), \
             patch.object(pg, 'gh', return_value=[]) as get, \
             patch.object(pg, 'public_catalog', return_value={}), \
             patch.object(pg, 'audit', return_value={'state': 'UNVERIFIED', 'issues': []}), \
             patch.object(pg.subprocess, 'run') as write:
            pg.main()
        get.assert_called_once()
        body = written_body(write)
        self.assertIn('public-repo', body)
        self.assertNotIn('private-repo', body)
        self.assertNotIn('example.test/private', body)
        self.assertIn('public-only (dados privados omitidos)', body)
        # Writes inherit the workflow GH_TOKEN; the read token is never injected.
        self.assertNotIn('env', write.call_args.kwargs)
        self.assertEqual(write.call_args.args[0][:4], ['gh', 'api', '-X', 'POST'])

    def test_no_token_flow_publishes_partial_public_coverage(self):
        calls = []
        def fake_gh(path, read_portfolio=False):
            calls.append((path, read_portfolio))
            if path.startswith(f'users/{pg.OWNER}/repos?'):
                return [PUBLIC, PRIVATE]
            if path.startswith(f'repos/{pg.OWNER}/{pg.REPO}/issues?'):
                return []
            raise AssertionError(path)
        with patch.object(pg, 'gh', side_effect=fake_gh), \
             patch.object(pg, 'public_catalog', side_effect=OSError('synthetic')), \
             patch.object(pg.subprocess, 'run') as write:
            pg.main()
        self.assertEqual(calls[0][1], True)
        self.assertFalse(any(path.startswith('user/repos') for path, _ in calls))
        body = written_body(write)
        self.assertIn('public-only (privados não verificados)', body)
        self.assertIn('Total visível: 1;', body)
        for forbidden in PRIVATE_MARKERS:
            self.assertNotIn(forbidden, body)

    def test_existing_canonical_issue_is_patched_with_sanitized_body(self):
        canonical = {'number': 42, 'body': pg.MARKER, 'user': {'login': 'github-actions[bot]'}}
        with patch.dict(pg.os.environ, {'PORTFOLIO_READ_TOKEN': 'synthetic-read'}), \
             patch.object(pg, 'inventory', return_value=[PUBLIC, PRIVATE]), \
             patch.object(pg, 'gh', return_value=[canonical]), \
             patch.object(pg, 'public_catalog', side_effect=OSError('synthetic')), \
             patch.object(pg.subprocess, 'run') as write:
            pg.main()
        command = write.call_args.args[0]
        self.assertEqual(command[:5], ['gh', 'api', '-X', 'PATCH', f'repos/{pg.OWNER}/{pg.REPO}/issues/42'])
        self.assertNotIn('env', write.call_args.kwargs)
        payload = json.loads(write.call_args.kwargs['input'])
        self.assertEqual(set(payload), {'body'})
        self.assertIn('public-repo', payload['body'])
        for forbidden in PRIVATE_MARKERS:
            self.assertNotIn(forbidden, payload['body'])

    def test_spoofed_marker_from_untrusted_author_is_ignored(self):
        spoof = {'number': 7, 'body': pg.MARKER, 'user': {'login': 'stranger'}, 'author_association': 'NONE'}
        canonical = {'number': 42, 'body': 'x ' + pg.MARKER, 'user': {'login': pg.OWNER}}
        pr = {'number': 9, 'body': pg.MARKER, 'pull_request': {}, 'user': {'login': pg.OWNER}}
        with patch.object(pg, 'inventory', return_value=[PUBLIC]), \
             patch.object(pg, 'gh', return_value=[spoof, pr, canonical]), \
             patch.object(pg, 'public_catalog', side_effect=OSError('synthetic')), \
             patch.object(pg.subprocess, 'run') as write:
            pg.main()
        write.assert_called_once()
        self.assertTrue(write.call_args.args[0][4].endswith('/issues/42'))

    def test_ambiguous_or_incomplete_issue_lookup_never_writes(self):
        trusted = {'body': pg.MARKER, 'author_association': 'OWNER'}
        cases = {
            'ambiguous': [[dict(trusted, number=1), dict(trusted, number=2)]],
            'incomplete-pagination': [[{'number': n} for n in range(100)]] * 10,
            'invalid-page': [{'message': 'synthetic'}],
        }
        for label, pages in cases.items():
            with self.subTest(label), \
                 patch.object(pg, 'inventory', return_value=[PUBLIC]), \
                 patch.object(pg, 'gh', side_effect=pages), \
                 patch.object(pg, 'public_catalog', side_effect=OSError('synthetic')), \
                 patch.object(pg.subprocess, 'run') as write:
                with self.assertRaises(ValueError):
                    pg.main()
                write.assert_not_called()

    def test_catalog_request_is_anonymous_and_bounded(self):
        response = catalog_response(b'{}')
        with patch.dict(pg.os.environ, {'GH_TOKEN': 'synthetic-write', 'PORTFOLIO_READ_TOKEN': 'synthetic-read'}), \
             patch.object(pg.urllib.request, 'urlopen', return_value=response) as open_url, \
             patch.object(pg, 'decode_github_content', return_value={}) as decode:
            pg.public_catalog()
        request = open_url.call_args.args[0]
        self.assertIsNone(request.get_header('Authorization'))
        self.assertEqual(request.full_url, 'https://api.github.com/' + pg.PORTAL_PATH)
        self.assertEqual(open_url.call_args.kwargs['timeout'], 15)
        response.__enter__.return_value.read.assert_called_once_with(3_000_001)
        decode.assert_called_once_with({})

    def test_invalid_catalog_responses_raise_value_error(self):
        cases = {
            'oversize': b'x' * 3_000_001,
            'not-json': b'not json',
            'not-base64-envelope': json.dumps({'encoding': 'utf-8', 'content': '{}'}).encode(),
            'not-utf8': encoded_catalog(b'\xff\xfe'),
            'not-object': encoded_catalog(b'[]'),
        }
        for label, payload in cases.items():
            with self.subTest(label), \
                 patch.object(pg.urllib.request, 'urlopen', return_value=catalog_response(payload)):
                with self.assertRaises(ValueError):
                    pg.public_catalog()

    def test_inaccessible_catalog_fails_closed(self):
        for error in (OSError('synthetic-private-catalog'), http.client.IncompleteRead(b'partial')):
            with self.subTest(error=type(error).__name__), \
                 patch.object(pg, 'inventory', return_value=[]), \
                 patch.object(pg, 'public_catalog', side_effect=error), \
                 patch.object(pg, 'gh', return_value=[]), \
                 patch.object(pg.subprocess, 'run') as write:
                pg.main()
            body = written_body(write)
            self.assertIn('UNVERIFIED', body)
            self.assertNotIn('synthetic-private-catalog', body)

    def test_catalog_transport_and_content_failures_never_confirm_or_leak(self):
        secret = 'synthetic-secret-detail'
        cases = {
            'timeout': {'side_effect': socket.timeout(secret)},
            'http-error': {'side_effect': urllib.error.HTTPError('https://x.test', 404, secret, {}, None)},
            'url-error': {'side_effect': urllib.error.URLError(secret)},
            'non-object-catalog': {'return_value': catalog_response(encoded_catalog(b'["' + secret.encode() + b'"]'))},
            'invalid-json': {'return_value': catalog_response(secret.encode())},
        }
        for label, behaviour in cases.items():
            with self.subTest(label), \
                 patch.object(pg, 'inventory', return_value=[PUBLIC]), \
                 patch.object(pg, 'gh', return_value=[]), \
                 patch.object(pg.urllib.request, 'urlopen', **behaviour), \
                 patch.object(pg.subprocess, 'run') as write:
                pg.main()
            body = written_body(write)
            self.assertIn('UNVERIFIED — cobertura do catálogo não comprovada.', body)
            self.assertNotIn('CONSISTENT', body)
            self.assertNotIn(secret, body)

    def test_missing_private_token_selects_public_endpoint_and_marks_coverage(self):
        with patch.dict(pg.os.environ,{'PORTFOLIO_READ_TOKEN':''}),patch.object(pg,'gh',return_value=[]) as get:
            self.assertEqual(pg.inventory(),[])
            self.assertIn('users/leandroclf/repos?',get.call_args.args[0])
        report=pg.render([],coverage='public-only (privados não verificados)')
        self.assertIn('public-only',report)
        self.assertIn('não prova inexistência',report)

    def test_scoped_inventory_paginates_and_filters_owner(self):
        mine={'name':'a','owner':{'login':pg.OWNER}}
        other={'name':'foreign','owner':{'login':'other'}}
        orphan={'name':'orphan','owner':None}
        with patch.dict(pg.os.environ,{'PORTFOLIO_READ_TOKEN':'synthetic-read'}),patch.object(pg,'gh',side_effect=[[mine]*98+[other, orphan],[]]) as get:
            self.assertEqual(len(pg.inventory()),98)
            self.assertIn('user/repos?',get.call_args_list[0].args[0])
            self.assertIn('page=2',get.call_args_list[1].args[0])

    def test_reader_token_is_never_used_for_issue_operations(self):
        response=type('Response',(),{'stdout':'[]'})()
        with patch.dict(pg.os.environ,{'GH_TOKEN':'synthetic-write','PORTFOLIO_READ_TOKEN':'synthetic-read'}),patch.object(pg.subprocess,'run',return_value=response) as run:
            pg.gh('public/read',read_portfolio=True)
            self.assertEqual(run.call_args.kwargs['env']['GH_TOKEN'],'synthetic-read')
            pg.gh('repos/owner/repo/issues')
            self.assertEqual(run.call_args.kwargs['env']['GH_TOKEN'],'synthetic-write')

    def test_authorization_failure_with_token_does_not_downgrade_or_write(self):
        denied = subprocess.CalledProcessError(1, ['gh'], stderr='synthetic-denied')
        with patch.dict(pg.os.environ,{'PORTFOLIO_READ_TOKEN':'synthetic-read'}), \
             patch.object(pg,'gh',side_effect=denied) as get, \
             patch.object(pg.subprocess, 'run') as write:
            with self.assertRaises(subprocess.CalledProcessError):
                pg.main()
        get.assert_called_once()
        self.assertTrue(get.call_args.args[0].startswith('user/repos?'))
        write.assert_not_called()

if __name__=='__main__':unittest.main()
