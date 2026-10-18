#!/usr/bin/env python3
"""Read-only local AI-team acceptance evidence checker.

Does not run CLIs, authenticate, publish, or expose prompts/agent output.
Structural artifacts never prove authenticated model execution by themselves.
"""
import argparse
import json
from pathlib import Path
import re
import sys

from local_team import STAGES, plan_id, review_pass, validate_plan
from jsonschema import ValidationError

TASK_ID = re.compile(r"^[a-f0-9]{32}$")
SHA = re.compile(r"^[a-f0-9]{40}$")
EXPECTED_STAGES = ("plan", "implement", "validate", "review")


def object_file(folder, name):
    path = folder / name
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError(f"Missing, linked or oversized evidence: {name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Invalid evidence object: {name}")
    return value


def assess(path):
    path = Path(path)
    if path.is_symlink() or not path.is_dir() or not TASK_ID.fullmatch(path.name):
        raise ValueError("Expected existing local ai-team task directory (32 hex ID)")
    state = object_file(path, "state.json")
    blockers = []
    status = state.get("status")
    sha = state.get("head_sha")
    cycle = state.get("cycle")
    if status not in ("REVIEWED", "DELIVERED"):
        blockers.append("Task is not REVIEWED or DELIVERED")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        blockers.append("Missing valid reviewed HEAD")
    if type(cycle) is not int or cycle < 0 or cycle > 5:
        blockers.append("Invalid correction cycle")
    plan = state.get("plan")
    identifier = state.get("plan_id")
    if not isinstance(plan, dict) or not isinstance(identifier, str):
        blockers.append("Plan or plan ID absent")
    else:
        try:
            if plan_id(plan) != identifier:
                raise ValueError("Plan SHA mismatch")
            validate_plan(plan, plan["base_sha"])
            if plan.get("status") != "READY" or plan.get("risk") == "R3":
                raise ValueError("Plan is blocked or R3")
        except (ValueError, KeyError, TypeError, ValidationError) as exc:
            blockers.append("Plan integrity: " + str(exc)[:100])
    stage_runs = state.get("stage_runs")
    stage_summary = []
    if not isinstance(stage_runs, list):
        blockers.append("Missing stage execution records")
        stage_runs = []
    for stage in EXPECTED_STAGES:
        matching = [record for record in stage_runs
                    if isinstance(record, dict) and record.get("stage") == stage
                    and record.get("cycle") == cycle]
        role, provider = STAGES[stage]
        valid = bool(matching) and all(
            record.get("agent") == role and record.get("provider") == provider
            and record.get("started_at") is not None
            and record.get("ended_at") is not None
            and isinstance(record.get("requested_model"), str)
            for record in matching
        )
        if not valid:
            blockers.append(f"Missing or mismatched stage records: {stage}")
        stage_summary.append({
            "stage": stage, "agent": role, "provider": provider,
            "records": len(matching),
            "requested_models": sorted({str(x.get("requested_model")) for x in matching}),
            "resolved_model_confirmed": bool(matching) and all(bool(x.get("resolved_model")) for x in matching),
            "records_valid": valid,
        })
    if type(cycle) is int and 0 <= cycle <= 5 and isinstance(sha, str) and SHA.fullmatch(sha):
        try:
            tests = object_file(path, f"{cycle}-tests.json")
            if tests.get("head_sha") != sha or tests.get("exit_code") != 0 or not tests.get("checks"):
                blockers.append("Required tests missing, failed or not bound to reviewed HEAD")
        except (OSError, ValueError, json.JSONDecodeError):
            blockers.append("Test evidence missing or malformed")
        for stage in ("validate", "review"):
            try:
                value = object_file(path, f"{cycle}-{stage}.json")
                if not isinstance(plan, dict) or not isinstance(identifier, str) or not review_pass(
                    value, sha, STAGES[stage][0], plan, identifier
                ):
                    blockers.append(f"{stage} assessment did not pass exact HEAD and plan")
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, ValidationError):
                blockers.append(f"{stage} assessment missing or malformed")
    else:
        blockers.append("Cannot validate tests and reviews without valid HEAD/cycle")
    # Artifacts may be simulated. Model response authentication is external evidence.
    return {
        "schema_version": 1,
        "task_id": path.name,
        "status": status if isinstance(status, str) else "UNKNOWN",
        "head_sha": sha if isinstance(sha, str) and SHA.fullmatch(sha) else None,
        "cycle": cycle if type(cycle) is int else None,
        "stage_summary": stage_summary,
        "artifact_checks_pass": not blockers,
        "blockers": blockers,
        "authenticated_provider_execution_verified": False,
        "production_certified": False,
        "manual_acceptance_required": [
            "Inspect original provider CLI login, logs and model IDs on operator Linux",
            "Inspect actual diff, checks, scope, quotas, and a draft PR on reviewed HEAD",
            "Confirm no credentials in exported evidence; do not upload task-state or raw logs",
            "Owner reviews and merges PR manually; no deployment implied",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only AI-team task acceptance evidence")
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        output = assess(args.task_dir)
        data = json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            if args.output.resolve().is_relative_to(args.task_dir.resolve()):
                parser.error("Output must be outside task directory")
            args.output.write_text(data, encoding="utf-8")
        else:
            print(data, end="")
        return 0 if output["artifact_checks_pass"] else 2
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
