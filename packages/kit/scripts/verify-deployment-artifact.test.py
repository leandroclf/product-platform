"""Independent offline G6 release evidence checks; no real deploy or credentials."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("g6_artifact", ROOT / "scripts/verify-deployment-artifact.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
contract_spec = importlib.util.spec_from_file_location("g6_contract_tests", ROOT / "scripts/validate-deployment-plan.test.py")
contracts = importlib.util.module_from_spec(contract_spec)
contract_spec.loader.exec_module(contracts)


class DeploymentArtifactEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.repo = self.path / "source"
        self.repo.mkdir()
        def git(*args):
            return subprocess.run(["git", "-C", str(self.repo), *args],
                                  capture_output=True, text=True, check=True).stdout.strip()
        git("init", "-q")
        git("config", "user.email", "test@example.invalid")
        git("config", "user.name", "Test")
        (self.repo / "file.txt").write_text("reviewed source")
        git("add", "file.txt")
        git("commit", "-qm", "test baseline")
        self.sha = git("rev-parse", "HEAD")
        self.artifact = self.path / "release.tgz"
        self.artifact.write_bytes(b"offline-artifact-bytes")
        self.digest = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.plan = contracts.valid("staging")
        self.plan["source_sha"] = self.sha
        self.plan["artifact_sha256"] = self.digest
        self.plan["artifact_ref"] = "artifact@sha256:" + self.digest
        self.plan["evidence"]["source_sha"] = self.sha
        self.plan["evidence"]["artifact_sha256"] = self.digest
        self.plan_path = self.path / "plan.json"
        self.write_plan()

    def write_plan(self):
        self.plan_path.write_text(json.dumps(self.plan))

    def test_checks_actual_git_head_and_artifact_bytes_without_authorization(self):
        result = verifier.assess(self.plan_path, self.repo, self.artifact)
        self.assertEqual(result["source_sha"], self.sha)
        self.assertEqual(result["artifact_sha256"], self.digest)
        self.assertEqual(result["decision"], "ARTIFACT_AND_SOURCE_VERIFIED")
        self.assertFalse(result["authorized_to_deploy"])
        self.assertFalse(result["approval_identity_verified"])
        self.assertFalse(result["checks_provider_verified"])

    def test_tampered_artifact_rejected(self):
        self.artifact.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "artifact SHA"):
            verifier.assess(self.plan_path, self.repo, self.artifact)

    def test_wrong_source_sha_rejected(self):
        self.plan["source_sha"] = "f" * 40
        self.plan["evidence"]["source_sha"] = "f" * 40
        self.write_plan()
        with self.assertRaisesRegex(ValueError, "source SHA"):
            verifier.assess(self.plan_path, self.repo, self.artifact)

    def test_dirty_checkout_rejected(self):
        (self.repo / "file.txt").write_text("uncommitted change")
        with self.assertRaisesRegex(ValueError, "tracked repository"):
            verifier.assess(self.plan_path, self.repo, self.artifact)

    def test_artifact_symlink_rejected(self):
        alias = self.path / "alias.tgz"
        alias.symlink_to(self.artifact)
        with self.assertRaisesRegex(ValueError, "linked"):
            verifier.assess(self.plan_path, self.repo, alias)

    def test_missing_or_malformed_evidence_rejected(self):
        self.plan["approval"] = "not-an-approval"
        self.write_plan()
        with self.assertRaisesRegex(ValueError, "G6 plan blocked"):
            verifier.assess(self.plan_path, self.repo, self.artifact)

    def ci_env(self):
        return {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "push",
                "GITHUB_REF": "refs/heads/main", "GITHUB_REPOSITORY": "leandroclf/vehicle-tracking",
                "GITHUB_RUN_ID": "123456", "GITHUB_WORKSPACE": str(self.repo),
                "GITHUB_SHA": self.sha}

    def test_main_push_ci_context_and_real_artifact_pass_without_deploy_permission(self):
        result = ci_gate.assess(self.plan_path, self.repo, self.artifact,
                                "leandroclf/vehicle-tracking", self.ci_env())
        self.assertEqual(result["decision"], "CI_CONTEXT_AND_ARTIFACT_VERIFIED")
        self.assertFalse(result["authorized_to_deploy"])
        self.assertFalse(result["approval_identity_verified"])

    def test_ci_rejects_fork_pr_wrong_sha_ref_repository_and_workspace(self):
        invalid = [
            ("GITHUB_EVENT_NAME", "pull_request"),
            ("GITHUB_REF", "refs/heads/feature"),
            ("GITHUB_REPOSITORY", "attacker/fork"),
            ("GITHUB_SHA", "d" * 40),
            ("GITHUB_WORKSPACE", str(self.path)),
            ("GITHUB_RUN_ID", "none"),
            ("GITHUB_ACTIONS", "false"),
        ]
        for name, value in invalid:
            with self.subTest(name=name):
                env = self.ci_env()
                env[name] = value
                with self.assertRaises(ValueError):
                    ci_gate.assess(self.plan_path, self.repo, self.artifact,
                                   "leandroclf/vehicle-tracking", env)

    def test_ci_rejects_modified_artifact_even_in_valid_push(self):
        self.artifact.write_bytes(b"modified after build")
        with self.assertRaisesRegex(ValueError, "artifact SHA"):
            ci_gate.assess(self.plan_path, self.repo, self.artifact,
                           "leandroclf/vehicle-tracking", self.ci_env())

    def test_cli_emits_redacted_block_without_authority(self):
        cmd = [sys.executable, str(ROOT / "scripts/verify-deployment-artifact.py"),
               "--plan", str(self.plan_path), "--checkout", str(self.repo),
               "--artifact", str(self.artifact)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["authorized_to_deploy"])
        self.artifact.write_bytes(b"tampered")
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["decision"], "BLOCK")
        self.assertNotIn(str(self.path), result.stdout)


if __name__ == "__main__":
    unittest.main()
