"""No integrator token for stale, foreign, draft or non-opt-in PRs."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("candidate", SCRIPTS / "agent_merge_candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.pr = {"number": 7, "state": "open", "draft": False,
                   "head": {"sha": "a" * 40, "repo": {"full_name": "owner/repo"}},
                   "base": {"ref": "main", "repo": {"full_name": "owner/repo"}},
                   "labels": [{"name": "agent-auto-merge"}]}
        self.event = {"repository": {"default_branch": "main"},
                      "pull_request": copy.deepcopy(self.pr), "inputs": {"pr_number": "7"},
                      "workflow_run": {"conclusion": "success",
                                       "path": ".github/workflows/agent-review-gate.yml",
                                       "head_repository": {"full_name": "owner/repo"},
                                       "pull_requests": [copy.deepcopy(self.pr)]}}

    def resolve(self, name="workflow_run"):
        with patch.object(candidate, "api", return_value=self.pr) as api:
            result = candidate.resolve(self.event, "owner/repo", name)
            api.assert_called_once_with("repos/owner/repo/pulls/7")
            return result

    def test_supported_triggers_resolve_current_candidate(self):
        for name in ("workflow_run", "pull_request_target", "workflow_dispatch"):
            with self.subTest(trigger=name):
                self.assertEqual(self.resolve(name), (7, "a" * 40))

    def test_stale_events_rejected(self):
        self.pr["head"]["sha"] = "b" * 40
        for name in ("workflow_run", "pull_request_target"):
            with self.subTest(trigger=name), self.assertRaises(ValueError):
                self.resolve(name)

    def test_ineligible_live_prs_rejected(self):
        original = copy.deepcopy(self.pr)
        cases = [{"draft": True}, {"state": "closed"}, {"labels": []},
                 {"head": {"sha": "a" * 40, "repo": {"full_name": "foreign/repo"}}},
                 {"base": {"ref": "other", "repo": {"full_name": "owner/repo"}}}]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.pr = {**original, **changes}
                self.resolve()

    def test_failed_foreign_and_wrong_workflow_runs_rejected(self):
        original = copy.deepcopy(self.event["workflow_run"])
        for changes in ({"conclusion": "failure"}, {"path": ".github/workflows/untrusted.yml"},
                        {"head_repository": {"full_name": "foreign/repo"}}, {"pull_requests": []}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.event["workflow_run"] = {**original, **changes}
                self.resolve()

    def test_dispatch_does_not_accept_shell_input(self):
        self.event["inputs"]["pr_number"] = "7; false"
        with self.assertRaises(ValueError):
            self.resolve("workflow_dispatch")

    def test_unknown_event_rejected(self):
        with self.assertRaises(ValueError):
            self.resolve("pull_request_review")


if __name__ == "__main__":
    unittest.main()
