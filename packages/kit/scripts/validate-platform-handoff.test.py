import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vph", ROOT / "scripts/validate-platform-handoff.py")
vph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vph)

FIXTURE = json.loads((ROOT / "contracts/platform-handoff/fixtures/valid.json").read_text())
FIXTURE["portfolio"]["registry_fingerprint"] = vph.fingerprint(vph.REGISTRY)  # o fixture guarda só um valor de referência


def doc(mutate=None):
    value = copy.deepcopy(FIXTURE)
    if mutate:
        mutate(value)
    return value


def cap(value, i=0):
    return value["portfolio"]["capabilities"][i]


class PlatformHandoffTest(unittest.TestCase):
    def check(self, value):
        return vph.violations(value, vph.REGISTRY)

    def test_valid_envelope_and_flat_portfolio_handoff_pass(self):
        self.assertEqual(self.check(doc()), [])
        self.assertEqual(self.check(doc()["portfolio"]), [])  # formato de `omnicli conceive --handoff-out`

    def test_each_g1_stop_condition_is_reported(self):
        cases = {
            "registry defasado": lambda d: d["portfolio"].update(registry_fingerprint="0" * 64),
            "CREATE duplica": lambda d: cap(d).update(decision="CREATE"),
            "CREATE exige dono explícito": lambda d: cap(d, 1).update(owner="ninguem"),
            "deve mirar o dono canônico": lambda d: cap(d).update(decision="EXTEND", owner="vehicle-tracking"),
            "não existe no registry": lambda d: cap(d).update(name="inexistente"),
            "produto->produto": lambda d: d["portfolio"]["capabilities"].append(
                {"name": "financial_insights", "decision": "REUSE", "owner": "bussola-financeira"}),
            "duplicada": lambda d: d["portfolio"]["capabilities"].append(dict(cap(d))),
        }
        for message, mutate in cases.items():
            with self.subTest(message):
                self.assertTrue(any(message in line for line in self.check(doc(mutate))), self.check(doc(mutate)))

    def test_implementation_owner_is_accepted_for_reuse(self):
        value = doc(lambda d: cap(d).update(name="product_events", owner="product-platform-harness"))
        self.assertEqual(self.check(value), [])

    def test_schema_rejects_floating_refs_unknown_fields_and_bad_enums(self):
        cases = {
            "tag flutuante": lambda d: d["rules_refs"]["kit"].update(ref="main"),
            "campo extra": lambda d: d.update(extra=1),
            "campo extra aninhado": lambda d: d["proposal"]["scope"].update(extra=1),
            "perfil": lambda d: d["rules_refs"].update(profile="fullstack"),
            "decisão": lambda d: cap(d).update(decision="COPY"),
            "sem rules_refs": lambda d: d.pop("rules_refs"),
            "sem critérios": lambda d: d["proposal"]["acceptance"].update(criteria=[]),
            "versão": lambda d: d.update(schema_version="2.0"),
        }
        for name, mutate in cases.items():
            with self.subTest(name):
                self.assertTrue(any(line.startswith("schema:") for line in self.check(doc(mutate))))

    def test_cli_exit_codes_and_fingerprint_matches_sha256_of_bytes(self):
        script = str(ROOT / "scripts/validate-platform-handoff.py")
        with tempfile.TemporaryDirectory() as t:
            good, bad = Path(t, "good.json"), Path(t, "bad.json")
            good.write_text(json.dumps(doc())); bad.write_text(json.dumps(doc(lambda d: cap(d).update(decision="COPY"))))
            run = lambda *a: subprocess.run([sys.executable, script, *a], capture_output=True, text=True)
            self.assertEqual(run(str(good)).returncode, 0)
            self.assertEqual(run(str(bad)).returncode, 1)
            self.assertEqual(run(str(Path(t, "missing.json"))).returncode, 2)
            self.assertEqual(run("--fingerprint").stdout.strip(), vph.fingerprint(vph.REGISTRY))


# Reuse the existing kit CI test entry point without modifying protected workflows.
deployment_spec = importlib.util.spec_from_file_location(
    "deployment_g6_tests", ROOT / "scripts/validate-deployment-plan.test.py")
deployment_suite = importlib.util.module_from_spec(deployment_spec)
deployment_spec.loader.exec_module(deployment_suite)
DeploymentContractTests = deployment_suite.DeploymentContractTests
artifact_spec = importlib.util.spec_from_file_location(
    "g6_artifact_tests", ROOT / "scripts/verify-deployment-artifact.test.py")
artifact_suite = importlib.util.module_from_spec(artifact_spec)
artifact_spec.loader.exec_module(artifact_suite)
DeploymentArtifactEvidenceTests = artifact_suite.DeploymentArtifactEvidenceTests

# Reuse the existing Kit CI entrypoint for portfolio LF brand and G6 coverage.
for test_module_name, test_filename, suite_name in (
    ("portfolio_brand_deploy_tests", "test_portfolio_brand_deploy.py", "ContractTests"),
    ("portfolio_deployment_discovery_tests", "test_portfolio_deployment_discovery.py", "DiscoveryContractTests"),
    ("lf_brand_inventory_tests", "test_lf_brand_inventory.py", "InventoryTests"),
):
    spec = importlib.util.spec_from_file_location(test_module_name, ROOT / "scripts" / test_filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    globals()[suite_name] = getattr(module, suite_name)

if __name__ == "__main__":
    unittest.main()
