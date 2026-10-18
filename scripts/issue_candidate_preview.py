#!/usr/bin/env python3
"""Read one GitHub issue and export a non-executable candidate preview.

Uses GitHub API only for GET. Never runs model CLIs or changes GitHub state.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

from autonomy_backlog import prepare


def candidate(repo, number, get_issue):
    if not number.isdecimal() or not 1 <= int(number) <= 2_147_483_647:
        raise ValueError("Issue number must be a positive integer")
    issue = get_issue(f"repos/{repo}/issues/{int(number)}")
    if "pull_request" in issue:
        raise ValueError("A pull request is not a backlog issue")
    if issue.get("state") != "open":
        raise ValueError("Issue must be open")
    labels = {x["name"] for x in issue.get("labels", []) if isinstance(x, dict) and isinstance(x.get("name"), str)}
    if "agent-candidate" not in labels:
        raise ValueError("Issue lacks agent-candidate label")
    if not isinstance(issue.get("body"), str) or not issue["body"]:
        raise ValueError("Issue body required")
    return prepare(issue["body"], issue["html_url"])


def main():
    parser = argparse.ArgumentParser(description="Emit a fail-closed, read-only candidate artifact")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("GH_TOKEN"):
        parser.error("GH_TOKEN missing")
    if "/" not in args.repository or any(x in args.repository for x in ("..", " ", "\\", ":")):
        parser.error("Invalid repository")
    def get_issue(path):
        response = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)
        return json.loads(response.stdout)
    preview = candidate(args.repository, args.issue, get_issue)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Validated candidate: {preview['task_sha256']} (execution_allowed=false)")


if __name__ == "__main__":
    main()
