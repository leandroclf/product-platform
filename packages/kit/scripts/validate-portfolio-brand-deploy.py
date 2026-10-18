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
    "fxserver-distribution", "static-web-or-local-package",
}
STATES = {"discovery-required", "offline-staging-dry-run-verified"}


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
    editorial = brand.get("editorial", {})
    if editorial.get("tagline") != "Tecnologia que gera valor.":
        errors.append("Institutional tagline not sourced")
    visual = brand.get("visual", {})
    if visual.get("status") != "AWAITING_VERIFIED_ASSET_EXTRACTION" or any(
        visual.get(field) is not None for field in ("colors", "fonts", "dimensions", "logo_checksum_sha256")
    ):
        errors.append("Unverified design tokens must not be represented as extracted")
    adoption = brand.get("adoption", {})
    if (adoption.get("product_brand_preserved") is not True
        or adoption.get("force_rebrand") is not False
        or adoption.get("remote_asset_hotlink") is not False
        or adoption.get("requires_local_approved_assets") is not True):
        errors.append("Unsafe brand adoption policy")
    return errors


def main():
    inputs = [json.loads(f.read_text(encoding="utf-8")) for f in (REGISTERED, DEPLOY, BRAND)]
    errors = validate(*inputs)
    if errors:
        print("PORTFOLIO_CONTRACT_BLOCKED:", "; ".join(errors))
        raise SystemExit(1)
    print("PORTFOLIO_BRAND_AND_DEPLOY_CONTRACTS_VALID (offline only; no authorization or visual token extraction)")


if __name__ == "__main__":
    main()
