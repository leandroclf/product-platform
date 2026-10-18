"""Offline tests for PR risk packet; does not need GitHub credentials."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "packet", Path(__file__).resolve().parents[1] / "scripts" / "manual_pr_review_packet.py")
packet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packet)
HEAD = "a" * 40


def pr(sha=HEAD):
    return {"number": 19, "head": {"sha": sha}, "title": "Proposed change",
            "user": {"login": "agent-executor"}}


def changed(path="src/app.py"):
    return [{"filename": path, "status": "modified", "additions": 3, "deletions": 1}]


class ManualReviewPacketTests(unittest.TestCase):
    def test_normal_code_is_candidate_not_approved(self):
        report = packet.summarize(pr(), changed())
        self.assertTrue(report["manual_review_required"])
        self.assertFalse(report["automation_approval"])
        self.assertEqual(report["elevated"], [])
        self.assertIn("not an approval", packet.render(report))

    def test_workflow_requires_elevated_attention(self):
        report = packet.summarize(pr(), changed(".github/workflows/gate.yml"))
        self.assertEqual(report["elevated"][0]["risk"], "R2")

    def test_gate_script_requires_elevated_attention(self):
        report = packet.summarize(pr(), changed("scripts/agent_review_gate.py"))
        self.assertEqual(report["elevated"][0]["risk"], "R2")

    def test_dependencies_require_extra_review(self):
        report = packet.summarize(pr(), changed("package-lock.json"))
        self.assertEqual(report["elevated"][0]["risk"], "R2-review")

    def test_invalid_sha_fails_closed(self):
        with self.assertRaises(ValueError):
            packet.summarize(pr("invalid"), changed())

    def test_injection_path_rejected(self):
        with self.assertRaises(ValueError):
            packet.summarize(pr(), changed("bad\n| path"))

    def test_empty_file_set_rejected(self):
        with self.assertRaises(ValueError):
            packet.summarize(pr(), [])

    def test_paginated_files(self):
        calls = []
        def getter(url):
            calls.append(url)
            return changed() * 100 if url.endswith("&page=1") else changed()
        files = packet.fetch_files("leandroclf/product-platform", 2, getter)
        self.assertEqual(len(files), 101)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
