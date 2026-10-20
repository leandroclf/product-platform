import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "portfolio_deployment_discovery", ROOT / "scripts/validate-portfolio-deployment-discovery.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
SNAPSHOT = json.loads((ROOT / "contracts/portfolio-deployment-discovery.json").read_text())
PORTFOLIO = json.loads((ROOT / "contracts/portfolio-products.json").read_text())
DEPLOYMENT = json.loads((ROOT / "contracts/portfolio-deployment-targets.json").read_text())


class DiscoveryContractTests(unittest.TestCase):
    def check(self, snapshot):
        return module.validate(snapshot, PORTFOLIO, DEPLOYMENT)

    def test_pinned_snapshot_covers_products_without_claiming_deployment(self):
        self.assertEqual(self.check(SNAPSHOT), [])

    def test_missing_or_duplicate_products_are_rejected(self):
        missing = copy.deepcopy(SNAPSHOT)
        missing["products"].pop()
        self.assertTrue(any("cover each portfolio product" in error for error in self.check(missing)))
        duplicate = copy.deepcopy(SNAPSHOT)
        duplicate["products"].append(copy.deepcopy(duplicate["products"][0]))
        self.assertTrue(any("cover each portfolio product" in error for error in self.check(duplicate)))

    def test_malformed_source_revision_and_blob_are_rejected(self):
        bad_commit = copy.deepcopy(SNAPSHOT)
        bad_commit["products"][0]["source"]["commit_sha"] = "main"
        self.assertTrue(any("pinned source revision" in error for error in self.check(bad_commit)))
        bad_blob = copy.deepcopy(SNAPSHOT)
        bad_blob["products"][0]["source"]["files"][0]["git_blob_sha1"] = "0" * 39
        self.assertTrue(any("source file evidence" in error for error in self.check(bad_blob)))

    def test_unverified_remote_state_cannot_be_promoted_to_verified(self):
        value = copy.deepcopy(SNAPSHOT)
        value["products"][0]["verification"]["remote_deploy"] = True
        errors = self.check(value)
        self.assertTrue(any("must remain false" in error for error in errors))

    def test_discovery_does_not_accept_invented_production_urls(self):
        value = copy.deepcopy(SNAPSHOT)
        value["products"][0]["declarations"]["production_url"] = "https://example.invalid"
        errors = self.check(value)
        self.assertTrue(any("must not invent endpoint URLs" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
