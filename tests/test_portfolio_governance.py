import json
import http.client
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import portfolio_governance as pg

class InventoryTests(unittest.TestCase):
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
        body = json.loads(write.call_args.kwargs['input'])['body']
        self.assertIn('public-repo', body)
        self.assertNotIn('private-repo', body)
        self.assertNotIn('example.test/private', body)
        self.assertIn('public-only (dados privados omitidos)', body)

    def test_catalog_request_is_anonymous_and_bounded(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{}'
        with patch.dict(pg.os.environ, {'GH_TOKEN': 'synthetic-write', 'PORTFOLIO_READ_TOKEN': 'synthetic-read'}), \
             patch.object(pg.urllib.request, 'urlopen', return_value=response) as open_url, \
             patch.object(pg, 'decode_github_content', return_value={}) as decode:
            pg.public_catalog()
        request = open_url.call_args.args[0]
        self.assertIsNone(request.get_header('Authorization'))
        response.__enter__.return_value.read.assert_called_once_with(3_000_001)
        decode.assert_called_once_with({})

    def test_inaccessible_catalog_fails_closed(self):
        for error in (OSError('synthetic-private-catalog'), http.client.IncompleteRead(b'partial')):
            with self.subTest(error=type(error).__name__), \
                 patch.object(pg, 'inventory', return_value=[]), \
                 patch.object(pg, 'public_catalog', side_effect=error), \
                 patch.object(pg, 'gh', return_value=[]), \
                 patch.object(pg.subprocess, 'run') as write:
                pg.main()
            body = json.loads(write.call_args.kwargs['input'])['body']
            self.assertIn('UNVERIFIED', body)
            self.assertNotIn('synthetic-private-catalog', body)

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
        with patch.dict(pg.os.environ,{'PORTFOLIO_READ_TOKEN':'synthetic-read'}),patch.object(pg,'gh',side_effect=[[mine]*99+[other],[]]) as get:
            self.assertEqual(len(pg.inventory()),99)
            self.assertIn('user/repos?',get.call_args_list[0].args[0])
            self.assertIn('page=2',get.call_args_list[1].args[0])

    def test_reader_token_is_never_used_for_issue_operations(self):
        response=type('Response',(),{'stdout':'[]'})()
        with patch.dict(pg.os.environ,{'GH_TOKEN':'synthetic-write','PORTFOLIO_READ_TOKEN':'synthetic-read'}),patch.object(pg.subprocess,'run',return_value=response) as run:
            pg.gh('public/read',read_portfolio=True)
            self.assertEqual(run.call_args.kwargs['env']['GH_TOKEN'],'synthetic-read')
            pg.gh('repos/owner/repo/issues')
            self.assertEqual(run.call_args.kwargs['env']['GH_TOKEN'],'synthetic-write')

    def test_no_token_silently_downgrades_an_authorization_failure(self):
        with patch.dict(pg.os.environ,{'PORTFOLIO_READ_TOKEN':'synthetic-read'}),patch.object(pg,'gh',side_effect=RuntimeError('denied')):
            with self.assertRaises(RuntimeError):pg.inventory()

if __name__=='__main__':unittest.main()
