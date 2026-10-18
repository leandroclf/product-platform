#!/usr/bin/env python3
"""Read-only G6 CI context gate for use inside a product's trusted workflow.

Checks GitHub context against source/artifact evidence. This does not verify
approvals, actual executed checks, artifact registry, or permission to deploy.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys

try:
    from . import verify_deployment_artifact as verifier
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "g6_verifier", Path(__file__).with_name("verify-deployment-artifact.py"))
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)

REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
RUN_ID = re.compile(r"^[1-9][0-9]*$")


def assess(plan, checkout, artifact, repository, env):
    if not REPOSITORY.fullmatch(repository):
        raise ValueError("invalid expected repository")
    # A PR or fork-triggered workflow is untrusted for preparing release promotion.
    required = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REPOSITORY": repository,
    }
    if any(env.get(key) != value for key, value in required.items()):
        raise ValueError("CI context is not a main-branch push on the intended repository")
    if not RUN_ID.fullmatch(env.get("GITHUB_RUN_ID", "")):
        raise ValueError("GitHub workflow run ID missing")
    workspace = env.get("GITHUB_WORKSPACE", "")
    if not workspace or Path(workspace).resolve() != Path(checkout).resolve():
        raise ValueError("CI checkout must be the exact GitHub workspace")
    result = verifier.assess(plan, checkout, artifact)
    if env.get("GITHUB_SHA") != result["source_sha"]:
        raise ValueError("GitHub event SHA differs from verified artifact source")
    return dict(result, decision="CI_CONTEXT_AND_ARTIFACT_VERIFIED",
                github_repository=repository, github_run_id=env["GITHUB_RUN_ID"],
                ci_event="push", ci_ref="refs/heads/main",
                approval_identity_verified=False, checks_provider_verified=False,
                authorized_to_deploy=False)


def main():
    parser = argparse.ArgumentParser(description="Read-only release CI context and G6 artifact gate")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--repository", required=True, help="expected owner/repository")
    args = parser.parse_args()
    try:
        print(json.dumps(assess(args.plan, args.checkout, args.artifact,
                                args.repository, os.environ), sort_keys=True))
        return 0
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
        print(json.dumps({"gate": "G6", "decision": "BLOCK",
                          "errors": ["CI context or artifact evidence failed"],
                          "authorized_to_deploy": False}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
