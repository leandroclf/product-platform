#!/usr/bin/env python3
"""Local opt-in ai-team runner from a verified, still-untrusted candidate preview.

Dry-run is default. Execution requires --execute AND an exact fingerprint.
No shell, push, PR, merge or deploy actions are performed here.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

from verified_ai_team_handoff import build_request
from issue_candidate_preview import candidate

ISSUE_URL = re.compile(r"^https://github[.]com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/([1-9][0-9]*)$")

GITHUB_ORIGIN = re.compile(
    r"^(?:https://github[.]com/|git@github[.]com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:[.]git)?$"
)


def command(argv, cwd):
    return subprocess.run(argv, cwd=cwd, text=True, check=True, capture_output=True).stdout.strip()


def inspect_target(target, expected_repo, run=command):
    root = Path(target).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Target is not a directory")
    top = Path(run(["git", "rev-parse", "--show-toplevel"], root)).resolve(strict=True)
    if top != root:
        raise ValueError("Target must be the Git repository root")
    origin = run(["git", "remote", "get-url", "origin"], root)
    match = GITHUB_ORIGIN.fullmatch(origin)
    if not match or match.group(1).lower() != expected_repo.lower():
        raise ValueError("Git origin does not match candidate target_repository")
    status = run(["git", "status", "--porcelain=v1", "--untracked-files=all"], root)
    if status:
        raise ValueError("Working tree is not clean")
    branch = run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], root)
    if not branch:
        raise ValueError("Detached HEAD is not supported")
    return root, branch


def plan(preview, target, run=command):
    request = build_request(preview)
    root, branch = inspect_target(target, request["target_repository"], run=run)
    return {
        "mode": "PREVIEW_ONLY",
        "execution_allowed": False,
        "repository": request["target_repository"],
        "target": str(root),
        "branch": branch,
        "task_sha256": request["task_sha256"],
        "command": ["ai-team", "run", request["ai_team_request"]],
        "checks_required": request["required_checks"],
    }



def github_issue(endpoint):
    return json.loads(subprocess.run(["gh", "api", endpoint], capture_output=True,
                                     text=True, check=True).stdout)


def verify_live(preview, get_issue=github_issue):
    """Read live issue; reject closed, unlabeled and edited tasks before agents run."""
    local = build_request(preview)
    match = ISSUE_URL.fullmatch(local["issue_url"])
    if not match:
        raise ValueError("Invalid source issue URL")
    repository, number = match.groups()
    current = candidate(repository, number, get_issue)
    if current["issue_url"] != local["issue_url"]:
        raise ValueError("Current issue URL differs from preview")
    if current["task_sha256"] != local["task_sha256"]:
        raise ValueError("Issue changed since candidate preview; refresh queue and handoff")
    return current

def execute(preview, target, confirm_hash, run=command, get_issue=github_issue):
    summary = plan(preview, target, run=run)
    if confirm_hash != summary["task_sha256"]:
        raise ValueError("Explicit SHA256 confirmation does not match")
    verify_live(preview, get_issue=get_issue)
    if not shutil.which("ai-team"):
        raise ValueError("ai-team is not installed in PATH")
    # The user's local doctor checks authenticated CLIs, Docker and project readiness.
    run(["ai-team", "doctor"], Path(summary["target"]))
    # Recheck target just before execution to prevent use after a changed checkout.
    inspect_target(summary["target"], summary["repository"], run=run)
    verify_live(preview, get_issue=get_issue)
    return run(summary["command"], Path(summary["target"]))


def main():
    parser = argparse.ArgumentParser(description="Preview or explicitly run verified local ai-team request")
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-hash", default="")
    args = parser.parse_args()
    if args.preview.stat().st_size > 128_000:
        parser.error("Preview too large")
    request = json.loads(args.preview.read_text(encoding="utf-8"))
    try:
        if args.execute:
            print(execute(request, args.target, args.confirm_hash))
        else:
            output = plan(request, args.target)
            print(json.dumps(output, ensure_ascii=False, indent=2))
    except (ValueError, subprocess.CalledProcessError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
