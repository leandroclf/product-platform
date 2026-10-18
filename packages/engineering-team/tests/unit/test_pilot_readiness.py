import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import pilot_readiness as readiness


class PilotReadinessTests(unittest.TestCase):
    def test_missing_prerequisites_never_claims_pilot_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(readiness, "acl_canary", return_value=False):
                report = readiness.assess(Path(tmp) / "missing")
            self.assertFalse(report["ready_for_operator_authenticated_pilot"])
            self.assertFalse(report["provider_authenticated"])
            self.assertFalse(report["actual_inference_verified"])
            self.assertFalse(report["production_certified"])
            self.assertFalse(report["checks"]["git_checkout"])

    def test_valid_git_and_config_reports_readiness_but_not_authentication(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            config = {"repository": str(repo),
                      "provider_image": "provider@sha256:" + "a" * 64,
                      "test_image": "python:3.12",
                      "checks": ["python -m unittest"],
                      "models": readiness.team.DEFAULT_MODELS,
                      "quality_checks": {"api_contract": "python -m unittest tests.test_api"}}
            def fake_run(args, **kwargs):
                if args[:3] == ["git", "-C", str(repo)]:
                    action = args[3:]
                    if action[0] == "rev-parse":
                        value = str(repo) + "\n"
                    elif action[0] == "status":
                        value = ""
                    elif action[0] == "branch":
                        value = "pilot\n"
                    elif action[0] == "remote":
                        value = "git@github.com:leandroclf/product-platform.git\n"
                    else:
                        raise AssertionError(action)
                    return readiness.subprocess.CompletedProcess(args, 0, value, "")
                return readiness.subprocess.CompletedProcess(args, 0, "", "")
            with patch.object(readiness.sys, "platform", "linux"), \
                 patch.object(readiness.shutil, "which", return_value="/usr/bin/available"), \
                 patch.object(readiness, "acl_canary", return_value=True), \
                 patch.object(readiness.team, "home", return_value=Path(tmp)), \
                 patch.object(readiness.team, "read", return_value=config), \
                 patch.object(readiness.team, "validate_config", return_value=config), \
                 patch.object(readiness.subprocess, "run", side_effect=fake_run), \
                 patch.object(Path, "is_file", return_value=True):
                report = readiness.assess(repo)
            self.assertTrue(report["ready_for_operator_authenticated_pilot"], report["blockers"])
            self.assertFalse(report["provider_authenticated"])
            self.assertFalse(report["actual_inference_verified"])
            self.assertTrue(report["checks"]["config_valid"])
            self.assertFalse("repo" in json.dumps(report).lower())

    def test_acl_canary_denies_when_dependency_missing(self):
        with patch.object(readiness.shutil, "which", return_value=None):
            self.assertFalse(readiness.acl_canary())

    def test_acl_canary_requires_exact_scoped_grant(self):
        with patch.object(readiness.shutil, "which", return_value="/usr/bin/setfacl"), \
             patch.object(readiness, "command", return_value=True), \
             patch.object(readiness.subprocess, "run") as run:
            run.return_value = readiness.subprocess.CompletedProcess(
                ["getfacl"], 0, "user::rw-\nuser:1001:rw-\ngroup::---\nother::---\n", "")
            self.assertTrue(readiness.acl_canary())
            run.return_value = readiness.subprocess.CompletedProcess(
                ["getfacl"], 0, "user::rw-\ngroup::---\nother::---\n", "")
            self.assertFalse(readiness.acl_canary())


if __name__ == "__main__":
    unittest.main()
