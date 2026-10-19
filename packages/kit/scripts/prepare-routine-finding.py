#!/usr/bin/env python3
"""Safely prepare a review-only triage packet from a GitHub Routine Finding issue."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

VALID_STATES = {"new", "triaged", "accepted", "in_progress", "resolved", "dismissed"}
FIELDS = {"schema_version", "finding_id", "source_routine", "target_repository", "category", "severity", "observed_ref", "observed_at", "evidence_urls", "recommendation", "acceptance_criteria", "state"}

def parse_finding(body):
    """Parse the limited YAML envelope through the Kit's existing PyYAML dependency."""
    try:
        import yaml
    except ImportError as exc:
        raise ValueError("PyYAML is required; install existing Kit validation dependencies") from exc
    matches = re.findall(r"\x60\x60\x60yaml\s*([\s\S]*?)\x60\x60\x60", body)
    if len(matches) != 1:
        raise ValueError("expected exactly one fenced yaml block")
    payload = yaml.safe_load(matches[0])
    finding = payload.get("routine_finding") if isinstance(payload, dict) else None
    if not isinstance(finding, dict) or not FIELDS.issubset(finding):
        raise ValueError("incomplete Routine Finding v1")
    if finding["schema_version"] != 1 or finding["state"] not in VALID_STATES:
        raise ValueError("unsupported finding schema/state")
    if not isinstance(finding["evidence_urls"], list) or not finding["evidence_urls"]:
        raise ValueError("missing evidence")
    if not isinstance(finding["acceptance_criteria"], list) or not finding["acceptance_criteria"]:
        raise ValueError("missing acceptance criteria")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+:[a-z-]+:[a-z0-9-]+", finding["finding_id"]):
        raise ValueError("invalid finding_id")
    if not all(isinstance(u, str) and u.startswith("https://github.com/") for u in finding["evidence_urls"]):
        raise ValueError("untrusted evidence URLs")
    return finding

def prepare(issue, repository):
    if issue.get("state") != "OPEN":
        raise ValueError("only open issues can be triaged")
    finding = parse_finding(issue.get("body", ""))
    if finding["target_repository"] != repository or not finding["finding_id"].startswith(repository + ":"):
        raise ValueError("repository mismatch")
    if finding["state"] != "accepted":
        raise ValueError("issue must be explicitly marked accepted before handoff")
    url = issue.get("url", "")
    if not url.startswith("https://github.com/" + repository + "/issues/"):
        raise ValueError("unexpected issue URL")
    return {
        "kind": "routine-finding-triage-packet",
        "schema_version": 1,
        "source_issue": url,
        "finding_id": finding["finding_id"],
        "target_repository": repository,
        "objective": finding["recommendation"],
        "acceptance_criteria": finding["acceptance_criteria"],
        "evidence_urls": finding["evidence_urls"],
        "status": "ready_for_proposal_review",
        "next_step": "Generate a fully validated PlatformHandoff using OmniCLI/Kit; do not execute ai-team from this packet.",
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--issue", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
        parser.error("invalid --repo")
    completed = subprocess.run(
        ["gh", "issue", "view", str(args.issue), "--repo", args.repo, "--json", "body,state,url"],
        check=True, capture_output=True, text=True, timeout=30,
    )
    packet = prepare(json.loads(completed.stdout), args.repo)
    if args.out.exists():
        parser.error("output already exists (refusing overwrite)")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(args.out))

if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"triage blocked: {exc}", file=sys.stderr)
        sys.exit(2)
