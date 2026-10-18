"""Offline integrity checks for read-only ai-team request export."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

scripts = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location("verified_ai_team_handoff", scripts / "verified_ai_team_handoff.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from autonomy_backlog import prepare


def sample():
    task = {
        "source": "architecture",
        "target_repository": "leandroclf/product-platform",
        "problem": "Broken documentation link",
        "evidence_url": "https://github.com/leandroclf/product-platform/issues/12",
        "acceptance_criteria": ["Broken link corrected"],
        "risk": "R1",
        "rollback": "Revert documentation commit",
        "max_cycles": 2,
    }
    return prepare("```autonomy-task\n" + json.dumps(task) + "\n```",
                   "https://github.com/leandroclf/product-platform/issues/12")


class VerificationTests(unittest.TestCase):
    def test_valid_candidate_gives_inert_request(self):
        output = module.build_request(sample())
        self.assertEqual(output["mode"], "MANUAL_IMPORT_ONLY")
        self.assertFalse(output["execution_allowed"])
        self.assertIn("Broken link corrected", output["ai_team_request"])

    def test_tampering_with_task_detected(self):
        preview = sample()
        preview["task"]["problem"] = "Changed after triage"
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            module.build_request(preview)

    def test_refuse_execution_override(self):
        preview = sample()
        preview["execution_allowed"] = True
        with self.assertRaises(ValueError):
            module.build_request(preview)

    def test_refuse_extra_fields(self):
        preview = sample()
        preview["shell"] = "echo unsafe"
        with self.assertRaises(ValueError):
            module.build_request(preview)

    def test_refuse_high_risk_even_with_rehashed_task(self):
        preview = sample()
        preview["task"]["risk"] = "R3"
        with self.assertRaises(ValueError):
            module.build_request(preview)

    def test_refuse_changed_status(self):
        preview = sample()
        preview["status"] = "ready"
        with self.assertRaises(ValueError):
            module.build_request(preview)


if __name__ == "__main__":
    unittest.main()
