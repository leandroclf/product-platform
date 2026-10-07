#!/usr/bin/env python3
"""Run bounded repository checks and record observed evidence, without provider calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def collect(workspace, python, overrides, timeout, only=None):
    portfolio = json.loads((ROOT / "contracts/portfolio-products.json").read_text())
    commands = {
        "product-platform-kit": [["node", "scripts/validate-architecture.cjs"], ["node", "scripts/validate-capability-registry.cjs"], ["node", "scripts/validate-retired-platform-names.cjs"], ["{python}", "scripts/conformance-product-event.py"]],
        "product-platform-cli": [["{python}", "-m", "pytest"], ["{python}", "-m", "omnicli", "lab", "verify", "--json"]],
        "product-platform-engineering-team": [["{python}", "scripts/validate.py"], ["{python}", "scripts/validate_hardening.py"], ["{python}", "-m", "unittest", "discover", "-s", "tests/unit", "-q"]],
        "product-platform-harness": [["npm", "run", "validate"]],
        "vehicle-tracking": [["npm", "run", "validate:product-contract"], ["npm", "test"], ["npm", "run", "typecheck"], ["npm", "run", "build"]],
        "bussola-financeira": [["{python}", "-m", "pytest", "-q"]],
        "lf-worldbank-risk-pricing": [["{python}", "-m", "pytest", "-q"]],
        "lf-openalex-enrichment-mvp": [["{python}", "-m", "pytest", "-q"]],
        "lf-wikidata-entity-graph": [["{python}", "-m", "pytest", "-q"]],
        "agentic-travel-engine": [["{python}", "-m", "pytest", "-q"]],
        "fivem-server-monitor-pro": [["npm", "run", "verify"]],
        "professional-english-coach": [["npm", "run", "check"]],
    }
    names = portfolio["platform_repositories"] + [p["repository"] for p in portfolio["products"]]
    if only:
        if set(only) - set(names):
            raise ValueError("unknown repository selection")
        names = [name for name in names if name in only]
    result = {"schema_version": 1, "observed_at": datetime.now(timezone.utc).isoformat(), "scope": "local automated checks; not live-provider or production acceptance", "repositories": []}
    env = {k: v for k, v in os.environ.items() if not any(word in k.upper() for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))}
    env.update(PYTHONDONTWRITEBYTECODE="1", NEXT_TELEMETRY_DISABLED="1")
    for name in names:
        repo = workspace / name
        def git(*args):
            return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
        record = {"repository": name, "base_sha": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"), "working_tree": git("status", "--porcelain"), "checks": []}
        for template in commands[name]:
            command = [overrides.get(name, python) if arg == "{python}" else arg for arg in template]
            check = {"command": command}
            started = datetime.now(timezone.utc)
            try:
                proc = subprocess.run(command, cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
                output = proc.stdout.decode("utf-8", errors="replace")
                check.update(status="PASS" if proc.returncode == 0 else "FAIL", exit_code=proc.returncode)
            except subprocess.TimeoutExpired as exc:
                output = (exc.stdout or b"").decode("utf-8", errors="replace")
                check.update(status="TIMEOUT", exit_code=None)
            except FileNotFoundError as exc:
                output = str(exc)
                check.update(status="NOT_RUN", exit_code=None)
            check.update(duration_seconds=round((datetime.now(timezone.utc) - started).total_seconds(), 2), output_sha256=hashlib.sha256(output.encode()).hexdigest(), output_tail=output[-6000:])
            record["checks"].append(check)
            print(f"{name}: {check['status']} {' '.join(command)}", flush=True)
        result["repositories"].append(record)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--python", default="python3")
    parser.add_argument("--python-override", action="append", default=[], metavar="REPOSITORY=EXECUTABLE")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", action="append", help="Repeat to verify only repositories changed since the baseline")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    report = collect(args.workspace.resolve(), args.python, dict(item.split("=", 1) for item in args.python_override), args.timeout, args.only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Evidence: {args.output}")
