"""Offline tests: refuse stale, closed and tampered queue entries."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

scripts = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(scripts))
from autonomy_backlog import prepare
from backlog_candidate_queue import build_queue

spec = importlib.util.spec_from_file_location("fresh_queue_handoff",
                                               scripts / "fresh_queue_handoff.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def live_issue(number=28):
    task = {
        "source": "architecture",
        "target_repository": "leandroclf/product-platform",
        "problem": "Verify current issue before handoff",
        "evidence_url": "https://github.com/leandroclf/product-platform/issues/12",
        "acceptance_criteria": ["Do not execute changed task"],
        "risk": "R1", "rollback": "Revert documentation commit", "max_cycles": 1,
    }
    return {
        "number": number, "state": "open",
        "labels": [{"name": "agent-candidate"}, {"name": "priority-p1"}],
        "html_url": f"https://github.com/leandroclf/product-platform/issues/{number}",
        "body": "\u0060\u0060\u0060autonomy-task\n" + json.dumps(task) + "\n\u0060\u0060\u0060",
    }


def queue_from(issue):
    return build_queue([issue], "leandroclf/product-platform")


class FreshQueueTests(unittest.TestCase):
    def test_live_issue_produces_inert_preview(self):
        issue = live_issue()
        queue = queue_from(issue)
        result = module.select(queue, 28, lambda _: issue)
        self.assertEqual(result["mode"], "PREVIEW_ONLY")
        self.assertFalse(result["execution_allowed"])
        self.assertEqual(result["task_sha256"], queue["items"][0]["task_sha256"])

    def test_closed_issue_rejected(self):
        issue = live_issue()
        queue = queue_from(issue)
        with self.assertRaises(ValueError):
            module.select(queue, 28, lambda _: {**issue, "state": "closed"})

    def test_label_removed_rejected(self):
        issue = live_issue()
        queue = queue_from(issue)
        with self.assertRaises(ValueError):
            module.select(queue, 28, lambda _: {**issue, "labels": []})

    def test_changed_body_rejected(self):
        issue = live_issue()
        queue = queue_from(issue)
        changed = {**issue, "body": issue["body"].replace("current issue", "altered issue")}
        with self.assertRaisesRegex(ValueError, "changed"):
            module.select(queue, 28, lambda _: changed)

    def test_queue_hash_tampered(self):
        issue = live_issue()
        queue = queue_from(issue)
        queue["items"][0]["task_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            module.select(queue, 28, lambda _: issue)

    def test_queue_not_executable(self):
        issue = live_issue()
        queue = queue_from(issue)
        queue["execution_allowed"] = True
        with self.assertRaises(ValueError):
            module.select(queue, 28, lambda _: issue)

    def test_missing_issue_rejected_without_get(self):
        issue = live_issue()
        queue = queue_from(issue)
        with self.assertRaises(ValueError):
            module.select(queue, 29, lambda _: self.fail("unwanted API call"))

    def test_duplicated_issue_rejected(self):
        issue = live_issue()
        queue = queue_from(issue)
        queue["items"].append(dict(queue["items"][0]))
        with self.assertRaises(ValueError):
            module.select(queue, 28, lambda _: issue)

    def test_forged_issue_url_rejected(self):
        issue = live_issue()
        queue = queue_from(issue)
        queue["items"][0]["issue_url"] = "https://github.com.evil.test/x/y/issues/28"
        with self.assertRaises(ValueError):
            module.select(queue, 28, lambda _: issue)


if __name__ == "__main__":
    unittest.main()
