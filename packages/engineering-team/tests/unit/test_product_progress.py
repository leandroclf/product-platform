"""Persistent product-content repair loop detection using real Git repositories."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.local_team import Blocked, record_product_progress


class ProductProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'test')
        self.commit('initial')
        self.state = {'base_sha': self.git('rev-parse', 'HEAD'), 'task': 'test'}

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, text=True,
                              capture_output=True, check=True).stdout.strip()

    def commit(self, content):
        (self.repo / 'product.txt').write_text(content)
        self.git('add', '.')
        self.git('commit', '-qm', 'test')

    def observe(self, content):
        self.commit(content)
        record_product_progress(self.repo, self.state)

    def test_real_changes_continue_and_history_is_bounded(self):
        for index in range(10):
            self.observe(str(index))
        self.assertEqual(len(self.state['product_progress']), 6)

    def test_notes_and_restart_cannot_hide_no_progress(self):
        self.observe('changed')
        for index in range(2):
            notes = self.repo / 'openspec/changes/ai-team-test/tasks.md'
            notes.parent.mkdir(parents=True, exist_ok=True)
            notes.write_text(str(index))
            self.git('add', '.')
            self.git('commit', '-qm', 'notes only')
            self.state = json.loads(json.dumps(self.state))
            if index == 0:
                record_product_progress(self.repo, self.state)
            else:
                with self.assertRaisesRegex(Blocked, 'no product progress'):
                    record_product_progress(self.repo, self.state)

    def test_alternating_repairs_block(self):
        for content in ['A', 'B', 'A']:
            self.observe(content)
        with self.assertRaisesRegex(Blocked, 'alternating product repair'):
            self.observe('B')

    def test_product_specs_count_as_progress(self):
        spec = self.repo / 'openspec/specs/product/spec.md'
        spec.parent.mkdir(parents=True)
        for index in range(4):
            spec.write_text(str(index))
            self.git('add', '.')
            self.git('commit', '-qm', 'spec change')
            record_product_progress(self.repo, self.state)
        self.assertEqual(len(set(self.state['product_progress'])), 4)


if __name__ == '__main__':
    unittest.main()
