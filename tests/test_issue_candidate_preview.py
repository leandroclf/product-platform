"""No credential tests for GitHub issue candidate validation."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

script_dir = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(script_dir))
spec = importlib.util.spec_from_file_location("issue_candidate_preview", script_dir / "issue_candidate_preview.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def issue(*, label=True, state="open", pr=False, number=17):
    body = {
        "source": "security",
        "target_repository": "leandroclf/product-platform",
        "problem": "Regression detected in test runner",
        "evidence_url": "https://github.com/leandroclf/product-platform/issues/12",
        "acceptance_criteria": ["Tests pass"],
        "risk": "R1",
        "rollback": "Revert the changes",
        "max_cycles": 2,
    }
    item = {"state": state, "number": number, "labels": [{"name": "agent-candidate"}] if label else [],
            "body": "```autonomy-task\n" + json.dumps(body) + "\n```",
            "html_url": f"https://github.com/leandroclf/product-platform/issues/{number}"}
    if pr:
        item["pull_request"] = {"url": "https://api.github.com/example"}
    return item


class CandidateTests(unittest.TestCase):
    def test_open_labeled_issue_generates_only_preview(self):
        item = module.candidate("leandroclf/product-platform", "17", lambda _: issue())
        self.assertEqual(item["mode"], "PREVIEW_ONLY")
        self.assertFalse(item["execution_allowed"])

    def test_unlabeled_issue_rejected(self):
        with self.assertRaises(ValueError):
            module.candidate("leandroclf/product-platform", "17", lambda _: issue(label=False))

    def test_closed_issue_rejected(self):
        with self.assertRaises(ValueError):
            module.candidate("leandroclf/product-platform", "17", lambda _: issue(state="closed"))

    def test_pull_request_rejected(self):
        with self.assertRaises(ValueError):
            module.candidate("leandroclf/product-platform", "17", lambda _: issue(pr=True))

    def test_invalid_issue_number_rejected(self):
        for value in ("-1", "abc", "0", "1;echo"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.candidate("leandroclf/product-platform", value, lambda _: issue())

    def test_invalid_body_rejected(self):
        with self.assertRaises(ValueError):
            module.candidate("leandroclf/product-platform", "17", lambda _: {**issue(), "body": "not a task"})


if __name__ == "__main__":
    unittest.main()
