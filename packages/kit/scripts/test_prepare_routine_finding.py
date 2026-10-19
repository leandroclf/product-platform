"""Regression checks for the guarded Routine Finding triage packet."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("prepare-routine-finding.py")
spec = importlib.util.spec_from_file_location("routine_finding_triage", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

FINDING = """```yaml
routine_finding:
  schema_version: 1
  finding_id: "leandroclf/product-platform:architecture:package-catalog-documentation-drift"
  source_routine: "Arquitetura, Agentes e Skills"
  target_repository: "leandroclf/product-platform"
  category: "architecture"
  severity: "low"
  observed_ref: "unknown"
  observed_at: "2026-10-18T22:00:00-03:00"
  evidence_urls:
    - "https://github.com/leandroclf/product-platform/blob/main/README.md"
  recommendation: "Align docs"
  acceptance_criteria:
    - "Documentation matches manifest"
  state: accepted
```"""

def issue(body=FINDING, state="OPEN"):
    return {"body": body, "state": state, "url": "https://github.com/leandroclf/product-platform/issues/69"}

class TriageTest(unittest.TestCase):
    def test_accepted_finding_prepares_review_only_packet(self):
        packet = module.prepare(issue(), "leandroclf/product-platform")
        self.assertEqual(packet["status"], "ready_for_proposal_review")
        self.assertIn("not execute ai-team", packet["next_step"])

    def test_unaccepted_finding_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "accepted"):
            module.prepare(issue(FINDING.replace("state: accepted", "state: new")), "leandroclf/product-platform")

    def test_wrong_repository_is_blocked(self):
        with self.assertRaises(ValueError):
            module.prepare(issue(), "leandroclf/vehicle-tracking")

    def test_closed_issue_is_blocked(self):
        with self.assertRaises(ValueError):
            module.prepare(issue(state="CLOSED"), "leandroclf/product-platform")

    def test_missing_evidence_is_blocked(self):
        with self.assertRaises(ValueError):
            module.prepare(issue(FINDING.replace("    - \"https://github.com/leandroclf/product-platform/blob/main/README.md\"", "    - \"https://evil.example/test\"")), "leandroclf/product-platform")

if __name__ == "__main__":
    unittest.main()
