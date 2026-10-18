#!/usr/bin/env python3
"""Offline, review-only SVG/CSS LF style inventory. Does NOT approve brand tokens.

Supply locally acquired assets from the documented LF corporate website.
Does not download external URLs, execute CSS, render SVG or rewrite product UIs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {".svg", ".css"}
COLORS = re.compile(r"(?<![\w-])#[0-9a-fA-F]{3,8}\b|(?:rgb|rgba|hsl|hsla)\([^)]{1,110}\)", re.I)
CSS_VAR = re.compile(r"--[\w-]*(?:color|brand|primary|secondary|accent|surface|background|foreground)[\w-]*\s*:\s*([^;{}]+)", re.I)
FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;{}]{1,250})", re.I)
SVG_ATTR_COLOR = re.compile(r'\b(?:fill|stroke|stop-color)\s*=\s*["\x27]([^"\x27]{1,150})["\x27]', re.I)


def inventory(files):
    if not files:
        raise ValueError("At least one locally retrieved .svg/.css file is required")
    observations = []
    for name in files:
        file = Path(name)
        if file.is_symlink() or not file.is_file() or file.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError("Only regular, non-linked SVG/CSS files are allowed")
        data = file.read_bytes()
        if not data or len(data) > MAX_INPUT_BYTES:
            raise ValueError("Invalid file size")
        raw = data.decode("utf-8-sig")
        if re.search(r"<!DOCTYPE|<!ENTITY|<script\b", raw, re.I):
            raise ValueError("Potentially unsafe XML/HTML markup")
        observations.append({
            "file": file.name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "colors_candidates": sorted(set(COLORS.findall(raw)), key=str.lower),
            "css_variable_candidates": sorted(set(x.strip() for x in CSS_VAR.findall(raw))),
            "font_family_candidates": sorted(set(x.strip() for x in FONT_FAMILY.findall(raw))),
            "svg_color_attribute_candidates": sorted(set(x.strip() for x in SVG_ATTR_COLOR.findall(raw))),
        })
    return {
        "status": "REVIEW_REQUIRED_NOT_APPROVED",
        "source_website": "https://lfsolucoes.etc.br/",
        "assets": sorted(observations, key=lambda x: (x["file"], x["sha256"])),
        "visual_tokens_approved": False,
        "brand_asset_redistribution_approved": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("assets", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        print(json.dumps(inventory(args.assets), sort_keys=True, indent=2, ensure_ascii=False))
    except (ValueError, OSError, UnicodeError) as exc:
        print("LF_BRAND_INVENTORY_BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
