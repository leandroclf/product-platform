"""Readiness audits fail closed without administrative evidence."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "audit", Path(__file__).resolve().parents[1] / "scripts" / "audit_autonomy_readiness.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fake_get(path):
    if path == "repos/leandroclf/product-platform":
        return {"allow_auto_merge": True}
    if "/actions/secrets?" in path:
        return {"secrets": [{"name": "INTEGRATOR_APP_PRIVATE_KEY"}]}
    if "/actions/variables?" in path:
        return {"variables": [{"name": "AGENT_TRUSTED_REVIEWERS", "value": "trusted-reviewer[bot]"},
                              {"name": "INTEGRATOR_APP_ID", "value": "123"},
                              {"name": "AGENT_REVIEW_MODE", "value": "independent"}]}
    if path.endswith("/branches/main/protection"):
        return {"required_pull_request_reviews": {
            "required_approving_review_count": 1, "dismiss_stale_reviews": True
        }, "required_status_checks": {"contexts": ["independent-review-gate"]}}
    if "/rulesets?" in path:
        return []
    if path.endswith("/rules/branches/main"):
        return []
    raise AssertionError(path)


class AuditTests(unittest.TestCase):
    def test_settings_do_not_certify_operational_readiness(self):
        report = audit.assess("leandroclf/product-platform", fake_get)
        self.assertFalse(report["ready_for_autonomous_merge"])
        self.assertEqual(next(x["state"] for x in report["checks"] if x["name"] == "auto_merge_enabled"), "pass")
        self.assertEqual(next(x["state"] for x in report["checks"] if x["name"] == "real_end_to_end_pilot"), "unknown")

    def test_api_denied_results_unknown_not_success(self):
        def denied(_):
            raise PermissionError("Forbidden")
        report = audit.assess("leandroclf/product-platform", denied)
        self.assertFalse(report["ready_for_autonomous_merge"])
        self.assertTrue(all(x["state"] == "unknown" for x in report["checks"]))

    def test_disabled_merge_fails(self):
        def disabled(path):
            result = fake_get(path)
            if path == "repos/leandroclf/product-platform":
                result = {"allow_auto_merge": False}
            return result
        report = audit.assess("leandroclf/product-platform", disabled)
        self.assertEqual(next(x["state"] for x in report["checks"] if x["name"] == "auto_merge_enabled"), "fail")

    def test_missing_reviewer_variable_fails(self):
        def missing(path):
            if "/actions/variables?" in path:
                return {"variables": []}
            return fake_get(path)
        report = audit.assess("leandroclf/product-platform", missing)
        self.assertEqual(next(x["state"] for x in report["checks"] if x["name"] == "variable:AGENT_TRUSTED_REVIEWERS"), "fail")

    def test_effective_rulesets_work_without_legacy_protection(self):
        def rules(path):
            if path.endswith("/branches/main/protection"):
                raise PermissionError("No legacy branch protection")
            if path.endswith("/rules/branches/main"):
                return [{"type": "pull_request", "parameters": {
                    "required_approving_review_count": 1, "dismiss_stale_reviews_on_push": True}},
                    {"type": "required_status_checks", "parameters": {
                        "required_status_checks": [{"context": "independent-review-gate"}]}}]
            return fake_get(path)
        states = {c["name"]: c["state"] for c in audit.assess("leandroclf/product-platform", rules)["checks"]}
        for name in ("required_pr_review", "stale_reviews_dismissed", "independent_review_check"):
            self.assertEqual(states[name], "pass")

    def test_integrator_metadata_matches_app_workflow(self):
        states = {c["name"]: c["state"] for c in audit.assess("leandroclf/product-platform", fake_get)["checks"]}
        self.assertEqual(states["secret_metadata:INTEGRATOR_APP_PRIVATE_KEY"], "pass")
        self.assertNotIn("secret_metadata:AGENT_MERGE_TOKEN", states)
        self.assertNotIn("secret_metadata:PORTFOLIO_READ_TOKEN", states)

    def test_manual_mode_is_not_ready(self):
        def manual(path):
            result = fake_get(path)
            if "/actions/variables?" in path:
                for variable in result["variables"]:
                    if variable["name"] == "AGENT_REVIEW_MODE":
                        variable["value"] = "manual"
            return result
        states = {c["name"]: c["state"] for c in audit.assess("leandroclf/product-platform", manual)["checks"]}
        self.assertEqual(states["variable:AGENT_REVIEW_MODE"], "fail")


if __name__ == "__main__":
    unittest.main()
