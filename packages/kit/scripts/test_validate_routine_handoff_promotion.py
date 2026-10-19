"""Tests for Routine Finding -> PlatformHandoff promotion boundaries."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).with_name("validate-routine-handoff-promotion.py")
spec = importlib.util.spec_from_file_location("promotion", path)
promotion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promotion)

URL = "https://github.com/leandroclf/product-platform/issues/69"
SHA = "a" * 40

def packet():
    return {"kind": "routine-finding-triage-packet", "status": "ready_for_proposal_review",
            "source_issue": URL, "target_repository": "leandroclf/product-platform",
            "acceptance_criteria": ["README updated"]}

def envelope():
    return {"schema_version": "1.0", "proposal": {
        "proposal_id": "issue-69", "repository": {"url": "https://github.com/leandroclf/product-platform",
                                                 "base_ref": "main", "base_sha": SHA},
        "objective": "Align documentation. Source: " + URL,
        "acceptance": {"criteria": ["README updated"]}}}

class Tests(unittest.TestCase):
    @patch.object(promotion, "load_validator")
    def test_valid_after_kit_approval(self, mock):
        mock.return_value.REGISTRY = Path("registry")
        mock.return_value.violations.return_value = []
        receipt = promotion.check(packet(), envelope())
        self.assertEqual(receipt["result"], "valid_for_manual_execution_review")
        mock.return_value.violations.assert_called_once()

    def test_unapproved(self):
        p = packet(); p["status"] = "new"
        with self.assertRaises(ValueError):
            promotion.check(p, envelope())

    def test_repo_mismatch(self):
        e = envelope(); e["proposal"]["repository"]["url"] = "https://github.com/elsewhere/repo"
        with self.assertRaises(ValueError):
            promotion.check(packet(), e)

    def test_missing_base_sha(self):
        e = envelope(); e["proposal"]["repository"].pop("base_sha")
        with self.assertRaises(ValueError):
            promotion.check(packet(), e)

    def test_missing_issue_provenance(self):
        e = envelope(); e["proposal"]["objective"] = "Align documentation"
        with self.assertRaises(ValueError):
            promotion.check(packet(), e)

    def test_missing_acceptance(self):
        e = envelope(); e["proposal"]["acceptance"]["criteria"] = ["different"]
        with self.assertRaises(ValueError):
            promotion.check(packet(), e)

    @patch.object(promotion, "load_validator")
    def test_kit_rejection(self, mock):
        mock.return_value.REGISTRY = Path("registry")
        mock.return_value.violations.return_value = ["invalid registry fingerprint"]
        with self.assertRaisesRegex(ValueError, "Kit G1 rejected"):
            promotion.check(packet(), envelope())

if __name__ == "__main__":
    unittest.main()
