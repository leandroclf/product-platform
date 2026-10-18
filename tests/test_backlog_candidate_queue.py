"""Credential-free queue selection tests."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

scripts = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location("backlog_candidate_queue", scripts / "backlog_candidate_queue.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def issue(n=1, *, priority=None, risk="R1", label=True, state="open"):
    task = {
        "source": "architecture",
        "target_repository": "leandroclf/product-platform",
        "problem": "Outdated documentation link",
        "evidence_url": "https://github.com/leandroclf/product-platform/issues/12",
        "acceptance_criteria": ["Canonical link is fixed"],
        "risk": risk,
        "rollback": "Revert documentation commit",
        "max_cycles": 1,
    }
    names = (["agent-candidate"] if label else []) + ([priority] if priority else [])
    return {"number": n, "state": state, "labels": [{"name": x} for x in names],
            "body": "\u0060\u0060\u0060autonomy-task\n" + json.dumps(task) + "\n\u0060\u0060\u0060",
            "html_url": f"https://github.com/leandroclf/product-platform/issues/{n}"}


class QueueTests(unittest.TestCase):
    def test_order_is_priority_then_risk_then_number(self):
        items = [
            issue(7, priority="priority-p2"), issue(5, priority="priority-p0"),
            issue(4, priority="priority-p1"), issue(9, priority="priority-p0", risk="R0"),
        ]
        result = module.build_queue(items, "leandroclf/product-platform")
        self.assertEqual([x["issue_number"] for x in result["items"]], [9, 5, 4, 7])
        self.assertFalse(result["execution_allowed"])
        self.assertTrue(all(not x["execution_allowed"] for x in result["items"]))

    def test_label_missing_excluded(self):
        result = module.build_queue([issue(label=False)], "leandroclf/product-platform")
        self.assertEqual(result["items"], [])

    def test_closed_issues_and_prs_excluded(self):
        pull = issue(3)
        pull["pull_request"] = {"url": "url"}
        result = module.build_queue([issue(1, state="closed"), pull], "leandroclf/product-platform")
        self.assertEqual(result["items"], [])

    def test_invalid_risk_rejected_not_dispatched(self):
        result = module.build_queue([issue(2, risk="R3")], "leandroclf/product-platform")
        self.assertEqual(result["eligible_total"], 0)
        self.assertEqual(result["rejected"][0]["issue_number"], 2)

    def test_conflicting_priority_rejected(self):
        item = issue(2, priority="priority-p0")
        item["labels"].append({"name": "priority-p1"})
        result = module.build_queue([item], "leandroclf/product-platform")
        self.assertEqual(result["eligible_total"], 0)

    def test_limit_bounds(self):
        with self.assertRaises(ValueError):
            module.build_queue([issue()], "leandroclf/product-platform", limit=0)
        result = module.build_queue([issue(2), issue(1)], "leandroclf/product-platform", limit=1)
        self.assertEqual(result["eligible_total"], 2)
        self.assertEqual(len(result["items"]), 1)

    def test_incomplete_pagination_fails(self):
        def get(_):
            return [issue()] * 100
        with self.assertRaises(ValueError):
            module.list_open("leandroclf/product-platform", get)

    def test_one_page_success(self):
        result = module.list_open("leandroclf/product-platform", lambda _: [issue()])
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
