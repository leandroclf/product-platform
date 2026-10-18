#!/usr/bin/env python3
"""Adversarial Docker boundary canaries. No provider login, secrets, or inference.

Uses production container flags. Deliberately tests denied operations, and fails
closed if any one succeeds. Synthetic sentinel strings are NOT credentials.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from local_team import docker_base, env_without_authority

SENTINEL = "SYNTHETIC_CANARY_DO_NOT_USE_AS_CREDENTIAL"


def run_canary(image, root, *, stage, writable):
    work = root / "workspace"
    git_dir = work / ".git"
    handoff = root / "handoff"
    output = root / "output"
    cmd = docker_base("ai-team-adversarial-" + stage, image, network=False)
    cmd += [
        "--tmpfs", "/home/agent:uid=1001,gid=1001,mode=700",
        "-v", str(work) + (":/work" if writable else ":/work:ro"),
        "-v", str(git_dir) + ":/work/.git:ro",
        "-v", str(handoff) + ":/handoff:ro",
        "-v", str(output) + ":/output",
        "-w", "/work", image, "python3", "-c",
        """import os, pathlib, socket
def blocked(action):
 try: action()
 except (OSError, PermissionError):
  return
 raise AssertionError('unexpected permitted operation')
assert os.getuid() == 1001
assert os.environ.get('GH_TOKEN') is None
assert os.environ.get('GITHUB_TOKEN') is None
assert os.environ.get('OPENAI_API_KEY') is None
assert os.environ.get('ANTHROPIC_API_KEY') is None
assert not pathlib.Path('/var/run/docker.sock').exists()
assert not pathlib.Path('/home/agent/.codex/auth.json').exists()
assert not pathlib.Path('/home/agent/.claude/.credentials.json').exists()
blocked(lambda: pathlib.Path('/work/.git/config').write_text('tampered'))
blocked(lambda: pathlib.Path('/handoff/plan.json').write_text('tampered'))
blocked(lambda: pathlib.Path('/work/git-link').write_text('tampered'))
blocked(lambda: pathlib.Path('/work/handoff-link').write_text('tampered'))
blocked(lambda: pathlib.Path('/work/secret-link').read_text())
blocked(lambda: socket.create_connection(('1.1.1.1',443),timeout=1))
if WRITABLE:
 pathlib.Path('/work/editable.py').write_text('edited')
else:
 blocked(lambda: pathlib.Path('/work/editable.py').write_text('edited'))
pathlib.Path('/output/canary.json').write_text('{"status":"PASS"}')
""".replace("WRITABLE", repr(writable)),
    ]
    env = env_without_authority()
    assert not any(k in env for k in (
        "GH_TOKEN", "GITHUB_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=40, env=env)
    if result.returncode:
        raise RuntimeError(f"{stage} boundary test failed: {result.stderr[-1500:]}")
    if json.loads((output / "canary.json").read_text())["status"] != "PASS":
        raise RuntimeError("Container did not produce expected canary")
    assert (git_dir / "config").read_text() == "git-metadata"
    assert (handoff / "plan.json").read_text() == "trusted-plan"
    assert (root / "outside.txt").read_text() == SENTINEL
    return (work / "editable.py").read_text()


def main():
    image = os.environ.get("AI_TEAM_SMOKE_IMAGE", "ai-eng-provider-cli:validation")
    with tempfile.TemporaryDirectory(prefix="ai-team-adversarial-") as directory:
        root = Path(directory)
        root.chmod(0o755)
        work = root / "workspace"
        work.mkdir(mode=0o777)
        work.chmod(0o777)
        git_dir = work / ".git"
        git_dir.mkdir(mode=0o755)
        (git_dir / "config").write_text("git-metadata")
        (git_dir / "config").chmod(0o644)
        handoff = root / "handoff"
        handoff.mkdir(mode=0o755)
        (handoff / "plan.json").write_text("trusted-plan")
        (handoff / "plan.json").chmod(0o644)
        output = root / "output"
        output.mkdir(mode=0o777)
        output.chmod(0o777)
        (root / "outside.txt").write_text(SENTINEL)
        (root / "outside.txt").chmod(0o600)
        (work / "git-link").symlink_to(".git/config")
        (work / "handoff-link").symlink_to("../handoff/plan.json")
        (work / "secret-link").symlink_to("../outside.txt")
        (work / "editable.py").write_text("original")
        (work / "editable.py").chmod(0o666)
        os.environ["GH_TOKEN"] = SENTINEL
        os.environ["GITHUB_TOKEN"] = SENTINEL
        os.environ["OPENAI_API_KEY"] = SENTINEL
        os.environ["ANTHROPIC_API_KEY"] = SENTINEL
        try:
            assert run_canary(image, root, stage="planner", writable=False) == "original"
            assert run_canary(image, root, stage="implementer", writable=True) == "edited"
        finally:
            for variable in ("GH_TOKEN", "GITHUB_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
                os.environ.pop(variable, None)
    print(json.dumps({
        "status": "PASS",
        "provider_authenticated": False,
        "tested": ["no token inheritance", "no docker socket", "no network",
                   "read-only planner checkout", "writable implementer checkout",
                   "read-only git and handoff", "symlink escape denial",
                   "no other-stage accounts"],
        "limitations": "Real Docker boundary test with synthetic data only; no provider runtime inference, native CLI permissions, or user host ACL certification.",
    }))


if __name__ == "__main__":
    main()
