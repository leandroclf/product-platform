"""Read-only live LF portal catalog audit for scheduled portfolio governance.

This module never writes to the portal, generates PRs or claims deployment success.
Registry is local at the checked-out commit; portal catalog comes from GitHub main.
"""
import base64
import json
import re

PORTAL_PATH = "repos/leandroclf/site-lf-solucoes/contents/data/product-catalog.json?ref=main"
SLUG = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def decode_github_content(result):
    if not isinstance(result, dict) or result.get("encoding") != "base64":
        raise ValueError("Expected GitHub content API base64 response")
    encoded = result.get("content")
    if not isinstance(encoded, str) or len(encoded) > 2_000_000:
        raise ValueError("Missing or unreasonably large portal catalog")
    return json.loads(base64.b64decode(encoded, validate=False).decode("utf-8"))


def audit(registry, catalog):
    if registry.get("portal", {}).get("repository") != "site-lf-solucoes":
        return {"state": "BLOCKED", "issues": ["Flagship ownership contract missing"]}
    products = registry.get("products")
    current = catalog.get("products")
    if not isinstance(products, list) or not isinstance(current, list):
        return {"state": "BLOCKED", "issues": ["Invalid product collections"]}
    expected = {}
    for item in products:
        if not isinstance(item, dict):
            return {"state": "BLOCKED", "issues": ["Invalid platform entry"]}
        name = item.get("repository")
        if not isinstance(name, str) or not SLUG.fullmatch(name) or name in expected:
            return {"state": "BLOCKED", "issues": ["Invalid/duplicated platform identity"]}
        expected[name] = item
    observed = {}
    for item in current:
        if not isinstance(item, dict):
            return {"state": "BLOCKED", "issues": ["Invalid portal entry"]}
        name = item.get("id")
        if not isinstance(name, str) or not SLUG.fullmatch(name) or name in observed:
            return {"state": "BLOCKED", "issues": ["Invalid/duplicated portal identity"]}
        observed[name] = item
    issues = []
    for name in sorted(expected.keys() - observed.keys()):
        issues.append(f"Falta página pública no catálogo: {name}")
    for name in sorted(observed.keys() - expected.keys()):
        issues.append(f"Produto sem registro na plataforma: {name}")
    for name in sorted(expected.keys() & observed.keys()):
        a, b = expected[name], observed[name]
        if b.get("slug") != name or b.get("detail_url") != f"/produtos/{name}.html":
            issues.append(f"Identidade/rota divergente: {name}")
        if a.get("runtime") != b.get("runtime") or a.get("wave") != b.get("wave"):
            issues.append(f"Runtime/etapa divergente: {name}")
        if b.get("visibility") != "public":
            issues.append(f"Visibilidade pendente de revisão: {name}")
    return {"state": "DRIFT" if issues else "CONSISTENT",
            "expected": len(expected), "observed": len(observed), "issues": issues}


def summarize(report):
    state = report.get("state", "UNVERIFIED")
    if state == "CONSISTENT":
        return f"CONSISTENT — {report['expected']} produtos no registry e no catálogo remoto da main; não atesta deploy Pages ou URLs públicas."
    result = [f"{state} — cobertura do catálogo não comprovada."]
    for issue in report.get("issues", [])[:25]:
        result.append("- " + issue.replace("|", "/").replace("\n", " ")[:180])
    return "\n".join(result)
