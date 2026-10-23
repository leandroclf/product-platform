"""Security invariants for the privileged auto-merge workflow."""
from pathlib import Path
import re
import unittest


WORKFLOW = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "agent-auto-merge.yml").read_text()


class AgentAutoMergeWorkflowTests(unittest.TestCase):
    def test_privileged_workflow_uses_trusted_triggers(self):
        self.assertRegex(WORKFLOW, r"(?m)^  pull_request_target:")
        self.assertNotRegex(WORKFLOW, r"(?m)^  pull_request:")
        self.assertNotRegex(WORKFLOW, r"(?m)^  pull_request_review:")
        self.assertIn("workflows: [Agent independent review gate]", WORKFLOW)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", WORKFLOW)
        self.assertRegex(WORKFLOW, r"(?m)^  workflow_dispatch:")

    def test_checkout_pins_trusted_default_branch(self):
        pins = re.findall(r"(?m)^\s*- uses:\s*actions/checkout@([0-9a-f]{40})(?:\s|$)", WORKFLOW)
        self.assertEqual(len(pins), 1, "Privileged checkout must use exactly one immutable full SHA pin")
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", WORKFLOW)
        self.assertNotIn("github.event.pull_request.head.sha }}", WORKFLOW.split("actions/checkout", 1)[1].split("- name: Verify", 1)[0])

    def test_app_token_is_created_only_after_gate_and_scoped_to_pr_write(self):
        self.assertLess(WORKFLOW.index("run: python3 scripts/agent_merge_candidate.py"), WORKFLOW.index("python3 scripts/agent_review_gate.py"))
        self.assertLess(WORKFLOW.index("python3 scripts/agent_review_gate.py"), WORKFLOW.index("id: integrator-token"))
        pins = re.findall(r"(?m)^\s*uses:\s*actions/create-github-app-token@([0-9a-f]{40})(?:\s|$)", WORKFLOW)
        self.assertEqual(len(pins), 1, "GitHub App token action must use exactly one immutable full SHA pin")
        self.assertIn("repositories: product-platform", WORKFLOW)
        self.assertIn("permission-pull-requests: write", WORKFLOW)
        self.assertIn("permission-contents: write", WORKFLOW)
        self.assertIn("environment: agent-integration", WORKFLOW)
        self.assertIn("github.ref == format('refs/heads/{0}', github.event.repository.default_branch)", WORKFLOW)
        self.assertEqual(WORKFLOW.count("if: steps.candidate.outputs.eligible == 'true'"), 3)
        self.assertNotIn("secrets.AGENT_MERGE_TOKEN", WORKFLOW)
        self.assertNotIn("ALLOW_SECURITY_REVIEW", WORKFLOW)
        self.assertNotIn("SECURITY_REVIEWERS", WORKFLOW)
        self.assertIn('--match-head-commit "$HEAD_SHA"', WORKFLOW)
        self.assertIn("HEAD_SHA: ${{ steps.candidate.outputs.head }}", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
