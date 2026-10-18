"""LF Soluções immutable visual asset and CSS token conformance guards."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1] / "packages/design-system"
COLORS = {
    "navy": "#061B4F", "blue": "#0757E8", "electric": "#008CFF",
    "cyan": "#00D4FF", "ice": "#EAF6FF", "graphite": "#172033",
    "text": "#172033", "muted": "#526079", "border": "#D8E7F4",
    "white": "#FFFFFF", "success": "#14804A",
}
SOURCE_BLOBS = {
    "assets/lf-logo-horizontal.svg": "536ee44d1e4b3601894eaa349d03e30635136a2d",
    "assets/lf-mark.svg": "0d3ed77bfb9fb3183a704f158be25ff3ee4cea82",
}

def git_blob_sha(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


class LFDesignSystemTests(unittest.TestCase):
    def test_tokens_are_exact_corporate_source_values(self):
        data = json.loads((ROOT / "tokens.json").read_text(encoding="utf-8"))
        self.assertEqual(data["colors"], COLORS)
        self.assertEqual(data["source"]["repository"], "leandroclf/site-lf-solucoes")
        self.assertEqual(data["source"]["source_hash_type"], "git-blob-sha1")
        self.assertFalse(data["distribution"]["automatic_product_adoption"])
        css = (ROOT / "tokens.css").read_text(encoding="utf-8")
        for name, color in COLORS.items():
            self.assertIn(f"--lf-{name}: {color};", css)
        self.assertIn("Inter", data["typography"]["fontFamily"])

    def test_logos_exactly_match_source_git_blob_hashes(self):
        data = json.loads((ROOT / "tokens.json").read_text(encoding="utf-8"))
        for path, sha in SOURCE_BLOBS.items():
            asset = (ROOT / path).read_bytes()
            self.assertEqual(git_blob_sha(asset), sha, path)
            self.assertEqual(data["source"]["files"][path], sha)
            self.assertNotRegex(asset.decode("utf-8"), r"(?i)<script\b|<!DOCTYPE|<!ENTITY|<foreignObject\b|https?://(?!www\.w3\.org/2000/svg)")

    def test_css_stays_namespaced_and_brand_not_product_status(self):
        css = (ROOT / "tokens.css").read_text(encoding="utf-8")
        for name in re.findall(r"(--[a-zA-Z][\w-]*)\s*:", css):
            self.assertTrue(name.startswith("--lf-"), name)
        self.assertNotIn("!important", css)
        self.assertNotIn("body {", css)
        self.assertNotIn("html {", css)

    def test_package_is_consumer_opt_in(self):
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertTrue(package["private"])
        self.assertEqual(package["name"], "@lf-solucoes/design-system")
        self.assertNotIn("dependencies", package)


if __name__ == "__main__":
    unittest.main()
