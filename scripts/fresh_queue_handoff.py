#!/usr/bin/env python3
"""Select one queue candidate and refetch its live GitHub issue before local handoff.

Read-only API access; writes only the explicitly requested local JSON file.
Never runs agents, changes issue labels, creates PRs or merges.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from issue_candidate_preview import candidate

REPO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
SHA = re.compile(r"^[a-f0-9]{64}$")


def select(queue, number, get_issue):
    if not isinstance(queue, dict) or queue.get("schema_version") != 1:
        raise ValueError("Unsupported queue schema")
    if queue.get("mode") != "PREVIEW_ONLY" or queue.get("execution_allowed") is not False:
        raise ValueError("Queue must be inert")
    repository = queue.get("repository")
    if not isinstance(repository, str) or not REPO.fullmatch(repository):
        raise ValueError("Invalid queue repository")
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise ValueError("Invalid issue number")
    items = queue.get("items")
    if not isinstance(items, list) or len(items) > 25:
        raise ValueError("Invalid queue candidates")
    matching = [i for i in items if isinstance(i, dict) and i.get("issue_number") == number]
    if len(matching) != 1:
        raise ValueError("Selected issue is missing or duplicated in queue")
    entry = matching[0]
    if entry.get("mode") != "PREVIEW_ONLY" or entry.get("execution_allowed") is not False:
        raise ValueError("Candidate is not inert")
    fingerprint = entry.get("task_sha256")
    if not isinstance(fingerprint, str) or not SHA.fullmatch(fingerprint):
        raise ValueError("Invalid task SHA256")
    expected_url = f"https://github.com/{repository}/issues/{number}"
    if entry.get("issue_url") != expected_url:
        raise ValueError("Queue issue URL does not match")
    if not isinstance(entry.get("target_repository"), str) or not REPO.fullmatch(entry["target_repository"]):
        raise ValueError("Invalid target repository")
    # candidate() re-reads the issue from GitHub and checks the open state,
    # label, canonical task schema and allowed risk classification.
    preview = candidate(repository, str(number), get_issue)
    if preview["issue_url"] != expected_url:
        raise ValueError("Current issue URL changed")
    if preview["task_sha256"] != fingerprint:
        raise ValueError("Issue changed since queue snapshot; regenerate queue")
    if preview["task"]["target_repository"] != entry["target_repository"]:
        raise ValueError("Target repository changed since queue snapshot")
    if preview["task"]["risk"] != entry.get("risk_claim"):
        raise ValueError("Risk claim changed since queue snapshot")
    return preview


def get_json(endpoint):
    output = subprocess.run(["gh", "api", endpoint], capture_output=True,
                            text=True, check=True)
    return json.loads(output.stdout)


def main():
    parser = argparse.ArgumentParser(description="Prepare one fresh candidate preview")
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("GH_TOKEN"):
        parser.error("GH_TOKEN required for read-only issue verification")
    if args.queue.stat().st_size > 128_000:
        parser.error("Queue artifact too large")
    if args.output.resolve() == args.queue.resolve():
        parser.error("Refuse to overwrite queue input")
    snapshot = json.loads(args.queue.read_text(encoding="utf-8"))
    payload = select(snapshot, args.issue, get_json)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True,
                                      ensure_ascii=False) + "\n", encoding="utf-8")
    print("Candidate refreshed:", payload["task_sha256"], "(execution_allowed=false)")


if __name__ == "__main__":
    main()
