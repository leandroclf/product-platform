import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import portfolio_governance as pg

class InventoryTests(unittest.TestCase):
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
