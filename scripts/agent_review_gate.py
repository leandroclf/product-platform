#!/usr/bin/env python3
"""Fail closed unless a distinct GitHub reviewer approved the current PR head."""
import json
import os
import subprocess
import sys

BLOCKED_PREFIXES = (
    ".github/workflows/", ".github/actions/", "infra/", "terraform/",
    "migrations/", "database/migrations/", "security/", "secrets/",
)
BLOCKED_NAMES = {"CODEOWNERS", "AGENTS.md"}

def api(path):
    return json.loads(subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout)

def main():
    repo = os.environ["GH_REPO"]
    number = os.environ["PR_NUMBER"]
    head = os.environ["HEAD_SHA"]
    pr = api(f"repos/{repo}/pulls/{number}")
    if pr["head"]["sha"] != head:
        sys.exit("Head SHA changed; review must be rerun")
    files = []
    page = 1
    while True:
        batch = api(f"repos/{repo}/pulls/{number}/files?per_page=100&page={page}")
        files.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    if not files:
        sys.exit("Empty PR")
    for f in files:
        name = f["filename"]
        if name.startswith(BLOCKED_PREFIXES) or name.split("/")[-1] in BLOCKED_NAMES:
            sys.exit(f"Protected path requires separate security policy: {name}")
    reviews = []
    page = 1
    while True:
        batch = api(f"repos/{repo}/pulls/{number}/reviews?per_page=100&page={page}")
        reviews.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    latest_by_reviewer = {}
    for review in reviews:
        login = (review.get("user") or {}).get("login", "").lower()
        if login and review.get("state") in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            latest_by_reviewer[login] = review
    author = pr["user"]["login"].lower()
    trusted = {x.strip().lower() for x in os.environ.get("TRUSTED_REVIEWERS", "").split(",") if x.strip()}
    if not trusted:
        sys.exit("TRUSTED_REVIEWERS not configured; fail closed")
    approvals = [
        r for r in latest_by_reviewer.values()
        if r.get("state") == "APPROVED"
        and r.get("commit_id") == head
        and r.get("user", {}).get("login", "").lower() != author
        and r.get("user", {}).get("login", "").lower() in trusted
    ]
    if not approvals:
        sys.exit("No independent approval for current head SHA")
    if any(r.get("state") == "CHANGES_REQUESTED" for r in latest_by_reviewer.values()):
        sys.exit("Unresolved changes requested")
    print("Independent GitHub approval verified for current head")

if __name__ == "__main__":
    main()
