#!/usr/bin/env python3
"""G6 deployment promotion policy: read-only, no cloud calls or deployment authority.

Checks the release plan and bounded operator-supplied evidence. Does NOT attest
CI, provider identity, deployment health, or approvals independently.
"""
import argparse
import json
from pathlib import Path
import re
import sys

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
NAME = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
ENVIRONMENTS = ("preview", "staging", "production")
REQUIRED = {"schema_version", "product", "source_sha", "artifact_sha256", "artifact_ref",
            "environment", "previous_artifact_sha256", "checks", "approval", "evidence"}
CHECKS = {"build", "unit", "security", "integration", "smoke", "health"}
EVIDENCE = {"source_sha", "artifact_sha256", "checks_sha", "checked_environment",
            "approved_by", "approved_source_sha", "approved_artifact_sha256",
            "approved_environment", "rollback_artifact_sha256"}


def errors(value):
    problems = []
    if not isinstance(value, dict):
        return ["plan must be a JSON object"]
    if set(value) != REQUIRED:
        problems.append("incorrect plan fields")
        return problems
    if value["schema_version"] != "1.0":
        problems.append("unsupported schema version")
    if not isinstance(value["product"], str) or not NAME.fullmatch(value["product"]):
        problems.append("invalid product")
    for field, pattern in (("source_sha", SHA40), ("artifact_sha256", SHA256)):
        if not isinstance(value[field], str) or not pattern.fullmatch(value[field]):
            problems.append("invalid " + field)
    if (not isinstance(value["artifact_ref"], str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/@:+-]{0,255}", value["artifact_ref"])
            or value["artifact_ref"].endswith((":latest", "/latest"))
            or not value["artifact_ref"].endswith("@sha256:" + str(value["artifact_sha256"]))):
        problems.append("artifact must use a pinned, non-latest reference")
    environment = value["environment"]
    if environment not in ENVIRONMENTS:
        problems.append("invalid environment")
    previous = value["previous_artifact_sha256"]
    if previous is not None and (not isinstance(previous, str) or not SHA256.fullmatch(previous)):
        problems.append("invalid rollback artifact SHA")
    if environment in ("staging", "production") and previous is None:
        problems.append("non-preview deployment requires prior rollback artifact")
    if previous == value["artifact_sha256"]:
        problems.append("rollback artifact must differ from candidate")
    checks = value["checks"]
    if (not isinstance(checks, dict) or set(checks) != CHECKS
            or any(type(item) is not bool for item in checks.values())):
        problems.append("checks must contain all explicit boolean gates")
    else:
        mandatory = {"build", "unit", "security"}
        if environment in ("staging", "production"):
            mandatory |= {"integration", "smoke", "health"}
        if not all(checks[k] for k in mandatory):
            problems.append("mandatory quality and health checks not passed")
    approval = value["approval"]
    if approval not in ("pending", "approved"):
        problems.append("invalid approval state")
    if environment == "production" and approval != "approved":
        problems.append("production requires explicit approval")
    evidence = value["evidence"]
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE:
        problems.append("incomplete evidence binding")
        return problems
    if (evidence["source_sha"] != value["source_sha"]
            or evidence["artifact_sha256"] != value["artifact_sha256"]):
        problems.append("evidence does not bind to source and artifact")
    if (evidence["checked_environment"] != environment
            or evidence["checks_sha"] != checks_hash(checks)):
        problems.append("evidence does not bind to environment and checks")
    if evidence["rollback_artifact_sha256"] != previous:
        problems.append("rollback evidence does not match prior artifact")
    if environment == "production":
        if (approval != "approved" or not isinstance(evidence["approved_by"], str)
                or not re.fullmatch(r"[A-Za-z0-9_.-]{2,80}", evidence["approved_by"])):
            problems.append("production approval identity missing")
        if (evidence["approved_source_sha"] != value["source_sha"]
                or evidence["approved_artifact_sha256"] != value["artifact_sha256"]
                or evidence["approved_environment"] != environment):
            problems.append("production approval must bind exact release and environment")
    elif any(evidence[k] is not None for k in
             ("approved_by", "approved_source_sha", "approved_artifact_sha256", "approved_environment")):
        problems.append("nonproduction plans must not claim a production approval")
    return problems


def checks_hash(checks):
    import hashlib
    if not isinstance(checks, dict):
        return None
    return hashlib.sha256(json.dumps(checks, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Read-only G6 deployment promotion contract")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    try:
        path = args.plan
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024:
            raise ValueError("untrusted plan path, symlink or oversized document")
        payload = json.loads(path.read_text(encoding="utf-8"))
        issues = errors(payload)
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"gate": "G6", "decision": "BLOCK", "errors": ["invalid or unreadable deployment plan"]}))
        return 2
    print(json.dumps({"gate": "G6", "decision": "READY_FOR_OPERATOR_REVIEW" if not issues else "BLOCK",
                      "errors": issues, "authorized_to_deploy": False}, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
