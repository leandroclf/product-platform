"""Fail-closed regression tests for nine-product brand/deployment composition."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("portfolio_guard", BASE / "scripts/validate-portfolio-brand-deploy.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.portfolio = json.loads((BASE / "contracts/portfolio-products.json").read_text())
        cls.deploy = json.loads((BASE / "contracts/portfolio-deployment-targets.json").read_text())
        cls.brand = json.loads((BASE / "contracts/lf-brand-source.json").read_text())

    def check(self, mutator):
        a, b, c = copy.deepcopy((self.portfolio, self.deploy, self.brand))
        mutator(a, b, c)
        self.assertTrue(guard.validate(a, b, c))

    def test_valid_portfolio(self):
        self.assertEqual(guard.validate(self.portfolio, self.deploy, self.brand), [])

    def test_flagship_portal_is_registered(self):
        self.assertEqual(self.portfolio["portal"]["repository"], "site-lf-solucoes")
        self.assertEqual(self.portfolio["portal"]["kind"], "flagship-product")
        self.assertEqual(self.deploy["flagship_portal"]["adapter"], "github-pages-static")

    def test_missing_portal_contract_rejected(self):
        self.check(lambda a, b, c: a.pop("portal"))

    def test_disabled_publication_requirement_rejected(self):
        self.check(lambda a, b, c: a["portal"].update(required_for_new_products=False))

    def test_unverified_auto_sync_cannot_be_claimed(self):
        self.check(lambda a, b, c: a["portal"].update(automatic_cross_repo_sync_verified=True))

    def test_missing_product_is_rejected(self):
        self.check(lambda a, b, c: b["targets"].pop())

    def test_duplicate_product_is_rejected(self):
        self.check(lambda a, b, c: b["targets"].append(dict(b["targets"][0])))

    def test_runtime_drift_rejected(self):
        self.check(lambda a, b, c: b["targets"][0].update(runtime="python-server"))

    def test_unverified_remote_deploy_rejected(self):
        self.check(lambda a, b, c: b["targets"][0].update(remote_deploy_verified=True))

    def test_automatic_production_authorization_rejected(self):
        self.check(lambda a, b, c: b["defaults"].update(deploy_authorized=True))

    def test_unverified_brand_color_rejected(self):
        self.check(lambda a, b, c: c["visual"].update(colors={"primary": "#ffffff"}))

    def test_brand_source_revision_and_digests_are_pinned(self):
        self.check(lambda a, b, c: c["source"].update(commit_sha="0" * 40))
        self.check(lambda a, b, c: c["source"]["files"]["assets/lf-logo-horizontal.svg"].update(sha256="0" * 64))

    def test_site_layout_is_not_promoted_to_shared_brand_grid(self):
        self.check(lambda a, b, c: c["visual"]["grid"].update(shared_brand_grid="approved"))

    def test_redistribution_and_product_adoption_remain_unapproved(self):
        self.check(lambda a, b, c: c["adoption"].update(redistribution_approved=True))
        self.check(lambda a, b, c: c["adoption"].update(product_adoption_approved=True))

    def test_remote_logo_hotlink_rejected(self):
        self.check(lambda a, b, c: c["adoption"].update(remote_asset_hotlink=True))

    def test_product_forced_rebrand_rejected(self):
        self.check(lambda a, b, c: c["adoption"].update(force_rebrand=True))


if __name__ == "__main__":
    unittest.main()
