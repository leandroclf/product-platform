#!/usr/bin/env python3
"""Validate an evidence-backed issue and build an inert ai-team handoff.

This module never starts agents, performs GitHub writes, merges or executes shell.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

FIELDS = {"source", "target_repository", "problem", "evidence_url",
          "acceptance_criteria", "risk", "rollback", "max_cycles"}
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
URL = re.compile(r"^https://[^\s<>]+$")
BLOCK = re.compile(r"```autonomy-task\s*([\s\S]*?)\s*```", re.IGNORECASE)


def parse_issue(body):
    blocks = BLOCK.findall(body)
    if len(blocks) != 1:
        raise ValueError("Exactly one fenced autonomy-task JSON block is required")
    try:
        item = json.loads(blocks[0])
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid task JSON") from exc
    if not isinstance(item, dict) or set(item) != FIELDS:
        raise ValueError("Unexpected or missing task fields")
    for field in ("source", "target_repository", "problem", "evidence_url", "rollback"):
        if not isinstance(item[field], str) or not item[field].strip():
            raise ValueError(f"Invalid field: {field}")
        item[field] = item[field].strip()
    if not REPOSITORY.fullmatch(item["target_repository"]):
        raise ValueError("Invalid target repository")
    if not URL.fullmatch(item["evidence_url"]):
        raise ValueError("Evidence must be an HTTPS link")
    if item["risk"] not in ("R0", "R1"):
        raise ValueError("Only R0/R1 candidates are eligible for handoff")
    if not isinstance(item["max_cycles"], int) or isinstance(item["max_cycles"], bool) or not 1 <= item["max_cycles"] <= 3:
        raise ValueError("max_cycles must be between 1 and 3")
    criteria = item["acceptance_criteria"]
    if not isinstance(criteria, list) or not 1 <= len(criteria) <= 10 or not all(isinstance(c, str) and c.strip() for c in criteria):
        raise ValueError("Nonempty acceptance criteria required")
    item["acceptance_criteria"] = [c.strip() for c in criteria]
    if any(len(str(v)) > 4000 for v in item.values()):
        raise ValueError("Field too large")
    return item


def prepare(body, issue_url):
    if not URL.fullmatch(issue_url):
        raise ValueError("Issue URL must be HTTPS")
    task = parse_issue(body)
    canonical = json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": 1,
        "mode": "PREVIEW_ONLY",
        "status": "awaiting_independent_triage",
        "issue_url": issue_url,
        "task_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "task": task,
        "execution_allowed": False,
        "note": "A human or separately authorized triage policy must mark ready; ai-team execution and merge are not invoked.",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate non-executable ai-team task preview")
    parser.add_argument("--body-file", type=Path, required=True)
    parser.add_argument("--issue-url", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = prepare(args.body_file.read_text(encoding="utf-8"), args.issue_url)
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(data, encoding="utf-8")
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
