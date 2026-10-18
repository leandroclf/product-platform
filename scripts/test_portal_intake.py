import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("portal_pr_proposer", ROOT / "scripts/propose_portal_intake.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

REGISTRY = {
    "portal": {"repository": "site-lf-solucoes"},
    "products": [{"repository": "product-a", "domain": "example", "runtime": "python-server", "wave": 2},
                 {"repository": "product-b", "domain": "example-b", "runtime": "typescript-server", "wave": 3}],
}
CATALOG = {"products": [{"id": "product-a"}]}


class PortalIntakeTests(unittest.TestCase):
    def test_only_missing_product_is_proposed(self):
        p = mod.plan(REGISTRY, CATALOG)
        self.assertEqual([x["id"] for x in p], ["product-b"])
        self.assertEqual(p[0]["visibility"], "review-required")
        self.assertIsNone(p[0]["verified_public_url"])
        self.assertFalse(p[0]["editorial_approval"])

    def test_all_present_is_noop(self):
        cat = {"products": [{"id": "product-a"}, {"id": "product-b"}]}
        self.assertEqual(mod.plan(REGISTRY, cat), [])

    def test_duplicate_portal_entry_is_blocked(self):
        cat = {"products": [{"id": "product-a"}, {"id": "product-a"}]}
        with self.assertRaises(ValueError):
            mod.plan(REGISTRY, cat)

    def test_duplicate_registry_entry_is_blocked(self):
        reg = copy.deepcopy(REGISTRY)
        reg["products"].append(dict(reg["products"][0]))
        with self.assertRaises(ValueError):
            mod.plan(reg, CATALOG)

    def test_invalid_slug_is_blocked(self):
        reg = copy.deepcopy(REGISTRY)
        reg["products"][1]["repository"] = "../../evil"
        with self.assertRaises(ValueError):
            mod.plan(reg, CATALOG)

    def test_requires_flagship_contract(self):
        reg = copy.deepcopy(REGISTRY)
        reg["portal"]["repository"] = "other"
        with self.assertRaises(ValueError):
            mod.plan(reg, CATALOG)


if __name__ == "__main__":
    unittest.main()
