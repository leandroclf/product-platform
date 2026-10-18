#!/usr/bin/env python3
"""Deduplicated radar finding intake. Dry-run by default; explicit --apply."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from autonomy_backlog import parse_issue

MAX_ITEMS = 50


def key_for(task):
    fields = [task["source"], task["target_repository"].lower(), task["evidence_url"]]
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def validate_findings(data):
    if not isinstance(data, list) or not 1 <= len(data) <= MAX_ITEMS:
        raise ValueError("Expected 1-50 findings")
    result, seen = [], set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Finding must be an object")
        task = parse_issue("\u0060\u0060\u0060autonomy-task\n" + json.dumps(item, ensure_ascii=False) + "\n\u0060\u0060\u0060")
        key = key_for(task)
        if key in seen:
            raise ValueError("Duplicate source/target/evidence within batch")
        seen.add(key)
        result.append((key, task))
    return result


def issue_body(key, task):
    payload = json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True)
    return (
        "<!-- autonomy-backlog-key:" + key + " -->\n"
        "Proposta de radar: requer triagem de evidências e risco. "
        "Não autoriza execução de agente, aprovação ou merge.\n\n"
        "\u0060\u0060\u0060autonomy-task\n" + payload + "\n\u0060\u0060\u0060\n"
        "\nStatus: candidate. Não promover automaticamente a ready."
    )


def actions(findings, existing):
    known = set()
    for issue in existing:
        if issue.get("pull_request"):
            continue
        body = issue.get("body") or ""
        known.update(re.findall(r"<!-- autonomy-backlog-key:([a-f0-9]{64}) -->", body))
    return [{"key": key, "action": "skip_existing" if key in known else "create",
             "title": "[candidate] " + task["problem"][:120],
             "body": issue_body(key, task)} for key, task in findings]


def gh(*argv):
    return json.loads(subprocess.run(["gh", "api", *argv], check=True, text=True,
                                     capture_output=True).stdout)


def list_existing(repo, get=gh):
    issues = []
    for page in range(1, 21):
        batch = get(f"repos/{repo}/issues?state=all&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("Invalid issue listing")
        issues.extend(batch)
        if len(batch) < 100:
            return issues
    raise ValueError("Incomplete issue pagination; refuse writes")


def run_intake(items, repo, get=gh, write=gh, apply=False):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repo):
        raise ValueError("Invalid central repository")
    findings = validate_findings(items)
    decisions = actions(findings, list_existing(repo, get))
    if apply:
        for item in decisions:
            if item["action"] == "create":
                created = write("-X", "POST", f"repos/{repo}/issues",
                                "-f", "title=" + item["title"], "-f", "body=" + item["body"])
                item["created_url"] = created["html_url"]
    return [{"key": d["key"], "action": d["action"],
             **({"created_url": d["created_url"]} if "created_url" in d else {})}
            for d in decisions]


def main():
    parser = argparse.ArgumentParser(description="Radar finding intake with deduplication")
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--repo", default="leandroclf/product-platform")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.findings.stat().st_size > 200_000:
        parser.error("Input too large")
    raw = json.loads(args.findings.read_text(encoding="utf-8"))
    print(json.dumps(run_intake(raw, args.repo, apply=args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
