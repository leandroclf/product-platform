"""Security regression tests for the shared read-only G6 promotion contract."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("deployment_contract", ROOT / "scripts/validate-deployment-plan.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def valid(environment="production"):
    checks = dict.fromkeys(gate.CHECKS, True)
    source, digest, rollback = "a" * 40, "b" * 64, "c" * 64
    evidence = dict(source_sha=source, artifact_sha256=digest,
                    checks_sha=gate.checks_hash(checks),
                    checked_environment=environment,
                    approved_by="release-operator" if environment == "production" else None,
                    approved_source_sha=source if environment == "production" else None,
                    approved_artifact_sha256=digest if environment == "production" else None,
                    approved_environment=environment if environment == "production" else None,
                    rollback_artifact_sha256=rollback if environment != "preview" else None)
    return dict(schema_version="1.0", product="vehicle-tracking", source_sha=source,
                artifact_sha256=digest, artifact_ref="ghcr.io/example/vehicle@sha256:" + digest,
                environment=environment, previous_artifact_sha256=rollback if environment != "preview" else None,
                checks=checks, approval="approved" if environment == "production" else "pending",
                evidence=evidence)


class DeploymentContractTests(unittest.TestCase):
    def test_all_environment_plans_are_structurally_reviewable_not_authorized(self):
        for env in gate.ENVIRONMENTS:
            with self.subTest(env=env):
                self.assertEqual(gate.errors(valid(env)), [])

    def test_rejects_missing_checks_and_failed_quality_health(self):
        for check in gate.CHECKS:
            p = valid()
            p["checks"][check] = False
            with self.subTest(check=check):
                self.assertTrue(gate.errors(p), check)

    def test_prod_approval_must_bind_exact_sha_digest_and_environment(self):
        for key, replacement in (
            ("approved_by", None), ("approved_source_sha", "d" * 40),
            ("approved_artifact_sha256", "d" * 64), ("approved_environment", "staging")):
            p = valid()
            p["evidence"][key] = replacement
            with self.subTest(key=key):
                self.assertTrue(gate.errors(p))

    def test_rejects_mismatched_evidence_and_rollback(self):
        for key, replacement in (
            ("source_sha", "d" * 40), ("artifact_sha256", "d" * 64),
            ("checks_sha", "d" * 64), ("checked_environment", "preview"),
            ("rollback_artifact_sha256", "d" * 64)):
            p = valid()
            p["evidence"][key] = replacement
            with self.subTest(key=key):
                self.assertTrue(gate.errors(p))

    def test_prod_needs_rollback_and_distinct_candidate(self):
        p = valid()
        p["previous_artifact_sha256"] = None
        self.assertTrue(gate.errors(p))
        p = valid()
        p["previous_artifact_sha256"] = p["artifact_sha256"]
        self.assertTrue(gate.errors(p))

    def test_invalid_unknown_fields_and_floating_artifacts(self):
        cases = [
            dict(valid(), extra=True),
            dict(valid(), artifact_ref="repo:latest"),
            dict(valid(), artifact_ref="repo/$(curl bad)"),
            dict(valid(), source_sha="main"),
            dict(valid(), approval="auto"),
        ]
        for index, p in enumerate(cases):
            with self.subTest(index=index):
                self.assertTrue(gate.errors(p))

    def test_cli_fails_closed_and_never_calls_cloud(self):
        script = str(ROOT / "scripts/validate-deployment-plan.py")
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "valid.json"
            bad = Path(tmp) / "bad.json"
            good.write_text(json.dumps(valid()))
            p = valid()
            p["approval"] = "pending"
            bad.write_text(json.dumps(p))
            def run(path):
                return subprocess.run([sys.executable, script, str(path)], capture_output=True, text=True)
            ok = run(good)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertFalse(json.loads(ok.stdout)["authorized_to_deploy"])
            self.assertEqual(json.loads(ok.stdout)["decision"], "READY_FOR_OPERATOR_REVIEW")
            self.assertEqual(run(bad).returncode, 1)
            self.assertEqual(run(Path(tmp) / "missing.json").returncode, 2)
            link = Path(tmp) / "linked.json"
            link.symlink_to(good)
            self.assertEqual(run(link).returncode, 2)


if __name__ == "__main__":
    unittest.main()
