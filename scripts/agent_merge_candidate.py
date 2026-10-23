#!/usr/bin/env python3
"""Resolve a live, opt-in PR before the integrator receives any write token."""
import json
import os
from pathlib import Path

from agent_review_gate import api


def resolve(event, repo, event_name):
    if event_name == "workflow_run":
        run = event["workflow_run"]
        if (run.get("conclusion") != "success"
                or run.get("path") != ".github/workflows/agent-review-gate.yml"
                or run.get("head_repository", {}).get("full_name") != repo):
            raise ValueError("Not a successful repository review-gate run")
        candidates = run.get("pull_requests", [])
        if len(candidates) != 1:
            raise ValueError("Expected exactly one associated PR; use workflow_dispatch to retry")
        number = candidates[0]["number"]
        expected = candidates[0]["head"]["sha"]
    elif event_name == "pull_request_target":
        number = event["pull_request"]["number"]
        expected = event["pull_request"]["head"]["sha"]
    elif event_name == "workflow_dispatch":
        number = event["inputs"]["pr_number"]
        expected = None
    else:
        raise ValueError("Unsupported merge trigger")
    if not str(number).isdigit() or int(number) < 1:
        raise ValueError("Invalid PR number")
    pr = api(f"repos/{repo}/pulls/{number}")
    if (pr["state"] != "open" or pr["draft"]
            or pr["head"]["repo"]["full_name"] != repo
            or pr["base"]["repo"]["full_name"] != repo
            or pr["base"]["ref"] != event["repository"]["default_branch"]
            or "agent-auto-merge" not in {label["name"] for label in pr["labels"]}):
        raise ValueError("PR is not an open, same-repository, opt-in default-branch candidate")
    head = pr["head"]["sha"]
    if expected is not None and expected != head:
        raise ValueError("PR changed since the triggering event")
    return int(number), head


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    number, head = resolve(event, os.environ["GH_REPO"], os.environ["GITHUB_EVENT_NAME"])
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"number={number}\nhead={head}\n")


if __name__ == "__main__":
    main()
