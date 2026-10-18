import importlib.util
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent / "inventory-lf-brand-assets.py"
SPEC = importlib.util.spec_from_file_location("lf_inventory", SOURCE)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_extract_candidates_but_never_approve(self):
        asset = self.root / "lf-logo.svg"
        asset.write_text('<svg fill="#123456"><style>--brand-color: #aabbcc;font-family: "Example Sans"</style></svg>')
        result = module.inventory([asset])
        self.assertFalse(result["visual_tokens_approved"])
        self.assertFalse(result["brand_asset_redistribution_approved"])
        self.assertEqual(result["assets"][0]["colors_candidates"], ["#123456", "#aabbcc"])
        self.assertEqual(result["assets"][0]["font_family_candidates"], ['"Example Sans"'])
        self.assertEqual(len(result["assets"][0]["sha256"]), 64)

    def test_rejects_unapproved_inputs(self):
        text = self.root / "other.txt"
        text.write_text("#fff")
        with self.assertRaises(ValueError):
            module.inventory([text])
        with self.assertRaises(ValueError):
            module.inventory([])
        svg = self.root / "lf.svg"
        svg.write_text("<!DOCTYPE svg><svg/>")
        with self.assertRaises(ValueError):
            module.inventory([svg])
        svg.write_text("<svg><script>foo</script></svg>")
        with self.assertRaises(ValueError):
            module.inventory([svg])
        link = self.root / "linked.css"
        link.symlink_to(svg)
        with self.assertRaises(ValueError):
            module.inventory([link])

    def test_rejects_empty_and_huge(self):
        asset = self.root / "empty.css"
        asset.touch()
        with self.assertRaises(ValueError):
            module.inventory([asset])
        asset.write_bytes(b"x" * (module.MAX_INPUT_BYTES + 1))
        with self.assertRaises(ValueError):
            module.inventory([asset])


if __name__ == "__main__":
    unittest.main()
