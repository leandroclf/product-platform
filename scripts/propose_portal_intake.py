#!/usr/bin/env python3
"""Propose missing corporate portal content as a review-only GitHub PR.

Default is read-only planning. --apply requires PORTAL_PR_TOKEN with scoped
contents:write and pull_requests:write on site-lf-solucoes ONLY.
No application deploy, workflow dispatch, secrets read or direct main writes.
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1] / "packages/kit/contracts/portfolio-products.json"
HOST = "https://api.github.com"
PORTAL_REPO = "leandroclf/site-lf-solucoes"
SLUG = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def plan(registry, site_catalog):
    if registry.get("portal", {}).get("repository") != "site-lf-solucoes":
        raise ValueError("Flagship portal contract missing")
    products = registry.get("products")
    current = site_catalog.get("products")
    if not isinstance(products, list) or not isinstance(current, list):
        raise ValueError("Invalid product arrays")
    ids = [p.get("id") for p in current if isinstance(p, dict)]
    if len(ids) != len(current) or len(set(ids)) != len(ids):
        raise ValueError("Invalid or repeated portal product IDs")
    names = [p.get("repository") for p in products if isinstance(p, dict)]
    if len(names) != len(products) or len(set(names)) != len(names):
        raise ValueError("Invalid or repeated platform product names")
    proposed = []
    for p in products:
        name = p["repository"]
        if not isinstance(name, str) or not SLUG.fullmatch(name):
            raise ValueError("Invalid product repository identity")
        if name not in ids:
            proposed.append({
                "id": name,
                "source_repository": "leandroclf/" + name,
                "domain": p["domain"],
                "runtime": p["runtime"],
                "wave": p["wave"],
                "visibility": "review-required",
                "title": None,
                "category": None,
                "summary": None,
                "highlights": None,
                "verified_public_url": None,
                "editorial_approval": False,
                "next_action": "Review and move approved contents into data/product-catalog.json, regenerate /produtos/ pages, update platform-portfolio.snapshot.json and validate CI",
            })
    return sorted(proposed, key=lambda p: p["id"])


def github(method, endpoint, token, payload=None):
    if not endpoint.startswith("/repos/" + PORTAL_REPO + "/"):
        raise ValueError("GitHub API endpoint outside approved portal repository")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        HOST + endpoint, data=body, method=method,
        headers={"Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "Authorization": "Bearer " + token,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--catalog", type=Path, required=True,
                             help="Locally reviewed copy of site-lf-solucoes/data/product-catalog.json")
    args_parser.add_argument("--apply", action="store_true",
                             help="Create one review-only intake PR in site-lf-solucoes using PORTAL_PR_TOKEN")
    args = args_parser.parse_args()
    try:
        registry = json.loads(PLATFORM.read_text(encoding="utf-8"))
        site_catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
        candidates = plan(registry, site_catalog)
        if not args.apply:
            print(json.dumps({"mode": "DRY_RUN", "unlisted_products": candidates}, ensure_ascii=False, indent=2))
            return 0
        token = os.environ.get("PORTAL_PR_TOKEN", "")
        if not token:
            raise ValueError("PORTAL_PR_TOKEN is required for --apply")
        if not candidates:
            print("PORTAL_INTAKE_UP_TO_DATE: no PR needed")
            return 0
        # The base SHA is obtained from authenticated GitHub, never assumed.
        base = github("GET", "/repos/" + PORTAL_REPO + "/git/ref/heads/main", token)
        sha = base["object"]["sha"]
        branch = "automation/portal-intake-" + sha[:12]
        branch_ref = "refs/heads/" + branch
        try:
            github("POST", "/repos/" + PORTAL_REPO + "/git/refs", token,
                   {"ref": branch_ref, "sha": sha})
        except urllib.error.HTTPError as exc:
            if exc.code != 422:
                raise
            # Fail closed rather than overwrite a prior intake branch.
            raise ValueError("Portal intake branch already exists, review its prior PR") from None
        for p in candidates:
            content = json.dumps(p, ensure_ascii=False, indent=2) + "\n"
            github("PUT", "/repos/" + PORTAL_REPO + "/contents/data/portal-intake/" + p["id"] + ".json", token,
                   {"message": "chore(portal): queue editorial review for " + p["id"],
                    "branch": branch,
                    "content": base64.b64encode(content.encode("utf-8")).decode("ascii")})
        issue = github("POST", "/repos/" + PORTAL_REPO + "/pulls", token,
                       {"title": "chore(portal): review new portfolio product intake",
                        "head": branch, "base": "main", "draft": True,
                        "body": "Automatically proposed **non-public editorial intake only** for products newly registered in product-platform. This PR does NOT publish catalog pages. Review each intake, verify marketing claims and product URLs, then open a separate catalog/page update PR with platform snapshot refresh. No release/deploy authorized. Source product-platform registry."})
        print(json.dumps({"status": "DRAFT_INTAKE_PR_CREATED", "url": issue["html_url"],
                          "products": [p["id"] for p in candidates]}))
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError, urllib.error.HTTPError,
            urllib.error.URLError) as exc:
        # Never print token-bearing request objects.
        print("PORTAL_INTAKE_BLOCKED: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
