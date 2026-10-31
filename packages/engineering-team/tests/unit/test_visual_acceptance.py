import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import unittest

from scripts import validate_visual_feedback as visual
from tests.unit import test_visual_feedback as fixtures


class VisualAcceptanceTests(unittest.TestCase):
    def setUp(self):
        fixtures.VisualFeedbackTests.setUp(self)
        self.checkout = self.root / 'checkout'
        self.checkout.mkdir()
        self.git('init', '-q')
        (self.checkout / 'index.html').write_text('<button>Original</button>')
        self.git('add', '.')
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        self.tree = self.git('rev-parse', 'HEAD^{tree}')
        self.task.update(schema_version=2, base_sha=self.head,
                         ux={'user_goal': 'Navigate the home page', 'entry': 'Home', 'exit': 'Product page',
                             'patterns_status': 'existing', 'pattern_refs': ['index.html: button'],
                             'design_constraints': ['Reuse existing tokens'],
                             'states': [{'id': state, 'applicable': state == 'ready',
                                         'behavior': 'Ready view' if state == 'ready' else 'Static page: not applicable'}
                                        for state in ['ready', 'loading', 'empty', 'error', 'disabled']]},
                         impact={'paths': ['index.html'], 'preserved_behaviors': [{'id': 'navigation', 'behavior': 'Button remains accessible'}]},
                         regressions=[{'id': 'button', 'behavior_ids': ['navigation'], 'criterion_ids': ['functional'], 'check_name': 'native button smoke'}],
                         performance_budgets=[{'id': 'bundle', 'unit': 'bytes', 'baseline': 100, 'max_after': 110}])
        self.task['viewports'].append({'id': 'desktop', 'width': 1280, 'height': 900})
        desktop = fixtures.png(1280, 900)
        (self.root / 'desktop.png').write_bytes(desktop)
        self.evidence.update(schema_version=2, head_sha=self.head, source_tree_sha=self.tree, status='assessed',
                             screenshots=[{'viewport_id': 'mobile', 'state_id': 'ready', 'artifact': self.artifact},
                                          {'viewport_id': 'desktop', 'state_id': 'ready', 'artifact': {'path': 'desktop.png', 'sha256': hashlib.sha256(desktop).hexdigest()}}],
                             regression_results=[{'id': 'button', 'status': 'pass', 'artifact': self.artifact}],
                             performance_results=[{'id': 'bundle', 'before': 100, 'after': 100, 'artifact': self.artifact}])
        for check in self.evidence['checks']:
            check.update(status='pass', evidence='synthetic fixture, not a live browser result', artifacts=[self.artifact])

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.checkout), *args], text=True).strip()

    def commit(self):
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')

    def validate(self):
        return fixtures.VisualFeedbackTests.validate(self)

    def accept(self):
        self.validate()
        return visual.require_acceptance(self.root / 'task.json', self.root / 'evidence.json', self.root, self.head, self.checkout)

    def test_v2_acceptance_requires_current_clean_checkout_and_complete_results(self):
        self.assertEqual(self.accept(), 'pass')
        self.evidence['status'] = 'captured'
        with self.assertRaisesRegex(ValueError, 'assessed'):
            self.accept()

    def test_fail_not_run_and_blocked_never_accept(self):
        original = copy.deepcopy(self.evidence)
        for collection in ['checks', 'regression_results']:
            for status in ['fail', 'not-run']:
                with self.subTest(collection=collection, status=status):
                    self.evidence = copy.deepcopy(original)
                    self.evidence[collection][0]['status'] = status
                    with self.assertRaises(ValueError):
                        self.accept()
        self.evidence = original
        self.evidence['status'] = 'blocked'
        with self.assertRaises(ValueError):
            self.accept()

    def test_dirty_tracked_staged_and_untracked_code_reject_old_capture(self):
        for mode in ['tracked', 'staged', 'untracked']:
            path = self.checkout / ('index.html' if mode != 'untracked' else 'new.css')
            original = path.read_bytes() if path.exists() else None
            path.write_text('modified after capture')
            if mode == 'staged':
                self.git('add', '.')
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'dirty|source bytes'):
                self.accept()
            self.git('reset', '-q', 'HEAD')
            if original is None:
                path.unlink()
            else:
                path.write_bytes(original)

    def test_stale_tree_and_other_commit_are_rejected(self):
        self.evidence['source_tree_sha'] = 'b' * 40
        with self.assertRaisesRegex(ValueError, 'tree'):
            self.accept()
        self.evidence['source_tree_sha'] = self.tree
        (self.checkout / 'index.html').write_text('new commit after capture')
        self.git('add', '.')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'HEAD'):
            self.accept()

    def test_index_flags_cannot_hide_a_modified_source_file(self):
        for flag in ['assume-unchanged', 'skip-worktree']:
            self.git('update-index', '--' + flag, 'index.html')
            (self.checkout / 'index.html').write_text('change hidden from ordinary git status')
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, 'index flags'):
                self.accept()
            self.git('update-index', '--no-' + flag, 'index.html')
            (self.checkout / 'index.html').write_text('<button>Original</button>')

    def test_preserved_stat_cache_cannot_hide_changed_source_bytes(self):
        source = self.checkout / 'index.html'
        old = time.time() - 86400
        os.utime(source, (old, old))
        self.git('config', 'core.trustctime', 'false')
        self.git('config', 'core.checkStat', 'minimal')
        self.git('update-index', '--refresh')
        source.write_text('<button>Modified</button>')  # same byte length as Original
        os.utime(source, (old, old))
        self.assertEqual(self.git('status', '--porcelain'), '')
        with self.assertRaisesRegex(ValueError, 'source bytes'):
            self.accept()

    def test_acceptance_never_executes_repository_clean_filters(self):
        (self.checkout / '.gitattributes').write_text('index.html filter=poison\n')
        self.git('add', '.')
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        self.evidence.update(head_sha=self.head, source_tree_sha=self.git('rev-parse', 'HEAD^{tree}'))
        self.task['impact']['paths'].append('.gitattributes')
        marker = self.checkout / 'filter-executed'
        self.git('config', 'filter.poison.clean', 'touch filter-executed; cat')
        old = time.time() - 86400
        os.utime(self.checkout / 'index.html', (old, old))
        self.assertEqual(self.accept(), 'pass')
        self.assertFalse(marker.exists())

    def test_source_symlink_is_not_accepted_as_a_materialized_input(self):
        (self.checkout / 'alias.html').symlink_to('index.html')
        self.git('add', '.')
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        self.evidence.update(head_sha=self.head, source_tree_sha=self.git('rev-parse', 'HEAD^{tree}'))
        self.task['impact']['paths'].append('alias.html')
        with self.assertRaisesRegex(ValueError, 'materialized-input'):
            self.accept()

    def test_changed_files_outside_impact_block_acceptance(self):
        (self.checkout / 'other.css').write_text('body { color: red }')
        self.git('add', '.')
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        self.evidence.update(head_sha=self.head, source_tree_sha=self.git('rev-parse', 'HEAD^{tree}'))
        with self.assertRaisesRegex(ValueError, 'scope'):
            self.accept()
        self.task['impact']['paths'].append('other.css')
        self.assertEqual(self.accept(), 'pass')

    def test_states_and_regression_mapping_cannot_be_silently_skipped(self):
        self.task['ux']['states'][1]['applicable'] = True
        with self.assertRaisesRegex(ValueError, 'missing state'):
            self.accept()
        self.task['ux']['states'][1]['applicable'] = False
        self.task['impact']['preserved_behaviors'].append({'id': 'filter', 'behavior': 'Filter still works'})
        with self.assertRaisesRegex(ValueError, 'coverage'):
            self.accept()

    def test_missing_hash_bound_check_artifact_is_rejected(self):
        self.evidence['checks'][0]['artifacts'] = [{'path': 'missing.json', 'sha256': 'a' * 64}]
        with self.assertRaises(FileNotFoundError):
            self.accept()

    def test_patterns_and_performance_require_actual_defined_results(self):
        for status in ['not-assessed', 'existing']:
            self.task['ux'].update(patterns_status=status, pattern_refs=[])
            with self.assertRaises(ValueError):
                self.accept()
        self.task['ux'].update(patterns_status='new', pattern_refs=[])
        self.evidence['performance_results'][0]['after'] = 111
        with self.assertRaisesRegex(ValueError, 'budget'):
            self.accept()
        self.evidence['performance_results'][0].update(before=99, after=100)
        with self.assertRaisesRegex(ValueError, 'baseline'):
            self.accept()

    def test_v1_integrity_cannot_be_relabelled_as_acceptance(self):
        for name in ['ux', 'impact', 'regressions', 'performance_budgets']:
            self.task.pop(name)
        self.task['schema_version'] = 1
        self.evidence['schema_version'] = 1
        for name in ['source_tree_sha', 'regression_results', 'performance_results']:
            self.evidence.pop(name)
        for capture in self.evidence['screenshots']:
            capture.pop('state_id')
        for check in self.evidence['checks']:
            check.pop('artifacts')
        self.assertEqual(self.validate(), 'assessed')
        with self.assertRaisesRegex(ValueError, 'v2'):
            self.accept()

    def test_missing_checkout_cli_never_silently_falls_back_to_integrity(self):
        self.validate()
        self.assertEqual(visual.main(['--task', str(self.root / 'task.json'), '--evidence', str(self.root / 'evidence.json'),
                                      '--root', str(self.root), '--expected-head', self.head, '--require-acceptance']), 1)


if __name__ == '__main__':
    unittest.main()
