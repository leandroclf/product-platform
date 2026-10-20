#!/usr/bin/env python3
"""Offline guard for portfolio G6 adoption and LF brand source contracts.

No network, no cloud access, no deploy permissions. Never treats plans as approvals.
"""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REGISTERED = ROOT / "contracts/portfolio-products.json"
DEPLOY = ROOT / "contracts/portfolio-deployment-targets.json"
BRAND = ROOT / "contracts/lf-brand-source.json"
ADAPTERS = {
    "cloudflare-workers-opennext", "python-container-or-serverless",
    "rapidapi-or-python-service", "python-api-plus-web-frontend",
    "fxserver-distribution", "static-web-or-local-package", "github-pages-static",
}
STATES = {"discovery-required", "offline-staging-dry-run-verified", "existing-automatic-pages-deploy-unverified-runtime"}
BRAND_SOURCE_COMMIT = "d85d2e622e3ebbcd23ae73c279ba7ef9bf09fac8"
BRAND_COLORS = {
    "navy": "#061B4F", "blue": "#0757E8", "electric": "#008CFF",
    "cyan": "#00D4FF", "ice": "#EAF6FF", "graphite": "#172033",
    "text": "#172033", "muted": "#526079", "border": "#D8E7F4",
    "white": "#FFFFFF", "success": "#14804A",
}
BRAND_FONTS = [
    "Inter", "ui-sans-serif", "system-ui", "-apple-system",
    "BlinkMacSystemFont", "Segoe UI", "sans-serif",
]
BRAND_DIMENSIONS = {
    "lf-logo-horizontal.svg": {"width_px": 620, "height_px": 150, "view_box": "0 0 620 150"},
    "lf-mark.svg": {"width_px": 120, "height_px": 120, "view_box": "0 0 120 120"},
}
BRAND_GRID = {
    "status": "SITE_LAYOUT_NOT_BRAND_TOKEN",
    "layout_patterns": [
        ".nav-solutions-grid: repeat(3, 1fr); max-width 920px: 1fr",
        ".brand-hero-layout: minmax(0, .9fr) minmax(0, 1.1fr); max-width 920px: 1fr",
        ".section-heading: .72fr 1.28fr; max-width 920px: 1fr",
    ],
    "shared_brand_grid": "not_declared",
}
BRAND_FILES = {
    "brand-system.css": {
        "git_blob_sha1": "02a646af52d899935f1d28214d449bf1f5965c5f",
        "sha256": "a2094af1d4799838bd041c0ee78203187d6b47df3d13776e61a0bfb237deb93b",
    },
    "assets/lf-logo-horizontal.svg": {
        "git_blob_sha1": "536ee44d1e4b3601894eaa349d03e30635136a2d",
        "sha256": "b2d5fccc716a37e493832b7822a82143e442785bb77a48ce962ae209270da0a7",
    },
    "assets/lf-mark.svg": {
        "git_blob_sha1": "0d3ed77bfb9fb3183a704f158be25ff3ee4cea82",
        "sha256": "0f62def35ce80650cdfe4a975efba5cf93940a5df4a93a343a3e2897280d95da",
    },
}


def validate(portfolio, deploy, brand):
    errors = []
    products = portfolio.get("products")
    targets = deploy.get("targets")
    if not isinstance(products, list) or not isinstance(targets, list):
        return ["Portfolio products/targets must be lists"]
    registered = {p.get("repository"): p.get("runtime") for p in products if isinstance(p, dict)}
    if len(registered) != len(products):
        errors.append("Portfolio contains duplicate or invalid products")
    mapped = {}
    for entry in targets:
        if not isinstance(entry, dict):
            errors.append("Deployment target is not an object")
            continue
        name = entry.get("product")
        if not isinstance(name, str) or name not in registered or name in mapped:
            errors.append("Deployment target is unknown or repeated")
            continue
        mapped[name] = entry
        if entry.get("runtime") != registered[name]:
            errors.append("Runtime drift for " + name)
        if entry.get("adapter") not in ADAPTERS:
            errors.append("Unreviewed adapter for " + name)
        if entry.get("adoption") not in STATES:
            errors.append("Invalid unverified adoption claim for " + name)
        if entry.get("remote_deploy_verified") is not False:
            errors.append("Remote deployment cannot be claimed by offline registry for " + name)
        if name != "vehicle-tracking" and "evidence_run" in entry:
            errors.append("Unreviewed run evidence for " + name)
        if entry.get("adoption") == "offline-staging-dry-run-verified":
            if name != "vehicle-tracking" or entry.get("evidence_run") != "https://github.com/leandroclf/vehicle-tracking/actions/runs/39159440993":
                errors.append("Unsupported staging evidence for " + name)
    flagship = portfolio.get("portal", {})
    if (flagship.get("repository") != "site-lf-solucoes"
        or flagship.get("website") != "https://lfsolucoes.etc.br/"
        or flagship.get("catalog_manifest") != "data/product-catalog.json"
        or flagship.get("required_for_new_products") is not True
        or flagship.get("publication_requires_editorial_review") is not True
        or flagship.get("automatic_cross_repo_sync_verified") is not False):
        errors.append("Missing flagship portal publishing contract")
    if flagship.get("kind") != "flagship-product" or flagship.get("runtime") != "static-github-pages":
        errors.append("Flagship product type must remain explicit")
    portal_deploy = deploy.get("flagship_portal", {})
    if (portal_deploy.get("product") != "site-lf-solucoes"
        or portal_deploy.get("runtime") != "static-github-pages"
        or portal_deploy.get("adapter") != "github-pages-static"
        or portal_deploy.get("adoption") != "existing-automatic-pages-deploy-unverified-runtime"
        or portal_deploy.get("remote_deploy_verified") is not False):
        errors.append("Flagship portal deployment must be tracked without invented remote evidence")
    if set(mapped) != set(registered):
        errors.append("Every product must be mapped exactly once")
    d = deploy.get("defaults", {})
    for field, value in {
        "deploy_authorized": False, "production_requires_independent_approval": True,
        "artifact_immutable": True, "rollback_required_in_production": True,
        "credentials_in_repository": False,
    }.items():
        if d.get(field) is not value:
            errors.append("Unsafe deployment default: " + field)
    if deploy.get("policy_owner") != "packages/kit/docs/DEPLOYMENT-G6.md":
        errors.append("Deployment policy must remain in Kit")
    if brand.get("id") != "lf-solucoes" or brand.get("company") != "LF Soluções":
        errors.append("Incorrect corporate brand owner")
    source = brand.get("source", {})
    if source.get("url") != "https://lfsolucoes.etc.br/":
        errors.append("Unapproved brand source")
    if source.get("logo_url") != "https://lfsolucoes.etc.br/assets/lf-logo-horizontal.svg":
        errors.append("Unapproved logo source")
    if (source.get("repository") != "leandroclf/site-lf-solucoes"
        or source.get("commit_sha") != BRAND_SOURCE_COMMIT
        or source.get("files") != BRAND_FILES):
        errors.append("Brand source revision or digests are not pinned")
    editorial = brand.get("editorial", {})
    if editorial.get("tagline") != "Tecnologia que gera valor.":
        errors.append("Institutional tagline not sourced")
    visual = brand.get("visual", {})
    if (visual.get("status") != "SOURCE_VERIFIED_NOT_APPROVED"
        or visual.get("colors") != BRAND_COLORS
        or visual.get("fonts") != BRAND_FONTS
        or visual.get("dimensions") != BRAND_DIMENSIONS
        or visual.get("grid") != BRAND_GRID
        or visual.get("logo_checksum_sha256") != BRAND_FILES["assets/lf-logo-horizontal.svg"]["sha256"]):
        errors.append("Brand visual extraction does not match pinned source facts")
    adoption = brand.get("adoption", {})
    if (adoption.get("product_brand_preserved") is not True
        or adoption.get("force_rebrand") is not False
        or adoption.get("remote_asset_hotlink") is not False
        or adoption.get("requires_local_approved_assets") is not True
        or adoption.get("redistribution_license") != "not_declared"
        or adoption.get("redistribution_approved") is not False
        or adoption.get("product_adoption_approved") is not False):
        errors.append("Unsafe brand adoption policy")
    return errors


def main():
    inputs = [json.loads(f.read_text(encoding="utf-8")) for f in (REGISTERED, DEPLOY, BRAND)]
    errors = validate(*inputs)
    if errors:
        print("PORTFOLIO_CONTRACT_BLOCKED:", "; ".join(errors))
        raise SystemExit(1)
    print("PORTFOLIO_BRAND_AND_DEPLOY_CONTRACTS_VALID (pinned source facts; no redistribution, product-use, or deploy authorization)")


if __name__ == "__main__":
    main()
