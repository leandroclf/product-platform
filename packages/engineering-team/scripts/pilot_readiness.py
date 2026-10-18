#!/usr/bin/env python3
"""Fail-closed Linux pilot readiness. No agent inference, login or code execution."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

try:
    from . import local_team as team
except ImportError:
    import local_team as team


def command(argv, timeout=15):
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def acl_canary():
    """Verify the host can grant a scoped POSIX ACL without world-write."""
    if not shutil.which("setfacl") or not shutil.which("getfacl"):
        return False
    with tempfile.TemporaryDirectory(prefix="ai-team-acl-probe-") as directory:
        folder = Path(directory)
        candidate = folder / "test"
        candidate.write_text("synthetic")
        candidate.chmod(0o600)
        if not command(["setfacl", "-m", "u:1001:rw-", "--", str(candidate)]):
            return False
        try:
            result = subprocess.run(["getfacl", "-cp", "--", str(candidate)],
                                    capture_output=True, text=True, timeout=10)
            return (result.returncode == 0 and
                    any(re.fullmatch(r"user:1001:rw-", line.strip())
                        for line in result.stdout.splitlines()) and
                    not candidate.stat().st_mode & 0o002)
        except (OSError, subprocess.TimeoutExpired):
            return False


def assess(target):
    """No credentials, tokens, prompts, full paths or raw stderr in output."""
    checks = {}
    repo = Path(target).expanduser().resolve()
    checks["linux"] = sys.platform.startswith("linux")
    checks["git"] = bool(shutil.which("git"))
    checks["docker"] = bool(shutil.which("docker"))
    checks["python_version"] = sys.version_info >= (3, 10)
    checks["acl_scoped_write"] = acl_canary() if checks["linux"] else False
    checks["git_checkout"] = False
    checks["git_clean"] = False
    checks["git_branch"] = False
    checks["github_origin"] = False
    checks["config_valid"] = False
    checks["image_provider_present"] = False
    checks["image_tests_present"] = False
    checks["quality_checks_defined"] = False
    checks["stage_models_declared"] = False

    if checks["git"] and repo.is_dir():
        def git(*args):
            try:
                return subprocess.run(["git", "-C", str(repo), *args],
                                      capture_output=True, text=True, timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                return None
        root = git("rev-parse", "--show-toplevel")
        checks["git_checkout"] = bool(root and root.returncode == 0 and
                                      Path(root.stdout.strip()).resolve() == repo)
        if checks["git_checkout"]:
            status = git("status", "--porcelain")
            checks["git_clean"] = bool(status and status.returncode == 0 and not status.stdout.strip())
            branch = git("branch", "--show-current")
            checks["git_branch"] = bool(branch and branch.returncode == 0 and branch.stdout.strip())
            remote = git("remote", "get-url", "origin")
            checks["github_origin"] = bool(remote and remote.returncode == 0 and
                re.fullmatch(r"(?:https://github\.com/|git@github\.com:)[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?",
                             remote.stdout.strip()))
    config_path = team.home() / "projects" / team.project_id(repo) / "config.json"
    if checks["git_checkout"] and config_path.is_file() and not config_path.is_symlink():
        try:
            config = team.validate_config(team.read(config_path))
            checks["config_valid"] = config["repository"] == str(repo)
            if checks["config_valid"]:
                checks["quality_checks_defined"] = bool(config.get("checks")) and (
                    isinstance(config.get("quality_checks", {}), dict))
                checks["stage_models_declared"] = set(config["models"]) == set(team.STAGES)
                if checks["docker"]:
                    for key, image in (("image_provider_present", config["provider_image"]),
                                       ("image_tests_present", config["test_image"])):
                        checks[key] = command(["docker", "image", "inspect", "--", image])
        except (OSError, ValueError, KeyError, team.Blocked):
            pass
    blockers = sorted(key for key, ok in checks.items() if not ok)
    return {
        "schema_version": 1,
        "ready_for_operator_authenticated_pilot": not blockers,
        "checks": checks, "blockers": blockers,
        "provider_authenticated": False, "actual_inference_verified": False,
        "production_certified": False,
        "next_manual_steps": [
            "Confirm four provider stage accounts with ai-team doctor and models",
            "Run adversarial Docker canaries on this Linux host before first pilot",
            "Select a real R0/R1 task and inspect the frozen dry-run and risk controls",
            "Inspect exact SHA, tests and PR; do not merge or deploy automatically",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only host readiness for authenticated ai-team pilot")
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Optional redacted JSON destination")
    args = parser.parse_args()
    report = assess(args.target)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = args.output.expanduser()
        if target.is_symlink():
            parser.error("Refuse symlink output")
        if target.exists():
            parser.error("Refuse overwrite of existing report")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(target, flags, 0o600)
        with os.fdopen(fd, "w") as result:
            result.write(payload)
    else:
        print(payload, end="")
    return 0 if report["ready_for_operator_authenticated_pilot"] else 2


if __name__ == "__main__":
    sys.exit(main())
