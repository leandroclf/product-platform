#!/usr/bin/env python3
"""Update provider CLIs only after a stable-registry lookup and isolated compatibility test.

Check is read-only. Promotion requires the operator's exact version approval.
No provider login/inference; no live running task can change runtime mid-stage.
"""
import argparse
import hashlib
import os
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
import urllib.error

PACKAGES = {"codex": "@openai/codex", "claude": "@anthropic-ai/claude-code"}
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
IMAGE = "ai-eng-provider-cli:local"
REQUIRED = {
    "codex": ("--json", "--sandbox", "--ephemeral", "--output-schema", "--model", "--config"),
    "claude": ("--output-format", "--json-schema", "--permission-mode", "--permission-prompts",
               "--restricted", "--strict-mcp-config", "--model", "--effort", "--tools",
               "--allowedTools", "--disallowedTools", "--add-dir", "--no-session-persistence"),
}


def latest(name):
    package = PACKAGES[name]
    # Official npm registry stable dist-tag; do not rely on a pre-release/latest string from a mirror.
    url = "https://registry.npmjs.org/" + package.replace("/", "%2f") + "/latest"
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "ai-team-cli-updater"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            if response.status != 200:
                raise ValueError("Registry returned non-200")
            payload = response.read(512 * 1024 + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ValueError("Official npm registry unavailable; refuse to guess latest version") from exc
    if len(payload) > 512 * 1024:
        raise ValueError("Oversized registry result")
    data = json.loads(payload)
    if data.get("name") != package or not VERSION.fullmatch(str(data.get("version", ""))):
        raise ValueError("Registry stable version is missing or invalid")
    return data["version"]


def run(args, *, timeout=240, capture=True, env=None):
    try:
        return subprocess.run(args, check=True, capture_output=capture, text=True, timeout=timeout, env=env)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError("CLI update check/build failed; active runtime preserved") from exc


def inspect_versions(image):
    """Verify the native flags and version of both actual binaries, without auth volumes."""
    info = {}
    for name in PACKAGES:
        executable = name if name == "codex" else "claude"
        def docker(*args):
            result = run(["docker", "run", "--rm", "--pull", "never", "--network", "none",
                          "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                          "--user", "1001:1001", "--tmpfs", "/tmp:uid=1001,gid=1001",
                          "--tmpfs", "/home/agent:uid=1001,gid=1001",
                          "--entrypoint", executable, image, *args], timeout=40)
            return result.stdout
        version_output = docker("--version")
        version = re.search(r"\b[0-9]+\.[0-9]+\.[0-9]+\b", version_output)
        if not version:
            raise ValueError("Cannot verify installed CLI version")
        help_text = docker(*(("exec", "--help") if name == "codex" else ("--help",)))
        missing = [flag for flag in REQUIRED[name] if flag not in help_text]
        if missing:
            raise ValueError(f"{name}: required compatibility flags missing: {','.join(missing)}")
        info[name] = version.group()
    return info


def active_tasks(home):
    runs = Path(home) / "runs"
    if runs.is_symlink():
        raise ValueError("Task directory symlink; cannot safely promote")
    if not runs.exists():
        return []
    if not runs.is_dir():
        raise ValueError("Invalid tasks directory; cannot safely promote")
    active = []
    safe_statuses = {"REVIEWED", "DELIVERED", "FAILED", "STOPPED"}
    for directory in runs.iterdir():
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Unexpected entry in task directory; cannot safely promote")
        file = directory / "state.json"
        if file.is_symlink() or not file.is_file():
            raise ValueError("Missing or linked task state; cannot safely promote")
        try:
            state = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ValueError("Unreadable task state; cannot safely promote") from None
        if not isinstance(state, dict) or not isinstance(state.get("status"), str):
            raise ValueError("Malformed task state; cannot safely promote")
        if state["status"] not in safe_statuses:
            active.append(directory.name)
    return active


def plan(installed, available):
    outdated = {key: installed.get(key) != available[key] for key in PACKAGES}
    token = hashlib.sha256(json.dumps(available, sort_keys=True).encode()).hexdigest()
    return {"installed": installed, "available": available, "update_needed": outdated,
            "approval_fingerprint": token, "automatic_promotion": False}


def promote(root, versions, fingerprint, state_home):
    if fingerprint != plan({}, versions)["approval_fingerprint"]:
        raise ValueError("Explicit approval hash does not match latest stable versions")
    if active_tasks(state_home):
        raise ValueError("Active or uncertain ai-team tasks; refusing runtime promotion")
    candidate = "ai-eng-provider-cli:candidate-" + fingerprint[:16]
    run(["docker", "build", "--pull", "--build-arg", "CODEX_VERSION=" + versions["codex"],
         "--build-arg", "CLAUDE_VERSION=" + versions["claude"], "-f",
         str(root / "runtimes" / "Dockerfile"), "-t", candidate, str(root)], timeout=1200)
    # The candidate tag can be reassigned by a parallel process. Resolve its
    # immutable ID BEFORE any CLI or Docker canary verification.
    candidate_id = run(["docker", "image", "inspect", "--format", "{{.Id}}", candidate]).stdout.strip()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", candidate_id):
        raise ValueError("Candidate image lacks valid immutable ID")
    actual = inspect_versions(candidate_id)
    if actual != versions:
        raise ValueError("Candidate image versions differ from approved registry versions")
    # Exercise all four actual container mount boundaries and adversarial
    # probes against this exact candidate ID, never a mutable local tag.
    env = dict(os.environ, AI_TEAM_SMOKE_IMAGE=candidate_id)
    run([sys.executable, str(root / "scripts" / "local_stage_isolation_smoke.py")],
        timeout=300, env=env)
    # Release versions may have changed during the expensive build. Stop
    # instead of promoting a candidate which is no longer the latest stable.
    if {name: latest(name) for name in PACKAGES} != versions:
        raise ValueError("Stable registry versions changed during build; recheck and reapprove")
    if active_tasks(state_home):
        raise ValueError("Task started during candidate build; refusing promotion")
    run(["docker", "tag", candidate_id, IMAGE])
    return {"promoted": True, "versions": actual, "image_digest": candidate_id,
            "note": "New runs use the tag; existing tasks retain their frozen image ID."}


def main():
    parser = argparse.ArgumentParser(description="Test stable CLI releases before explicit promotion")
    parser.add_argument("--promote", action="store_true", help="opt-in build, test and promote both CLIs")
    parser.add_argument("--confirm-hash", help="exact approval_fingerprint from latest check")
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        parser.error("Linux is required")
    root = Path(__file__).resolve().parents[1]
    try:
        from local_team import home
        current = inspect_versions(IMAGE)
        desired = {name: latest(name) for name in PACKAGES}
        result = plan(current, desired)
        if args.promote:
            if not args.confirm_hash:
                raise ValueError("--promote requires --confirm-hash from check output")
            if args.confirm_hash != result["approval_fingerprint"]:
                raise ValueError("Registry changed since approval; recheck versions first")
            result["promotion"] = promote(root, desired, args.confirm_hash, home())
        elif args.confirm_hash:
            raise ValueError("--confirm-hash must accompany --promote")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
