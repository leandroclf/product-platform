#!/usr/bin/env python3
"""Verify release SHA and artifact bytes independently of self-declared G6 evidence.

Offline, read-only; never authorizes or executes deployment. The trusted CI
runner must supply the correct repository checkout and actual built artifact.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import stat
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("deployment_gate", ROOT / "scripts/validate-deployment-plan.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
MAX_PLAN = 64 * 1024
MAX_ARTIFACT = 2 * 1024 * 1024 * 1024


def read_plan(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_PLAN:
        raise ValueError("plan is missing, linked or oversized")
    payload = json.loads(path.read_text(encoding="utf-8"))
    violations = gate.errors(payload)
    if violations:
        raise ValueError("G6 plan blocked: " + "; ".join(violations))
    return payload


def verified_checkout(path):
    if path.is_symlink() or not path.is_dir():
        raise ValueError("invalid repository checkout")
    def git(*args):
        try:
            result = subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                                    text=True, timeout=15, check=True)
            return result.stdout.strip()
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError("cannot inspect repository checkout") from exc
    if Path(git("rev-parse", "--show-toplevel")).resolve() != path.resolve():
        raise ValueError("not the root of the checkout")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("tracked repository changes are present")
    return git("rev-parse", "HEAD")


def verified_artifact(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("artifact missing, linked or not a regular file")
    before = path.stat(follow_symlinks=False)
    if before.st_size <= 0 or before.st_size > MAX_ARTIFACT:
        raise ValueError("empty or oversized release artifact")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    digest = hashlib.sha256()
    try:
        with os.fdopen(os.open(path, flags), "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError("artifact must be a regular file")
            while block := handle.read(1024 * 1024):
                digest.update(block)
            opened = os.fstat(handle.fileno())
    except OSError as exc:
        raise ValueError("could not read artifact") from exc
    after = path.stat(follow_symlinks=False)
    if (before.st_ino, before.st_dev, before.st_size, before.st_mtime_ns) != (
            after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns):
        raise ValueError("artifact changed during verification")
    if (opened.st_ino, opened.st_dev, opened.st_size, opened.st_mtime_ns) != (
            after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns):
        raise ValueError("artifact changed while hashing")
    return digest.hexdigest()


def assess(plan_path, checkout, artifact):
    plan = read_plan(Path(plan_path))
    head = verified_checkout(Path(checkout))
    if head != plan["source_sha"]:
        raise ValueError("plan source SHA does not match actual checkout HEAD")
    actual_digest = verified_artifact(Path(artifact))
    if actual_digest != plan["artifact_sha256"]:
        raise ValueError("plan artifact SHA does not match artifact bytes")
    return {"gate": "G6", "decision": "ARTIFACT_AND_SOURCE_VERIFIED",
            "product": plan["product"], "environment": plan["environment"],
            "source_sha": head, "artifact_sha256": actual_digest,
            "independent_checks": ["checkout_HEAD", "tracked_checkout_clean", "artifact_SHA256"],
            "checks_provider_verified": False, "approval_identity_verified": False,
            "deployment_health_verified": False, "authorized_to_deploy": False}


def main():
    parser = argparse.ArgumentParser(description="Offline G6 source/artifact evidence verification")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = assess(args.plan, args.checkout, args.artifact)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError):
        print(json.dumps({"gate": "G6", "decision": "BLOCK",
                          "errors": ["G6 policy, checkout or artifact verification failed"],
                          "authorized_to_deploy": False}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
