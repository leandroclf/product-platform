import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

from scripts import validate_visual_feedback as visual


def png(width=320, height=480):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress((b'\0' + b'\xff\xff\xff' * width) * height)) + chunk(b'IEND', b''))


class VisualFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        raw = png()
        (self.root / 'capture.png').write_bytes(raw)
        self.artifact = {'path': 'capture.png', 'sha256': hashlib.sha256(raw).hexdigest()}
        self.head = 'a' * 40
        self.task = {
            'schema_version': 1, 'task_id': 'visual-pilot', 'repository': 'example/product', 'base_sha': self.head,
            'reference': {'artifact': self.artifact, 'usage': 'synthetic', 'source': 'synthetic unit test'},
            'design_system': 'existing product tokens',
            'viewports': [{'id': 'mobile', 'width': 320, 'height': 480}],
            'criteria': [{'id': kind, 'kind': kind, 'description': 'fixture criterion'} for kind in ['visual', 'functional', 'accessibility']],
            'budget': {'max_iterations': 2, 'max_elapsed_seconds': 60, 'max_cost_usd': 1, 'unknown_cost_policy': 'stop'},
        }
        self.evidence = {
            'schema_version': 1, 'task_sha256': '', 'head_sha': self.head, 'condition': 'baseline', 'status': 'captured',
            'iterations': 0, 'elapsed_seconds': 1, 'cost_usd': None, 'model_execution': 'not-run',
            'screenshots': [{'viewport_id': 'mobile', 'artifact': self.artifact}],
            'checks': [{'criterion_id': kind, 'status': 'not-run', 'evidence': 'not executed'} for kind in ['visual', 'functional', 'accessibility']],
            'limitations': ['synthetic test, no model or browser execution'],
        }

    def validate(self):
        task = self.root / 'task.json'
        task.write_text(json.dumps(self.task))
        self.evidence['task_sha256'] = hashlib.sha256(task.read_bytes()).hexdigest()
        evidence = self.root / 'evidence.json'
        evidence.write_text(json.dumps(self.evidence))
        return visual.validate(task, evidence, self.root, self.head)

    def test_capture_is_integrity_not_acceptance(self):
        self.assertEqual(self.validate(), 'captured')
        self.evidence['status'] = 'assessed'
        with self.assertRaisesRegex(ValueError, 'unexecuted'):
            self.validate()
        for check in self.evidence['checks']:
            check['status'] = 'fail'
        self.assertEqual(self.validate(), 'assessed')  # failed quality can have valid evidence

    def test_stale_head_and_task_are_rejected(self):
        self.evidence['head_sha'] = 'b' * 40
        with self.assertRaisesRegex(ValueError, 'stale head'):
            self.validate()
        self.evidence['head_sha'] = self.head
        self.validate()
        task_path = self.root / 'task.json'
        task_path.write_text(task_path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'stale task'):
            visual.validate(task_path, self.root / 'evidence.json', self.root, self.head)

    def test_missing_duplicate_unknown_viewport_and_criterion(self):
        for collection, changed in [('screenshots', []), ('checks', []),
                                    ('screenshots', self.evidence['screenshots'] * 2),
                                    ('checks', [{'criterion_id': 'unknown', 'status': 'pass', 'evidence': 'x'}])]:
            with self.subTest(collection=collection, changed=changed):
                original = self.evidence[collection]
                self.evidence[collection] = changed
                with self.assertRaises(ValueError):
                    self.validate()
                self.evidence[collection] = original

    def test_digest_dimensions_and_corrupt_png(self):
        (self.root / 'capture.png').write_bytes(png(321))
        with self.assertRaisesRegex(ValueError, 'digest'):
            self.validate()
        self.artifact['sha256'] = hashlib.sha256((self.root / 'capture.png').read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            self.validate()
        raw = png()[:-1]
        (self.root / 'capture.png').write_bytes(raw)
        self.artifact['sha256'] = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError):
            self.validate()

    def test_paths_and_symlink_escape(self):
        for path in ['../capture.png', '/tmp/capture.png', 'a\\capture.png']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                visual.artifact_bytes(self.root, {**self.artifact, 'path': path})
        (self.root / 'escape').symlink_to(self.root.parent)
        with self.assertRaises(ValueError):
            visual.artifact_bytes(self.root, {**self.artifact, 'path': 'escape/' + self.root.name + '/capture.png/../..'})
        with tempfile.TemporaryDirectory() as other:
            external = Path(other) / 'outside.png'
            external.write_bytes(png())
            (self.root / 'outside.png').symlink_to(external)
            with self.assertRaises(ValueError):
                visual.artifact_bytes(self.root, {**self.artifact, 'path': 'outside.png'})

    def test_budget_and_unknown_live_cost_require_blocked(self):
        for changes in [{'iterations': 3}, {'elapsed_seconds': 61}, {'cost_usd': 2}, {'model_execution': 'live'}]:
            with self.subTest(changes=changes):
                original = copy.deepcopy(self.evidence)
                self.evidence.update(changes)
                with self.assertRaisesRegex(ValueError, 'budget'):
                    self.validate()
                self.evidence['status'] = 'blocked'
                self.assertEqual(self.validate(), 'blocked')
                self.evidence = original

    def test_duplicate_keys_nonfinite_and_schema_extensions(self):
        path = self.root / 'invalid.json'
        for raw in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}']:
            path.write_text(raw)
            with self.assertRaises(ValueError):
                visual.read_json(path)
        self.task['execute'] = 'never run manifest commands'
        with self.assertRaises(Exception):
            self.validate()

    def test_reads_are_bounded_before_allocation(self):
        path = self.root / 'large.json'
        path.write_bytes(b' ' * 65)
        with patch.object(visual, 'MAX_JSON_BYTES', 64), self.assertRaisesRegex(ValueError, 'size limit'):
            visual.read_json(path)
        with patch.object(visual, 'MAX_ARTIFACT_BYTES', 64), self.assertRaisesRegex(ValueError, 'size limit'):
            visual.artifact_bytes(self.root, self.artifact)


class VisualFeedbackBaselineIntegrityTests(unittest.TestCase):
    def test_committed_lf_home_baseline_artifacts_keep_integrity(self):
        root = Path(__file__).resolve().parents[2] / 'validation/visual-feedback-baseline-2026-10-31'
        self.assertEqual(visual.validate(root / 'task.v2.json', root / 'evidence.v2.json', root,
                                         '3ff63351fca2ca3b0166bfe3056bca44e93368b1'), 'captured')


if __name__ == '__main__':
    unittest.main()
