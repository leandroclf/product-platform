#!/usr/bin/env python3
"""Resolve a live, opt-in PR before the integrator receives any write token."""
import json
import os
from pathlib import Path
import re

from agent_review_gate import api


class SkipCandidate(ValueError):
    """A valid event without an eligible opt-in PR has no work to perform."""


def resolve(event, repo, event_name):
    if event_name == "workflow_run":
        run = event["workflow_run"]
        if (run.get("conclusion") != "success"
                or run.get("path") != ".github/workflows/agent-review-gate.yml"
                or run.get("head_repository", {}).get("full_name") != repo):
            raise ValueError("Not a successful repository review-gate run")
        candidates = run.get("pull_requests", [])
        if not candidates:
            # Review-triggered runs have an empty pull_requests array on GitHub.
            candidates = api(f"repos/{repo}/commits/{run['head_sha']}/pulls?per_page=100")
            if not isinstance(candidates, list):
                raise ValueError("Invalid associated-PR response")
            candidates = [pr for pr in candidates if pr.get("state") == "open"
                          and pr.get("head", {}).get("sha") == run["head_sha"]]
        if not candidates:
            raise SkipCandidate("No open PR matches this completed gate run")
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
    if not re.fullmatch(r"[1-9][0-9]*", str(number)):
        raise ValueError("Invalid PR number")
    pr = api(f"repos/{repo}/pulls/{number}")
    if (pr["state"] != "open" or pr["draft"]
            or pr["head"]["repo"]["full_name"] != repo
            or pr["base"]["repo"]["full_name"] != repo
            or pr["base"]["ref"] != event["repository"]["default_branch"]
            or "agent-auto-merge" not in {label["name"] for label in pr["labels"]}):
        raise SkipCandidate("PR is not an open, same-repository, opt-in default-branch candidate")
    head = pr["head"]["sha"]
    if expected is not None and expected != head:
        raise ValueError("PR changed since the triggering event")
    return int(number), head


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    try:
        number, head = resolve(event, os.environ["GH_REPO"], os.environ["GITHUB_EVENT_NAME"])
    except SkipCandidate as exc:
        print(str(exc))
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write("eligible=false\n")
        return
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"eligible=true\nnumber={number}\nhead={head}\n")


if __name__ == "__main__":
    main()
