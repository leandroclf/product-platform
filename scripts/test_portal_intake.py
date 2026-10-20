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

    def test_draft_commit_is_prepared_before_branch_ref_and_pr(self):
        calls = []
        responses = {
            ("GET", "/git/ref/heads/main"): {"object": {"sha": "a" * 40}},
            ("GET", "/git/commits/" + "a" * 40): {"tree": {"sha": "b" * 40}},
            ("POST", "/git/blobs"): {"sha": "c" * 40},
            ("POST", "/git/trees"): {"sha": "d" * 40},
            ("POST", "/git/commits"): {"sha": "e" * 40},
            ("POST", "/git/refs"): {},
            ("POST", "/pulls"): {"html_url": "https://github.com/leandroclf/site-lf-solucoes/pull/99"},
        }

        def api(method, endpoint, token, payload=None):
            calls.append((method, endpoint, payload))
            suffix = endpoint.removeprefix("/repos/" + mod.PORTAL_REPO)
            return responses[(method, suffix)]

        result = mod.create_draft_intake([mod.plan(REGISTRY, CATALOG)[0]], "test-token", api=api)
        endpoints = [call[1] for call in calls]
        self.assertEqual(result["status"], "DRAFT_INTAKE_PR_CREATED")
        self.assertLess(endpoints.index("/repos/" + mod.PORTAL_REPO + "/git/blobs"),
                        endpoints.index("/repos/" + mod.PORTAL_REPO + "/git/refs"))
        self.assertLess(endpoints.index("/repos/" + mod.PORTAL_REPO + "/git/commits"),
                        endpoints.index("/repos/" + mod.PORTAL_REPO + "/git/refs"))
        self.assertEqual(calls[-2][2]["sha"], "e" * 40)
        self.assertTrue(calls[-1][2]["draft"])

    def test_failed_blob_does_not_create_branch_or_pull_request(self):
        calls = []

        def api(method, endpoint, token, payload=None):
            calls.append((method, endpoint))
            if endpoint.endswith("/git/ref/heads/main"):
                return {"object": {"sha": "a" * 40}}
            if endpoint.endswith("/git/commits/" + "a" * 40):
                return {"tree": {"sha": "b" * 40}}
            raise RuntimeError("simulated blob failure")

        with self.assertRaisesRegex(RuntimeError, "blob failure"):
            mod.create_draft_intake([mod.plan(REGISTRY, CATALOG)[0]], "test-token", api=api)
        self.assertFalse(any(endpoint.endswith("/git/refs") or endpoint.endswith("/pulls")
                             for _, endpoint in calls))

    def test_empty_intake_is_network_noop(self):
        def fail_if_called(*_args, **_kwargs):
            self.fail("empty intake must not call GitHub")
        result = mod.create_draft_intake([], "test-token", api=fail_if_called)
        self.assertEqual(result, {"status": "PORTAL_INTAKE_UP_TO_DATE", "products": []})


if __name__ == "__main__":
    unittest.main()
