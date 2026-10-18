"""Offline contract for one-command pilot. Never starts a real model."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

scripts = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location("run_backlog_pilot", scripts / "run_backlog_pilot.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def issue(state="open", labeled=True, risk="R1"):
    task = {
        "source": "architecture", "target_repository": "leandroclf/product-platform",
        "problem": "Repair broken reference",
        "evidence_url": "https://github.com/leandroclf/product-platform/issues/12",
        "acceptance_criteria": ["Link corrected"],
        "risk": risk, "rollback": "Revert docs change", "max_cycles": 1,
    }
    return {
        "number": 32, "state": state,
        "html_url": "https://github.com/leandroclf/product-platform/issues/32",
        "labels": [{"name": "agent-candidate"}] if labeled else [],
        "body": "\u0060\u0060\u0060autonomy-task\n" + json.dumps(task) + "\n\u0060\u0060\u0060",
    }


class OneCommandPilotTests(unittest.TestCase):
    def setUp(self):
        self.called = []
        self.plan = lambda p, t: {
            "repository": "leandroclf/product-platform",
            "target": str(t), "branch": "pilot",
            "checks_required": ["tests"],
        }
        def execute(p, t, digest):
            self.called.append(digest)
            return "REVIEWED"
        self.execute = execute

    def run_pilot(self, live=None, **kw):
        data = live or issue()
        return module.pilot("leandroclf/product-platform", 32, "/repo",
                            get_issue=lambda _: data, plan_run=self.plan,
                            execute_run=self.execute, **kw)

    def test_default_is_inert_with_no_agent_execution(self):
        result = self.run_pilot()
        self.assertEqual(result["mode"], "PREVIEW_ONLY")
        self.assertFalse(result["execution_allowed"])
        self.assertEqual(self.called, [])

    def test_explicit_correct_hash_runs_existing_launcher(self):
        from autonomy_backlog import prepare
        task = issue()
        expected = prepare(task["body"], task["html_url"])["task_sha256"]
        result = self.run_pilot(execute_requested=True, confirm_hash=expected)
        self.assertEqual(result["result"], "REVIEWED")
        self.assertEqual(self.called, [expected])
        self.assertFalse(result["automatic_merge"])

    def test_wrong_hash_blocks(self):
        with self.assertRaises(ValueError):
            self.run_pilot(execute_requested=True, confirm_hash="nope")
        self.assertEqual(self.called, [])

    def test_missing_label_blocks(self):
        with self.assertRaises(ValueError):
            self.run_pilot(live=issue(labeled=False))
        self.assertEqual(self.called, [])

    def test_closed_issue_blocks(self):
        with self.assertRaises(ValueError):
            self.run_pilot(live=issue(state="closed"))
        self.assertEqual(self.called, [])

    def test_r3_blocks(self):
        with self.assertRaises(ValueError):
            self.run_pilot(live=issue(risk="R3"))
        self.assertEqual(self.called, [])

    def test_issue_changes_between_queries_blocks(self):
        reads = []
        def get(_):
            reads.append(True)
            return issue(state="open" if len(reads) == 1 else "closed")
        with self.assertRaises(ValueError):
            module.pilot("leandroclf/product-platform", 32, "/repo",
                         get_issue=get, plan_run=self.plan, execute_run=self.execute)
        self.assertEqual(len(reads), 2)
        self.assertEqual(self.called, [])

    def test_bad_repository_and_issue_number_fail(self):
        with self.assertRaises(ValueError):
            module.pilot("../unsafe", 32, "/repo", get_issue=lambda _: issue())
        with self.assertRaises(ValueError):
            module.pilot("leandroclf/product-platform", -1, "/repo",
                         get_issue=lambda _: issue())


if __name__ == "__main__":
    unittest.main()
