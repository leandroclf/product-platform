"""Boundary tests for the local reviewer; no model, Docker or GitHub credentials."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('worker', SCRIPTS / 'independent_pr_reviewer.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
SHA = 'a' * 40


def pr():
    return {'number': 7, 'state': 'open', 'draft': False, 'user': {'login': 'executor'},
            'head': {'sha': SHA, 'repo': {'full_name': worker.REPO}},
            'base': {'ref': 'main', 'repo': {'full_name': worker.REPO}},
            'labels': [{'name': 'agent-auto-merge'}]}


def checks():
    return [{'id': i, 'name': name, 'head_sha': SHA, 'status': 'completed',
             'conclusion': 'success', 'app': {'slug': 'github-actions'}}
            for i, name in enumerate(sorted(worker.REQUIRED_CHECKS))]


class ReviewerTests(unittest.TestCase):
    def test_only_open_same_repository_opt_in_prs(self):
        self.assertTrue(worker.eligible(pr(), [{'filename': 'src/app.py'}]))
        for change in ({'draft': True}, {'state': 'closed'}, {'labels': []},
                       {'user': {'login': worker.REVIEWER}},
                       {'head': {'sha': SHA, 'repo': {'full_name': 'foreign/repo'}}}):
            with self.subTest(change=change):
                self.assertFalse(worker.eligible({**pr(), **change}, [{'filename': 'src/app.py'}]))

    def test_protected_paths_renames_and_dependencies_require_manual_review(self):
        for path in ('.github/workflows/change.yml', 'infra/main.tf', 'AGENTS.md',
                     'scripts/independent_pr_reviewer.py', 'package-lock.json', 'package.json'):
            with self.subTest(path=path):
                self.assertFalse(worker.eligible(pr(), [{'filename': path}]))
                self.assertFalse(worker.eligible(pr(), [{'filename': 'docs/moved.md', 'previous_filename': path}]))

    def test_empty_or_large_pr_is_not_eligible(self):
        self.assertFalse(worker.eligible(pr(), []))
        self.assertFalse(worker.eligible(pr(), [{'filename': 'docs/a.md'}] * 51))

    def test_ci_requires_both_current_github_actions_checks(self):
        self.assertTrue(worker.ci_passed(checks(), SHA))
        self.assertFalse(worker.ci_passed(checks()[:1], SHA))
        self.assertFalse(worker.ci_passed(checks(), 'b' * 40))
        forged = checks()
        forged[0]['app']['slug'] = 'untrusted-app'
        self.assertFalse(worker.ci_passed(forged, SHA))

    def test_latest_failure_overrides_old_success(self):
        rows = checks()
        rows.append({**rows[0], 'id': 99, 'conclusion': 'failure'})
        self.assertFalse(worker.ci_passed(rows, SHA))

    def test_stale_head_never_submits_review(self):
        current = copy.deepcopy(pr())
        current['head']['sha'] = 'b' * 40
        with patch.object(worker, 'files_for', return_value=[{'filename': 'src/app.py'}]), \
             patch.object(worker, 'request', side_effect=[[], {'check_runs': checks()}, current]) as api, \
             patch.object(worker, 'evaluate', return_value=({'head_sha': SHA}, True)), \
             self.assertRaises(ValueError):
            worker.process(pr(), 'not-a-token', Path('/unused'))
        self.assertTrue(all(len(call.args) == 2 for call in api.call_args_list))

    def test_real_assessment_determines_review_event_and_commit(self):
        for accepted, event in ((True, 'APPROVE'), (False, 'REQUEST_CHANGES')):
            with self.subTest(accepted=accepted), \
                 patch.object(worker, 'files_for', return_value=[{'filename': 'src/app.py'}]), \
                 patch.object(worker, 'request', side_effect=[[], {'check_runs': checks()}, pr(), {}]) as api, \
                 patch.object(worker, 'evaluate', return_value=({'head_sha': SHA}, accepted)), \
                 patch.object(worker, 'rerun_gate'):
                self.assertTrue(worker.process(pr(), 'not-a-token', Path('/unused')))
                self.assertEqual(api.call_args.args[2]['event'], event)
                self.assertEqual(api.call_args.args[2]['commit_id'], SHA)

    def test_existing_review_prevents_duplicate_model_or_approval(self):
        review = {'user': {'login': worker.REVIEWER}, 'commit_id': SHA, 'state': 'APPROVED'}
        with patch.object(worker, 'files_for', return_value=[{'filename': 'src/app.py'}]), \
             patch.object(worker, 'request', return_value=[review]), \
             patch.object(worker, 'evaluate') as evaluate, patch.object(worker, 'rerun_gate') as rerun:
            self.assertFalse(worker.process(pr(), 'not-a-token', Path('/unused')))
            evaluate.assert_not_called()
            rerun.assert_called_once_with(SHA, Path('/unused'))

    def test_failed_ci_never_invokes_model(self):
        with patch.object(worker, 'files_for', return_value=[{'filename': 'src/app.py'}]), \
             patch.object(worker, 'request', side_effect=[[], {'check_runs': []}]), \
             patch.object(worker, 'evaluate') as evaluate:
            self.assertFalse(worker.process(pr(), 'not-a-token', Path('/unused')))
            evaluate.assert_not_called()

    def test_readable_key_or_symlink_is_rejected_before_transport(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(worker, 'request') as api:
            key = Path(directory) / 'key.pem'
            key.write_text('not a key')
            key.chmod(0o644)
            with self.assertRaises(ValueError):
                worker.installation_token(key, '123')
            key.chmod(0o600)
            link = Path(directory) / 'link.pem'
            link.symlink_to(key)
            with self.assertRaises(ValueError):
                worker.installation_token(link, '123')
            api.assert_not_called()


if __name__ == '__main__':
    unittest.main()
