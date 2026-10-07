#!/usr/bin/env python3
"""Validate synthetic benchmark evidence.

Synthetic evidence is useful for exercising scoring/reporting only. It MUST NOT be
reported as provider performance, token usage, cost, latency, or quality evidence.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"evaluation"/"simulations"/"english-coach-restore.json"
d=json.loads(P.read_text())
assert d["evidence_kind"]=="synthetic-simulation"
assert d["provider_execution"] is False
assert d["workload"]["pinned_sha"]=="2883d73b173b8fadefe38f8a3479409a9649d228"
conditions=d["conditions"]
assert {x["id"] for x in conditions}=={"single-openai","single-claude","team"}
for x in conditions:
    assert x["verified_pass"] is True
    assert x["acceptance_coverage"]==1.0
    assert x["regression_count"]==0
    assert x["tokens"] is None and x["cost_usd"] is None and x["elapsed_seconds"] is None
print("OK: synthetic benchmark evidence is explicit, complete and non-empirical")
