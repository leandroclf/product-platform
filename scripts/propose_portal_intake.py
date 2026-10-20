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


def create_draft_intake(candidates, token, *, api=github):
    """Create a single-commit review branch, then open a draft PR.

    Git objects are prepared before the branch ref is created so a failed blob,
    tree, or commit request cannot leave a partially populated remote branch.
    """
    if not candidates:
        return {"status": "PORTAL_INTAKE_UP_TO_DATE", "products": []}

    base = api("GET", "/repos/" + PORTAL_REPO + "/git/ref/heads/main", token)
    base_sha = base["object"]["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", base_sha):
        raise ValueError("Portal main returned an invalid commit SHA")
    branch = "automation/portal-intake-" + base_sha[:12]

    commit = api("GET", "/repos/" + PORTAL_REPO + "/git/commits/" + base_sha, token)
    base_tree = commit["tree"]["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", base_tree):
        raise ValueError("Portal main returned an invalid tree SHA")

    entries = []
    for product in candidates:
        path = "data/portal-intake/" + product["id"] + ".json"
        content = json.dumps(product, ensure_ascii=False, indent=2) + "\n"
        blob = api("POST", "/repos/" + PORTAL_REPO + "/git/blobs", token,
                   {"content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                    "encoding": "base64"})
        blob_sha = blob["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", blob_sha):
            raise ValueError("GitHub returned an invalid blob SHA")
        entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob_sha})

    tree = api("POST", "/repos/" + PORTAL_REPO + "/git/trees", token,
               {"base_tree": base_tree, "tree": entries})
    tree_sha = tree["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", tree_sha):
        raise ValueError("GitHub returned an invalid tree SHA")
    new_commit = api("POST", "/repos/" + PORTAL_REPO + "/git/commits", token,
                     {"message": "chore(portal): queue editorial review for new products",
                      "tree": tree_sha, "parents": [base_sha]})
    commit_sha = new_commit["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise ValueError("GitHub returned an invalid commit SHA")

    # The first mutable ref is created only after all immutable Git objects exist.
    try:
        api("POST", "/repos/" + PORTAL_REPO + "/git/refs", token,
            {"ref": "refs/heads/" + branch, "sha": commit_sha})
    except urllib.error.HTTPError as exc:
        if exc.code == 422:
            raise ValueError("Portal intake branch already exists, review its prior PR") from None
        raise
    pull = api("POST", "/repos/" + PORTAL_REPO + "/pulls", token,
               {"title": "chore(portal): review new portfolio product intake",
                "head": branch, "base": "main", "draft": True,
                "body": "Automatically proposed **non-public editorial intake only** for products newly registered in product-platform. This PR does NOT publish catalog pages. Review each intake, verify marketing claims and product URLs, then open a separate catalog/page update PR with platform snapshot refresh. No release/deploy authorized. Source product-platform registry."})
    return {"status": "DRAFT_INTAKE_PR_CREATED", "url": pull["html_url"],
            "products": [p["id"] for p in candidates]}


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
        # Prevent stale catalog snapshots from manufacturing irrelevant intake PRs.
        remote = github("GET", "/repos/" + PORTAL_REPO + "/contents/data/product-catalog.json?ref=main", token)
        remote_bytes = base64.b64decode(remote["content"])
        if json.loads(remote_bytes.decode("utf-8")) != site_catalog:
            raise ValueError("Local catalog differs from remote main; refresh before applying")
        # Git objects are prepared before a branch is created; the source SHA is
        # obtained from authenticated GitHub and never assumed.
        result = create_draft_intake(candidates, token)
        print(json.dumps(result))
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError, urllib.error.HTTPError,
            urllib.error.URLError) as exc:
        # Never print token-bearing request objects.
        print("PORTAL_INTAKE_BLOCKED: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
