#!/usr/bin/env python3
"""Validate the end-to-end benchmark contract without running any model."""

from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evaluation" / "e2e-workloads.json"
ALLOWED_CLASSES = {"bug-fix","backend-api","refactoring","security","performance","brownfield","documentation","architecture-change"}
ALLOWED_CONDITIONS = {"single-openai","single-claude","team","human-assisted"}
REQUIRED_METRICS = {"verified_pass","acceptance_coverage","regression_count","review_findings","repair_cycles","elapsed_seconds"}

def fail(message: str) -> None:
    raise SystemExit(message)

def main() -> None:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if data.get("contract_version") != "1.0.0":
        fail("unsupported contract_version")
    workloads = data.get("workloads")
    if not isinstance(workloads, list) or not workloads:
        fail("workloads must be a non-empty list")
    ids=set()
    for w in workloads:
        wid=w.get("id")
        if not wid or wid in ids: fail(f"invalid or duplicate workload id: {wid!r}")
        ids.add(wid)
        if w.get("class") not in ALLOWED_CLASSES: fail(f"{wid}: invalid class")
        if not w.get("repository"): fail(f"{wid}: repository required")
        if not w.get("pinned_sha"): fail(f"{wid}: pinned_sha required")
        criteria=w.get("acceptance_criteria")
        if not isinstance(criteria,list) or not criteria: fail(f"{wid}: acceptance_criteria required")
        verifier=w.get("verifier")
        if not isinstance(verifier,dict) or not verifier.get("command"): fail(f"{wid}: verifier.command required")
        conditions=set(w.get("conditions",[]))
        if not conditions or not conditions <= ALLOWED_CONDITIONS: fail(f"{wid}: invalid conditions")
        metrics=set(w.get("required_metrics",[]))
        missing=REQUIRED_METRICS-metrics
        if missing: fail(f"{wid}: missing required metrics {sorted(missing)}")
    print(f"OK: {len(workloads)} end-to-end workload contracts validated")

if __name__ == "__main__":
    main()
