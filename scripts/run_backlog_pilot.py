#!/usr/bin/env python3
"""One-command, explicitly authorized local backlog pilot using existing ai-team.

Read-only GitHub during selection. No PR, push, review or merge operations.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

from backlog_candidate_queue import build_queue
from fresh_queue_handoff import select
from local_ai_team_launcher import plan, execute

REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")


def github_get(path):
    response = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)
    return json.loads(response.stdout)


def pilot(repository, number, target, *, execute_requested=False, confirm_hash="",
          get_issue=github_get, plan_run=plan, execute_run=execute):
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
        raise ValueError("Invalid backlog repository")
    if type(number) is not int or not 1 <= number <= 2_147_483_647:
        raise ValueError("Invalid issue number")
    # Read the selected GitHub issue. build_queue performs the exact same
    # eligibility checks as the scheduled backlog workflow.
    issue = get_issue(f"repos/{repository}/issues/{number}")
    snapshot = build_queue([issue], repository, limit=1)
    if len(snapshot["items"]) != 1:
        reason = snapshot["rejected"][0]["reason"] if snapshot["rejected"] else "Issue not eligible"
        raise ValueError(reason)
    # Select refetches the live issue to detect a change even during preflight.
    preview = select(snapshot, number, get_issue)
    summary = plan_run(preview, target)
    if not execute_requested:
        return {
            "mode": "PREVIEW_ONLY", "execution_allowed": False,
            "issue_url": preview["issue_url"],
            "task_sha256": preview["task_sha256"],
            "repository": summary["repository"],
            "target": summary["target"],
            "branch": summary["branch"],
            "required_checks": summary["checks_required"],
            "next_step": "Verify task and run --execute --confirm-hash with this exact SHA256",
        }
    if not confirm_hash or confirm_hash != preview["task_sha256"]:
        raise ValueError("Explicit task SHA256 confirmation required")
    # The existing launcher invokes doctor, checks clean repo, re-reads live
    # GitHub issue before and after doctor, then invokes the authenticated ai-team.
    result = execute_run(preview, target, confirm_hash)
    return {"mode": "LOCAL_AI_TEAM_RUN", "issue_url": preview["issue_url"],
            "task_sha256": preview["task_sha256"],
            "result": result, "automatic_merge": False}


def main():
    parser = argparse.ArgumentParser(description="Inspect or explicitly run one backlog issue locally")
    parser.add_argument("--repo", default="leandroclf/product-platform")
    parser.add_argument("--issue", required=True, type=int)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-hash", default="")
    args = parser.parse_args()
    try:
        result = pilot(args.repo, args.issue, args.target,
                       execute_requested=args.execute, confirm_hash=args.confirm_hash)
    except (ValueError, OSError, subprocess.CalledProcessError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
