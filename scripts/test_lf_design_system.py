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
SOURCE_COMMIT = "d85d2e622e3ebbcd23ae73c279ba7ef9bf09fac8"
SOURCE_SHA256 = {
    "brand-system.css": "a2094af1d4799838bd041c0ee78203187d6b47df3d13776e61a0bfb237deb93b",
    "assets/lf-logo-horizontal.svg": "b2d5fccc716a37e493832b7822a82143e442785bb77a48ce962ae209270da0a7",
    "assets/lf-mark.svg": "0f62def35ce80650cdfe4a975efba5cf93940a5df4a93a343a3e2897280d95da",
}
CORPORATE_THEME = {
    "surface": "white",
    "surface_subtle": "ice",
    "text": "graphite",
    "text_muted": "muted",
    "primary": {"background": "blue", "foreground": "white"},
    "accent": {"background": "electric", "foreground": "navy"},
    "success": {"background": "success", "foreground": "white"},
}
PRODUCT_THEME = {
    "brand_attribution": "opt-in",
    "product_identity": "consumer-owned",
    "functional_status_colors": "consumer-owned",
}
CSS_THEME_ALIASES = {
    "--lf-corporate-surface": "--lf-white",
    "--lf-corporate-surface-subtle": "--lf-ice",
    "--lf-corporate-text": "--lf-graphite",
    "--lf-corporate-text-muted": "--lf-muted",
    "--lf-corporate-primary": "--lf-blue",
    "--lf-corporate-on-primary": "--lf-white",
    "--lf-corporate-accent": "--lf-electric",
    "--lf-corporate-on-accent": "--lf-navy",
    "--lf-corporate-success": "--lf-success",
    "--lf-corporate-on-success": "--lf-white",
}

def git_blob_sha(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))


def contrast_ratio(foreground, background):
    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class LFDesignSystemTests(unittest.TestCase):
    def test_tokens_are_exact_corporate_source_values(self):
        data = json.loads((ROOT / "tokens.json").read_text(encoding="utf-8"))
        self.assertEqual(data["colors"], COLORS)
        self.assertEqual(data["source"]["repository"], "leandroclf/site-lf-solucoes")
        self.assertEqual(data["source"]["commit_sha"], SOURCE_COMMIT)
        self.assertEqual(data["source"]["source_hash_type"], "git-blob-sha1")
        self.assertEqual(data["source"]["source_sha256"], SOURCE_SHA256)
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
            self.assertEqual(hashlib.sha256(asset).hexdigest(), SOURCE_SHA256[path], path)
            self.assertNotRegex(asset.decode("utf-8"), r"(?i)<script\b|<!DOCTYPE|<!ENTITY|<foreignObject\b|https?://(?!www\.w3\.org/2000/svg)")

    def test_css_stays_namespaced_and_brand_not_product_status(self):
        css = (ROOT / "tokens.css").read_text(encoding="utf-8")
        for name in re.findall(r"(--[a-zA-Z][\w-]*)\s*:", css):
            self.assertTrue(name.startswith("--lf-"), name)
        self.assertNotIn("!important", css)
        self.assertNotIn("body {", css)
        self.assertNotIn("html {", css)

    def test_corporate_theme_pairs_meet_wcag_aa_and_product_theme_stays_owned(self):
        data = json.loads((ROOT / "tokens.json").read_text(encoding="utf-8"))
        self.assertEqual(data["themes"]["corporate"], CORPORATE_THEME)
        self.assertEqual(data["themes"]["product"], PRODUCT_THEME)
        css = (ROOT / "tokens.css").read_text(encoding="utf-8")
        for alias, source in CSS_THEME_ALIASES.items():
            self.assertIn(f"{alias}: var({source});", css)

        pairs = [
            (CORPORATE_THEME["text"], CORPORATE_THEME["surface"]),
            (CORPORATE_THEME["text"], CORPORATE_THEME["surface_subtle"]),
            (CORPORATE_THEME["text_muted"], CORPORATE_THEME["surface"]),
            (CORPORATE_THEME["primary"]["foreground"], CORPORATE_THEME["primary"]["background"]),
            (CORPORATE_THEME["accent"]["foreground"], CORPORATE_THEME["accent"]["background"]),
            (CORPORATE_THEME["success"]["foreground"], CORPORATE_THEME["success"]["background"]),
        ]
        for foreground, background in pairs:
            self.assertGreaterEqual(contrast_ratio(COLORS[foreground], COLORS[background]), 4.5)

    def test_package_is_consumer_opt_in(self):
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertTrue(package["private"])
        self.assertEqual(package["name"], "@lf-solucoes/design-system")
        self.assertNotIn("dependencies", package)


if __name__ == "__main__":
    unittest.main()
