"""Offline safety contract for the independent-review gate."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("gate", Path(__file__).resolve().parents[1] / "scripts" / "agent_review_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class GateTests(unittest.TestCase):
    def run_gate(self, *, reviewer="trusted-bot", state="APPROVED", commit="head123", filename="src/app.py", trusted="trusted-bot", author="executor", pr_head="head123"):
        def fake_api(path):
            if path.endswith("/pulls/7"):
                return {"head": {"sha": pr_head}, "user": {"login": author}}
            if "/files?" in path:
                return [{"filename": filename}]
            if "/reviews?" in path:
                return [{"state": state, "commit_id": commit, "user": {"login": reviewer}}]
            raise AssertionError(path)
        env = {"GH_REPO": "owner/repo", "PR_NUMBER": "7", "HEAD_SHA": "head123", "TRUSTED_REVIEWERS": trusted}
        with patch.dict(os.environ, env), patch.object(gate, "api", fake_api):
            gate.main()

    def test_trusted_current_approval_passes(self):
        self.run_gate()

    def test_missing_allowlist_fails_closed(self):
        with self.assertRaises(SystemExit):
            self.run_gate(trusted="")

    def test_untrusted_reviewer_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_gate(reviewer="stranger")

    def test_self_approval_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_gate(author="trusted-bot")

    def test_stale_approval_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_gate(commit="old")

    def test_head_mismatch_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_gate(pr_head="new")

    def test_changes_requested_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_gate(state="CHANGES_REQUESTED")

    def test_workflow_change_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_gate(filename=".github/workflows/change.yml")

    def test_infra_change_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_gate(filename="infra/main.tf")

if __name__ == "__main__":
    unittest.main()
