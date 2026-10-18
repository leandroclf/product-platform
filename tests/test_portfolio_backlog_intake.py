"""Offline regression suite for radar-to-backlog deduplication and write safety."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "intake", Path(__file__).resolve().parents[1] / "scripts" / "portfolio_backlog_intake.py")
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
intake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intake)


def finding(**updates):
    data = {
        "source": "architecture", "target_repository": "leandroclf/agents-workspace",
        "problem": "Outdated canonical module link",
        "evidence_url": "https://github.com/leandroclf/agents-workspace",
        "acceptance_criteria": ["README links to canonical package"],
        "risk": "R1", "rollback": "Revert doc commit", "max_cycles": 1,
    }
    data.update(updates)
    return data


class IntakeTests(unittest.TestCase):
    def test_dry_run_never_writes(self):
        seen = []
        output = intake.run_intake([finding()], "leandroclf/product-platform",
                                   get=lambda _: [], write=lambda *args: seen.append(args))
        self.assertEqual(seen, [])
        self.assertEqual(output[0]["action"], "create")

    def test_known_issue_not_recreated(self):
        key = intake.key_for(finding())
        existing = [{"body": intake.issue_body(key, finding())}]
        output = intake.run_intake([finding()], "leandroclf/product-platform",
                                   get=lambda _: existing,
                                   write=lambda *args: self.fail("unexpected write"), apply=True)
        self.assertEqual(output[0]["action"], "skip_existing")

    def test_key_ignores_minor_description_edit(self):
        original = finding()
        other = finding(problem="More specific description")
        self.assertEqual(intake.key_for(original), intake.key_for(other))

    def test_duplicate_in_batch_blocks_before_access(self):
        with self.assertRaises(ValueError):
            intake.run_intake([finding(), finding()], "leandroclf/product-platform",
                              get=lambda _: self.fail("unexpected read"))

    def test_high_risk_blocks_before_access(self):
        with self.assertRaises(ValueError):
            intake.run_intake([finding(risk="R2")], "leandroclf/product-platform",
                              get=lambda _: self.fail("unexpected read"))

    def test_explicit_apply_creates_candidate(self):
        calls = []
        def write(*args):
            calls.append(args)
            return {"html_url": "https://github.com/leandroclf/product-platform/issues/99"}
        output = intake.run_intake([finding()], "leandroclf/product-platform",
                                   get=lambda _: [], write=write, apply=True)
        self.assertEqual(len(calls), 1)
        self.assertEqual(output[0]["created_url"].split("/")[-1], "99")
        self.assertIn("Status: candidate", calls[0][-1])
        self.assertNotIn("agent-auto-merge", calls[0][-1])

    def test_pagination(self):
        calls = []
        def get(url):
            calls.append(url)
            return [{}] * 100 if url.endswith("&page=1") else []
        self.assertEqual(len(intake.list_existing("leandroclf/product-platform", get)), 100)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
