"""Offline contract tests for inert, bounded task handoff."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "autonomy_backlog", Path(__file__).resolve().parents[1] / "scripts" / "autonomy_backlog.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def body(**changes):
    task = {
        "source": "architecture",
        "target_repository": "leandroclf/product-platform",
        "problem": "Outdated link in documentation",
        "evidence_url": "https://github.com/leandroclf/product-platform/issues/12",
        "acceptance_criteria": ["Link points to active directory"],
        "risk": "R1",
        "rollback": "Revert documentation commit",
        "max_cycles": 2,
    }
    task.update(changes)
    return "```autonomy-task\n" + json.dumps(task) + "\n```"


class TaskContractTests(unittest.TestCase):
    def test_valid_task_preview_does_not_execute(self):
        result = module.prepare(body(), "https://github.com/leandroclf/product-platform/issues/12")
        self.assertFalse(result["execution_allowed"])
        self.assertEqual(result["mode"], "PREVIEW_ONLY")
        self.assertEqual(result["status"], "awaiting_independent_triage")
        self.assertEqual(len(result["task_sha256"]), 64)

    def test_deterministic_fingerprint(self):
        self.assertEqual(module.prepare(body(), "https://example.com/1")["task_sha256"],
                         module.prepare(body(), "https://example.com/2")["task_sha256"])

    def test_blocks_high_risk(self):
        for value in ("R2", "R3", "UNKNOWN"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.parse_issue(body(risk=value))

    def test_rejects_missing_evidence(self):
        with self.assertRaises(ValueError):
            module.parse_issue(body(evidence_url=""))

    def test_rejects_unbounded_cycles(self):
        for value in (0, 4, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.parse_issue(body(max_cycles=value))

    def test_rejects_invalid_repository(self):
        with self.assertRaises(ValueError):
            module.parse_issue(body(target_repository="../local"))

    def test_rejects_extra_fields(self):
        with self.assertRaises(ValueError):
            module.parse_issue(body(shell_command="rm -rf ."))

    def test_rejects_duplicate_task_blocks(self):
        with self.assertRaises(ValueError):
            module.parse_issue(body() + "\n" + body())

    def test_rejects_missing_acceptance(self):
        with self.assertRaises(ValueError):
            module.parse_issue(body(acceptance_criteria=[]))


if __name__ == "__main__":
    unittest.main()
