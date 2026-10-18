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
        return {"secrets": [{"name": "PORTFOLIO_READ_TOKEN"}, {"name": "AGENT_MERGE_TOKEN"}]}
    if "/actions/variables?" in path:
        return {"variables": [{"name": "AGENT_TRUSTED_REVIEWERS", "value": "trusted-reviewer[bot]"}]}
    if path.endswith("/branches/main/protection"):
        return {"required_pull_request_reviews": {
            "required_approving_review_count": 1, "dismiss_stale_reviews": True
        }, "required_status_checks": {"contexts": ["independent-review-gate"]}}
    if "/rulesets?" in path:
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


if __name__ == "__main__":
    unittest.main()
