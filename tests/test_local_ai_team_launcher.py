"""Offline checks for the local ai-team launcher."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

scripts = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(scripts))
from autonomy_backlog import prepare
spec = importlib.util.spec_from_file_location("launcher", scripts / "local_ai_team_launcher.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def candidate():
    task = {
        "source": "architecture", "target_repository": "leandroclf/product-platform",
        "problem": "Correct an outdated link",
        "evidence_url": "https://github.com/leandroclf/product-platform/issues/12",
        "acceptance_criteria": ["Document link resolves"], "risk": "R1",
        "rollback": "Revert documentation commit", "max_cycles": 2,
    }
    return prepare("~~~\n".replace("~~~", "\u0060\u0060\u0060autonomy-task") +
                   json.dumps(task) + "\n" + "\u0060\u0060\u0060",
                   "https://github.com/leandroclf/product-platform/issues/12")


def live_issue(preview=None, state="open", labeled=True):
    preview = preview or candidate()
    task = preview["task"]
    return {
        "number": 12, "state": state,
        "labels": [{"name": "agent-candidate"}] if labeled else [],
        "html_url": preview["issue_url"],
        "body": "\u0060\u0060\u0060autonomy-task\n" + json.dumps(task) + "\n\u0060\u0060\u0060",
    }


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.calls = []

    def fake(self, argv, cwd):
        self.calls.append(argv)
        if argv[:3] == ["git", "rev-parse", "--show-toplevel"]:
            return str(self.root)
        if argv[:3] == ["git", "remote", "get-url"]:
            return "git@github.com:leandroclf/product-platform.git"
        if argv[:2] == ["git", "status"]:
            return ""
        if argv[:2] == ["git", "symbolic-ref"]:
            return "feature/issue"
        if argv[:2] == ["ai-team", "doctor"]:
            return "OK"
        if argv[:2] == ["ai-team", "run"]:
            return "REVIEWED"
        raise AssertionError(argv)

    def test_preview_does_not_invoke_ai_team(self):
        p = module.plan(candidate(), self.root, run=self.fake)
        self.assertFalse(p["execution_allowed"])
        self.assertFalse(any(x[0] == "ai-team" for x in self.calls))

    def test_rejects_wrong_origin(self):
        def fake(argv, cwd):
            if argv[:3] == ["git", "remote", "get-url"]:
                return "git@github.com:attacker/other.git"
            return self.fake(argv, cwd)
        with self.assertRaises(ValueError):
            module.plan(candidate(), self.root, run=fake)

    def test_rejects_dirty_checkout(self):
        def fake(argv, cwd):
            if argv[:2] == ["git", "status"]:
                return " M README.md"
            return self.fake(argv, cwd)
        with self.assertRaises(ValueError):
            module.plan(candidate(), self.root, run=fake)

    def test_rejects_wrong_hash_without_running(self):
        with patch.object(module.shutil, "which", return_value="/usr/bin/ai-team"):
            with self.assertRaises(ValueError):
                module.execute(candidate(), self.root, "wrong", run=self.fake,
                               get_issue=lambda _: live_issue())
        self.assertFalse(any(x[0] == "ai-team" for x in self.calls))

    def test_explicit_confirmation_runs_doctor_then_ai_team(self):
        verified = module.build_request(candidate())
        with patch.object(module.shutil, "which", return_value="/usr/bin/ai-team"):
            result = module.execute(candidate(), self.root, verified["task_sha256"], run=self.fake,
                                    get_issue=lambda _: live_issue())
        self.assertEqual(result, "REVIEWED")
        self.assertIn(["ai-team", "doctor"], self.calls)
        self.assertTrue(any(x[:2] == ["ai-team", "run"] for x in self.calls))

    def test_execute_blocks_closed_issue_before_doctor(self):
        preview = candidate()
        digest = module.build_request(preview)["task_sha256"]
        with patch.object(module.shutil, "which", return_value="/usr/bin/ai-team"):
            with self.assertRaises(ValueError):
                module.execute(preview, self.root, digest, run=self.fake,
                               get_issue=lambda _: live_issue(preview, state="closed"))
        self.assertFalse(any(args[0] == "ai-team" for args in self.calls))

    def test_execute_blocks_candidate_label_removed(self):
        preview = candidate()
        digest = module.build_request(preview)["task_sha256"]
        with patch.object(module.shutil, "which", return_value="/usr/bin/ai-team"):
            with self.assertRaises(ValueError):
                module.execute(preview, self.root, digest, run=self.fake,
                               get_issue=lambda _: live_issue(preview, labeled=False))
        self.assertFalse(any(args[0] == "ai-team" for args in self.calls))

    def test_execute_blocks_changed_task_body(self):
        preview = candidate()
        digest = module.build_request(preview)["task_sha256"]
        altered = live_issue(preview)
        altered["body"] = altered["body"].replace("outdated link", "different link")
        with patch.object(module.shutil, "which", return_value="/usr/bin/ai-team"):
            with self.assertRaisesRegex(ValueError, "changed"):
                module.execute(preview, self.root, digest, run=self.fake,
                               get_issue=lambda _: altered)
        self.assertFalse(any(args[0] == "ai-team" for args in self.calls))

    def test_execute_rechecks_after_doctor_before_run(self):
        preview = candidate()
        digest = module.build_request(preview)["task_sha256"]
        calls = []
        def issue_reader(_):
            calls.append(True)
            return live_issue(preview, state="open" if len(calls) == 1 else "closed")
        with patch.object(module.shutil, "which", return_value="/usr/bin/ai-team"):
            with self.assertRaises(ValueError):
                module.execute(preview, self.root, digest, run=self.fake, get_issue=issue_reader)
        self.assertEqual(len(calls), 2)
        self.assertIn(["ai-team", "doctor"], self.calls)
        self.assertFalse(any(args[:2] == ["ai-team", "run"] for args in self.calls))

    def test_execute_fails_closed_if_issue_query_unavailable(self):
        preview = candidate()
        digest = module.build_request(preview)["task_sha256"]
        def denied(_):
            raise OSError("GitHub temporarily unavailable")
        with patch.object(module.shutil, "which", return_value="/usr/bin/ai-team"):
            with self.assertRaises(OSError):
                module.execute(preview, self.root, digest, run=self.fake, get_issue=denied)
        self.assertFalse(any(args[0] == "ai-team" for args in self.calls))

    def test_rejects_tampering_before_git(self):
        p = candidate()
        p["execution_allowed"] = True
        with self.assertRaises(ValueError):
            module.plan(p, self.root, run=self.fake)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
