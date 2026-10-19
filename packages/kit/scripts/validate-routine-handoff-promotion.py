#!/usr/bin/env python3
"""Validate promotion of an approved Routine Finding packet to a real PlatformHandoff.

Never invokes a model, runs ai-team, changes GitHub state or manufactures SHA pins.
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate-platform-handoff.py"

def load_validator():
    spec = importlib.util.spec_from_file_location("platform_handoff_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def check(packet, handoff, registry=None):
    if not isinstance(packet, dict) or packet.get("kind") != "routine-finding-triage-packet":
        raise ValueError("expected Routine Finding triage packet")
    if packet.get("status") != "ready_for_proposal_review":
        raise ValueError("finding not accepted for proposal review")
    repository = packet.get("target_repository")
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid repository")
    issue_url = packet.get("source_issue", "")
    if not re.fullmatch(r"https://github\.com/" + re.escape(repository) + r"/issues/[1-9][0-9]*", issue_url):
        raise ValueError("invalid source issue")
    if not isinstance(handoff, dict) or handoff.get("schema_version") != "1.0":
        raise ValueError("expected full PlatformHandoff v1.0")
    proposal = handoff.get("proposal")
    if not isinstance(proposal, dict):
        raise ValueError("missing proposal")
    if proposal.get("repository", {}).get("url") != "https://github.com/" + repository:
        raise ValueError("handoff repository differs from source issue")
    if not proposal.get("repository", {}).get("base_sha"):
        raise ValueError("handoff must pin the repository base SHA")
    # There must be explicit traceability. Proposal IDs are controlled by the creator,
    # so embed the issue URL in the objective rather than assuming any issue ID scheme.
    if issue_url not in proposal.get("objective", ""):
        raise ValueError("handoff objective must reference originating issue URL")
    if not isinstance(proposal.get("acceptance"), dict) or not set(packet.get("acceptance_criteria", [])).issubset(set(proposal["acceptance"].get("criteria", []))):
        raise ValueError("handoff omitted Routine Finding acceptance criteria")
    validator = load_validator()
    errors = validator.violations(handoff, Path(registry) if registry else validator.REGISTRY)
    if errors:
        raise ValueError("Kit G1 rejected handoff: " + "; ".join(errors))
    return {"result": "valid_for_manual_execution_review", "source_issue": issue_url,
            "proposal_id": proposal["proposal_id"], "target_repository": repository,
            "base_sha": proposal["repository"]["base_sha"],
            "note": "Validation only; human review and ai-team gates remain required."}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--packet", required=True, type=Path)
    p.add_argument("--handoff", required=True, type=Path)
    p.add_argument("--registry", type=Path)
    args = p.parse_args()
    try:
        result = check(json.loads(args.packet.read_text()), json.loads(args.handoff.read_text()), args.registry)
    except (ValueError, OSError, ImportError, KeyError, TypeError) as exc:
        print("promotion blocked: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
