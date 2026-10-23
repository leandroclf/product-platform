#!/usr/bin/env python3
"""Fail closed unless a distinct GitHub reviewer approved the current PR head."""
import json
import os
import subprocess
import sys

BLOCKED_PREFIXES = (
    ".github/workflows/", ".github/actions/", "infra/", "terraform/",
    "migrations/", "database/migrations/", "security/", "secrets/",
    "scripts/agent_review_gate.py", "scripts/audit_autonomy_readiness.py",
    "scripts/agent_merge_candidate.py",
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
    protected = [name for f in files for name in (f["filename"], f.get("previous_filename", ""))
                 if name.startswith(BLOCKED_PREFIXES) or name.split("/")[-1] in BLOCKED_NAMES]
    security_review = bool(protected) and os.environ.get("ALLOW_SECURITY_REVIEW") == "true"
    if protected and not security_review:
        sys.exit(f"Protected path requires separate security policy: {protected[0]}")
    mode = os.environ.get("AGENT_REVIEW_MODE", "").strip() or "manual"
    if mode == "manual" and not security_review:
        print("Manual transition: structural scope and head SHA passed. Human PR review/merge remains required; no independent approval attested.")
        return
    if mode not in {"manual", "independent"}:
        sys.exit("Unknown AGENT_REVIEW_MODE; fail closed")
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
    reviewer_variable = "SECURITY_REVIEWERS" if security_review else "TRUSTED_REVIEWERS"
    trusted = {x.strip().lower() for x in os.environ.get(reviewer_variable, "").split(",") if x.strip()}
    if not trusted:
        sys.exit(f"{reviewer_variable} not configured; fail closed")
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
    print("Independent security approval verified; protected PR requires manual merge" if security_review
          else "Independent GitHub approval verified for current head")

if __name__ == "__main__":
    main()
