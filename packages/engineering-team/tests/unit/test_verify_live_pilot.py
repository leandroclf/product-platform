"""Offline verifier tests: simulated artifacts are never claimed authenticated."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts import local_team, verify_live_pilot


class LivePilotEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / ("a" * 32)
        self.path.mkdir()

    def write(self, name, value):
        (self.path / name).write_text(json.dumps(value))

    def fixture(self):
        sha = "b" * 40
        plan = {
            "schema_version": "1.0.0", "base_sha": "c" * 40,
            "status": "READY", "risk": "R1", "objective": "Fix reference",
            "out_of_scope": [], "assumptions": [], "validation": ["tests"],
            "tasks": [{"id": "T1", "description": "Fix", "acceptance_ids": ["AC1"]}],
            "acceptance_criteria": [{"id": "AC1", "description": "Reference fixed"}],
            "capability_decisions": [],
        }
        pid = local_team.plan_id(plan)
        runs = []
        for stage, (agent, provider) in local_team.STAGES.items():
            runs.append({"stage": stage, "cycle": 0, "agent": agent,
                         "provider": provider, "requested_model": "model",
                         "resolved_model": None, "started_at": 10, "ended_at": 12})
        self.write("state.json", {
            "status": "REVIEWED", "head_sha": sha, "cycle": 0,
            "plan": plan, "plan_id": pid, "stage_runs": runs,
        })
        self.write("0-tests.json", {"head_sha": sha, "exit_code": 0,
                                   "checks": ["python -m unittest"]})
        for stage in ("validate", "review"):
            self.write("0-" + stage + ".json", {
                "schema_version": "1.0.0", "reviewer": local_team.STAGES[stage][0],
                "head_sha": sha, "verdict": "PASS",
                "gates": {"quality": "PASS", "security": "PASS",
                          "architecture": "NOT_REQUESTED", "observability": "NOT_REQUESTED"},
                "findings": [], "checks_executed": ["python -m unittest"],
                "residual_risks": [], "plan_id": pid, "plan_status": "VALID",
                "acceptance_results": [{"id": "AC1", "status": "PASS",
                                        "evidence": "Tests and diff checked"}],
            })

    def test_structural_success_is_never_provider_certification(self):
        self.fixture()
        value = verify_live_pilot.assess(self.path)
        self.assertTrue(value["artifact_checks_pass"])
        self.assertFalse(value["authenticated_provider_execution_verified"])
        self.assertFalse(value["production_certified"])
        self.assertEqual(len(value["stage_summary"]), 4)
        self.assertTrue(all(not s["resolved_model_confirmed"] for s in value["stage_summary"]))

    def test_missing_stage_blocks(self):
        self.fixture()
        path = self.path / "state.json"
        state = json.loads(path.read_text())
        state["stage_runs"] = state["stage_runs"][:-1]
        self.write("state.json", state)
        self.assertFalse(verify_live_pilot.assess(self.path)["artifact_checks_pass"])

    def test_failed_tests_block(self):
        self.fixture()
        self.write("0-tests.json", {"head_sha": "b" * 40, "exit_code": 1,
                                    "checks": ["test"]})
        self.assertFalse(verify_live_pilot.assess(self.path)["artifact_checks_pass"])

    def test_stale_review_blocks(self):
        self.fixture()
        file = self.path / "0-review.json"
        data = json.loads(file.read_text())
        data["head_sha"] = "f" * 40
        self.write("0-review.json", data)
        self.assertFalse(verify_live_pilot.assess(self.path)["artifact_checks_pass"])

    def test_non_terminal_blocks(self):
        self.fixture()
        file = self.path / "state.json"
        data = json.loads(file.read_text())
        data["status"] = "FAILED"
        self.write("state.json", data)
        self.assertFalse(verify_live_pilot.assess(self.path)["artifact_checks_pass"])

    def test_symlinked_evidence_rejected(self):
        self.fixture()
        (self.path / "0-tests.json").unlink()
        (self.path / "0-tests.json").symlink_to(self.path / "state.json")
        self.assertFalse(verify_live_pilot.assess(self.path)["artifact_checks_pass"])

    def test_malformed_task_directory_rejected(self):
        with self.assertRaises(ValueError):
            verify_live_pilot.assess(self.path.parent)


if __name__ == "__main__":
    unittest.main()
