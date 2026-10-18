import base64
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("portal_live_audit", ROOT / "scripts/portal_live_catalog_audit.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
REG = {"portal": {"repository": "site-lf-solucoes"}, "products": [
    {"repository": "alpha", "runtime": "python-server", "wave": 1},
    {"repository": "beta", "runtime": "typescript-server", "wave": 2},
]}
CAT = {"products": [
    {"id": "alpha", "slug": "alpha", "detail_url": "/produtos/alpha.html", "runtime": "python-server", "wave": 1, "visibility": "public"},
    {"id": "beta", "slug": "beta", "detail_url": "/produtos/beta.html", "runtime": "typescript-server", "wave": 2, "visibility": "public"},
]}

class PortalLiveAuditTests(unittest.TestCase):
    def test_consistent(self):
        result = mod.audit(REG, CAT)
        self.assertEqual(result["state"], "CONSISTENT")
        self.assertIn("não atesta deploy", mod.summarize(result))

    def test_new_product_is_detected(self):
        reg = copy.deepcopy(REG)
        reg["products"].append({"repository": "gamma", "runtime": "python-server", "wave": 2})
        self.assertIn("gamma", " ".join(mod.audit(reg, CAT)["issues"]))

    def test_missing_or_extra_catalog_entries_fail(self):
        c = copy.deepcopy(CAT)
        c["products"].pop()
        self.assertEqual(mod.audit(REG, c)["state"], "DRIFT")
        c = copy.deepcopy(CAT)
        c["products"].append({"id": "rogue"})
        self.assertEqual(mod.audit(REG, c)["state"], "DRIFT")

    def test_metadata_drift_and_identity_fail(self):
        c = copy.deepcopy(CAT)
        c["products"][0]["runtime"] = "self-hosted-fxserver"
        c["products"][1]["detail_url"] = "/wrong"
        self.assertEqual(len(mod.audit(REG, c)["issues"]), 2)

    def test_invalid_duplicated_ids_fail_closed(self):
        c = copy.deepcopy(CAT)
        c["products"].append(dict(c["products"][0]))
        self.assertEqual(mod.audit(REG, c)["state"], "BLOCKED")

    def test_remote_content_roundtrip_and_encoding_guard(self):
        raw = json.dumps(CAT).encode("utf-8")
        self.assertEqual(mod.decode_github_content({"encoding": "base64", "content": base64.b64encode(raw).decode()}), CAT)
        with self.assertRaises(ValueError):
            mod.decode_github_content({"encoding": "utf-8", "content": "abc"})

if __name__ == "__main__":
    unittest.main()
