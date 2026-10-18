"""Contrato entre pacotes: o envelope gerado pelo cli deve passar no validador do kit com o registry real.

Fica na raiz porque nenhum pacote pode depender do outro nesse sentido (platform-packages.json).
Também prova a cadeia completa: o mesmo envelope é aceito pelo ai-team (schema do kit, registry e base_sha).
Requer PyYAML e jsonschema (requirements-validation.txt).
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/cli/src"))
sys.path.insert(0, str(ROOT / "packages/engineering-team/scripts"))
from omnicli.handoff import build_platform_handoff  # noqa: E402
import local_team  # noqa: E402

spec = importlib.util.spec_from_file_location("vph", ROOT / "packages/kit/scripts/validate-platform-handoff.py")
vph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vph)

CAPABILITIES = {"product": "vehicle-tracking", "capabilities": [
    {"name": "entitlements", "decision": "REUSE", "owner": "product-platform-harness"},
    {"name": "trip_export", "decision": "CREATE", "owner": "vehicle-tracking"}]}
ENGINEERING = {"objective": "Exportar viagens com limite por plano", "scope": {"allowed_paths": ["src/", "docs/"]},
               "acceptance": {"criteria": ["Exporta CSV", "Respeita o limite no servidor"]},
               "risk": {"level": "medium"}, "evidence": {"required": ["tests", "build", "ci"]}}
OPTIONS = {"repository_url": "https://github.com/leandroclf/vehicle-tracking.git", "base_ref": "main",
           "base_sha": "a" * 40, "kit_ref": "b" * 40, "harness_ref": "c" * 40, "profile": "backend"}


def proposal(capabilities=CAPABILITIES, engineering=ENGINEERING):
    return ("# Proposta\n```capability-handoff\n" + json.dumps(capabilities) + "\n```\n"
            "```engineering-handoff\n" + json.dumps(engineering) + "\n```\n")


class HandoffContractTest(unittest.TestCase):
    def envelope(self, **kwargs):
        return build_platform_handoff(proposal(**kwargs), vph.fingerprint(vph.REGISTRY), proposal_id="run-1", **OPTIONS)

    def test_cli_envelope_passes_the_kit_validator_with_the_real_registry(self):
        self.assertEqual(vph.violations(self.envelope(), vph.REGISTRY), [])

    def test_kit_validator_still_catches_g1_violations_in_a_cli_envelope(self):
        bad = {**CAPABILITIES, "capabilities": [{"name": "entitlements", "decision": "CREATE", "owner": "vehicle-tracking"}]}
        self.assertTrue(any("CREATE duplica" in v for v in vph.violations(self.envelope(capabilities=bad), vph.REGISTRY)))

    def test_stale_registry_fingerprint_is_reported(self):
        envelope = build_platform_handoff(proposal(), "0" * 64, proposal_id="run-1", **OPTIONS)
        self.assertTrue(any("registry defasado" in v for v in vph.violations(envelope, vph.REGISTRY)))


    def test_ai_team_accepts_the_cli_envelope_end_to_end(self):
        envelope = self.envelope()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "envelope.json"
            path.write_text(json.dumps(envelope))
            inputs = local_team.platform_inputs(str(path), [], str(vph.REGISTRY), OPTIONS["base_sha"])
            self.assertEqual(json.loads(inputs["capabilities.json"]), envelope["portfolio"])
            self.assertEqual(json.loads(inputs["rules.json"]), envelope["rules_refs"])
            with self.assertRaises(local_team.Blocked):  # proposta feita sobre outra base
                local_team.platform_inputs(str(path), [], str(vph.REGISTRY), "e" * 40)


# Portal intake safety tests are part of the pre-existing platform CI job.
portal_spec = importlib.util.spec_from_file_location("portal_intake_tests", ROOT / "scripts/test_portal_intake.py")
portal_test_module = importlib.util.module_from_spec(portal_spec)
portal_spec.loader.exec_module(portal_test_module)
PortalIntakeTests = portal_test_module.PortalIntakeTests

# The scheduled LF portal coverage watcher must pass the existing platform CI tests.
portal_live_spec = importlib.util.spec_from_file_location("portal_live_tests", ROOT / "scripts/test_portal_live_catalog_audit.py")
portal_live_module = importlib.util.module_from_spec(portal_live_spec)
portal_live_spec.loader.exec_module(portal_live_module)
PortalLiveAuditTests = portal_live_module.PortalLiveAuditTests

editorial_spec = importlib.util.spec_from_file_location("editorial_tests", ROOT / "scripts/test_portal_editorial_packet.py")
editorial_tests = importlib.util.module_from_spec(editorial_spec)
editorial_spec.loader.exec_module(editorial_tests)
EditorialPacketTests = editorial_tests.EditorialPacketTests

if __name__ == "__main__":
    unittest.main()
