"""Security invariants for the privileged auto-merge workflow."""
from pathlib import Path
import unittest


WORKFLOW = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "agent-auto-merge.yml").read_text()


class AgentAutoMergeWorkflowTests(unittest.TestCase):
    def test_privileged_workflow_uses_pull_request_target_only(self):
        self.assertRegex(WORKFLOW, r"(?m)^  pull_request_target:")
        self.assertNotRegex(WORKFLOW, r"(?m)^  pull_request:")
        self.assertNotRegex(WORKFLOW, r"(?m)^  pull_request_review:")

    def test_checkout_pins_trusted_default_branch(self):
        self.assertIn("actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803", WORKFLOW)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", WORKFLOW)
        self.assertNotIn("github.event.pull_request.head.sha }}", WORKFLOW.split("actions/checkout", 1)[1].split("- name: Verify", 1)[0])

    def test_app_token_is_created_only_after_gate_and_scoped_to_pr_write(self):
        self.assertLess(WORKFLOW.index("run: python3 scripts/agent_review_gate.py"), WORKFLOW.index("id: integrator-token"))
        self.assertIn("actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1", WORKFLOW)
        self.assertIn("repositories: product-platform", WORKFLOW)
        self.assertIn("permission-pull-requests: write", WORKFLOW)
        self.assertNotIn("secrets.AGENT_MERGE_TOKEN", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
