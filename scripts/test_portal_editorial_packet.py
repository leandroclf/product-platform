import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("editorial_packet", ROOT / "scripts/portal_editorial_packet.py")
packet_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packet_module)

REG = {"portal": {"repository": "site-lf-solucoes"}, "products": [
    {"repository": "known", "domain": "known-domain", "runtime": "python-server", "wave": 1},
    {"repository": "new-product", "domain": "safe-domain", "runtime": "typescript-server", "wave": 2},
]}
CAT = {"products": [{"id": "known"}]}


class EditorialPacketTests(unittest.TestCase):
    def test_safe_draft_has_no_publication_claim(self):
        packet = packet_module.editorial_packet(REG, CAT)
        self.assertEqual(packet["status"], "EDITORIAL_REVIEW_REQUIRED")
        self.assertEqual([x["id"] for x in packet["items"]], ["new-product"])
        rendered = packet_module.render_packet(packet)
        self.assertIn("aguardando validação editorial", rendered)
        self.assertIn("não verificadas", rendered)
        self.assertNotIn("https://", rendered)

    def test_no_missing_products_is_noop(self):
        catalog = {"products": [{"id": "known"}, {"id": "new-product"}]}
        packet = packet_module.editorial_packet(REG, catalog)
        self.assertEqual(packet["status"], "NO_INTAKE_REQUIRED")
        self.assertIn("Nenhum produto", packet_module.render_packet(packet))

    def test_blocks_invalid_registry_and_no_false_success(self):
        broken = copy.deepcopy(REG)
        broken["products"].append({"repository": "../../private", "domain": "x", "runtime": "python-server", "wave": 1})
        with self.assertRaises(ValueError):
            packet_module.editorial_packet(broken, CAT)
        self.assertIn("UNVERIFIED", packet_module.render_packet({"status": "UNVERIFIED"}))

    def test_does_not_render_unbounded_number_of_new_products(self):
        large = copy.deepcopy(REG)
        large["products"].extend({"repository": "new-" + str(i), "domain": "d", "runtime": "python-server", "wave": 1} for i in range(25))
        packet = packet_module.editorial_packet(large, CAT)
        self.assertEqual(packet["status"], "BLOCKED_TOO_MANY")
        self.assertEqual(packet["items"], [])


if __name__ == "__main__":
    unittest.main()
