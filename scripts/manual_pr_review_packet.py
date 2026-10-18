#!/usr/bin/env python3
"""Read-only pull-request review packet. No trusted reviewer / merge decisions."""
import argparse
import json
import os
from pathlib import PurePosixPath
import subprocess

CRITICAL_PREFIXES = (
    ".github/workflows/", ".github/actions/", "infra/", "terraform/",
    "migrations/", "database/migrations/", "security/", "secrets/",
)
CRITICAL_EXACT = {
    "CODEOWNERS", "AGENTS.md", "scripts/agent_review_gate.py",
    "scripts/audit_autonomy_readiness.py",
}
BUDGET_FILES = 2000


def classify(path):
    if path.startswith(CRITICAL_PREFIXES) or PurePosixPath(path).name in CRITICAL_EXACT or path in CRITICAL_EXACT:
        return "R2"
    if path.endswith((".lock", "-lock.json")) or path in ("package.json", "pyproject.toml"):
        return "R2-review"
    return "R1-candidate"


def summarize(pr, changed):
    if not isinstance(pr, dict) or not isinstance(changed, list):
        raise ValueError("Unexpected GitHub API response")
    sha = pr.get("head", {}).get("sha", "")
    if not isinstance(sha, str) or len(sha) != 40 or any(x not in "0123456789abcdef" for x in sha.lower()):
        raise ValueError("Invalid PR head SHA")
    if len(changed) > BUDGET_FILES or not changed:
        raise ValueError("Unexpected PR file count")
    files = []
    for entry in changed:
        path = entry.get("filename")
        if not isinstance(path, str) or not path or "\n" in path or "|" in path:
            raise ValueError("Unsafe or missing file path")
        files.append({"path": path, "risk": classify(path), "status": entry.get("status", "unknown"),
                      "additions": entry.get("additions", 0), "deletions": entry.get("deletions", 0)})
    elevated = [f for f in files if f["risk"] != "R1-candidate"]
    return {"number": pr.get("number"), "title": str(pr.get("title", "")), "head_sha": sha,
            "author": str(pr.get("user", {}).get("login", "")), "files": files,
            "elevated": elevated, "manual_review_required": True,
            "automation_approval": False}


def render(report):
    lines = [
        "## Manual PR review packet (informational only)",
        f"- PR: #{report['number']} — {report['title']}",
        f"- Head SHA: \`{report['head_sha']}\`",
        f"- Author: {report['author']}",
        "- **Review and merge must be performed manually.** This packet is not an approval.",
        f"- Files: {len(report['files'])}; elevated attention: {len(report['elevated'])}",
        "",
        "| Path | Risk flag | GitHub status | + / - |",
        "|---|---|---|---|",
    ]
    for f in report["files"]:
        path = f["path"].replace("\`", "&#96;")
        lines.append(f"| \`{path}\` | {f['risk']} | {f['status']} | {f['additions']} / {f['deletions']} |")
    lines += [
        "", "### Human review checklist",
        "- [ ] Inspect the actual diff, dependencies and test coverage",
        "- [ ] Confirm product scope, capability reuse, rollback and CI results",
        "- [ ] Confirm base branch rulesets, required checks and PR head unchanged",
        "- [ ] Treat any R2 / R2-review flag as requiring elevated scrutiny",
        "- [ ] Review security findings and production impact before clicking Merge",
        "", "Risk flags are path heuristics only; R1-candidate is **not** security certification.",
    ]
    return "\n".join(lines) + "\n"


def get_json(url):
    result = subprocess.run(["gh", "api", url], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def fetch_files(repo, number, getter):
    result = []
    for page in range(1, 22):
        batch = getter(f"repos/{repo}/pulls/{number}/files?per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("Invalid file response")
        result.extend(batch)
        if len(result) > BUDGET_FILES:
            raise ValueError("PR exceeds audit file budget")
        if len(batch) < 100:
            return result
    raise ValueError("File pagination incomplete")


def main():
    parser = argparse.ArgumentParser(description="Read-only manual PR report")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--number", required=True, type=int)
    args = parser.parse_args()
    if not (1 <= args.number <= 2_147_483_647):
        parser.error("Invalid PR number")
    if not os.environ.get("GH_TOKEN"):
        parser.error("GH_TOKEN required")
    pr = get_json(f"repos/{args.repo}/pulls/{args.number}")
    changed = fetch_files(args.repo, args.number, get_json)
    # Fail closed if files belong to a different head revision than the first API read.
    again = get_json(f"repos/{args.repo}/pulls/{args.number}")
    if pr.get("head", {}).get("sha") != again.get("head", {}).get("sha"):
        parser.error("PR changed while collecting review evidence")
    report = summarize(pr, changed)
    markdown = render(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as out:
            out.write(markdown)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
