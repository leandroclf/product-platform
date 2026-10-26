"""Conservative host-owned risk and verification policy for supervised AI-team runs.

An agent, task issue or plan may describe risk; none may lower these floors.
This is a bounded path-based safeguard, not a complete semantic risk engine.
"""
from pathlib import PurePosixPath
import re

RANK = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}
SENSITIVE_SUFFIXES = {".tf", ".tfvars", ".hcl", ".sql", ".prisma", ".lock", ".pem", ".key", ".p12", ".pfx"}
SENSITIVE_FILES = {"dockerfile", "compose.yaml", "compose.yml", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
                   "pyproject.toml", "requirements.txt", "pom.xml", "build.gradle",
                   "build.gradle.kts", "settings.gradle", ".npmrc", ".pypirc",
                   ".env", ".env.local", ".env.production"}
SENSITIVE_PARTS = {"migrations", "migration", "terraform", "infra", "infrastructure",
                   "k8s", "kubernetes", "helm", "auth", "authentication",
                   "authorization", "iam", "permissions", "secrets", ".github"}
SENSITIVE_WORDS = re.compile(r"(?:^|[_./-])(security|credentials?|password|token|oauth|rbac|acl|policy)(?:$|[_./-])", re.I)
TEST_PREFIXES = ("tests/", "test/", "__tests__/")


def classify_path(path):
    if not isinstance(path, str) or not path or "\x00" in path or "\\" in path:
        return "R2"
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts:
        return "R2"
    name = p.name.lower()
    parts = {x.lower() for x in p.parts}
    if (name in SENSITIVE_FILES or p.suffix.lower() in SENSITIVE_SUFFIXES or
            bool(parts & SENSITIVE_PARTS) or SENSITIVE_WORDS.search(path)):
        return "R2"
    if p.suffix.lower() in (".md", ".mdx", ".rst", ".txt") and "docs" in parts:
        return "R0"
    return "R1"


def classify_paths(paths):
    if not isinstance(paths, (list, tuple)) or not paths:
        return "R1"
    return max((classify_path(p) for p in paths), key=lambda risk: RANK[risk])


def authorize_plan(claim, authorized_risk="R1"):
    """Accept R0/R1 by default; R2 only when the operator explicitly selected that ceiling."""
    if authorized_risk not in ("R0", "R1", "R2"):
        raise ValueError("operator authorization may not exceed R2")
    if claim not in RANK or claim == "R3":
        raise ValueError("R3 and unknown plan risks are never authorized by this workflow")
    if RANK[claim] > RANK[authorized_risk]:
        raise ValueError(f"plan risk {claim} exceeds operator-authorized {authorized_risk}")
    return claim


def ensure_authorized(claim, paths, authorized_risk="R1"):
    """Keep the plan and actual change surface within the operator-authorized ceiling."""
    authorize_plan(claim, authorized_risk)
    actual = classify_paths(paths)
    if RANK[actual] > RANK[claim]:
        raise ValueError(f"Actual change surface is {actual}, above claimed {claim}; re-triage task")
    return actual


def required_quality_surfaces(paths):
    """Deterministically flag which specialized gate families require human setup."""
    kinds = set()
    for path in paths:
        p = path.lower()
        if classify_path(path) == "R2":
            kinds.add("security_and_approval")
        if any(x in p for x in ("api/", "controller", "route", "endpoint")):
            kinds.add("api_contract")
        if any(x in p for x in ("database/", "schema", "migration", ".sql", ".prisma")):
            kinds.add("database_migration")
        if p.endswith((".tsx", ".jsx")) or p.startswith(("app/", "pages/", "components/")):
            kinds.add("frontend")
        if p.endswith((".tf", ".tfvars")) or "/helm/" in p or "/k8s/" in p:
            kinds.add("infrastructure")
        if any(x in p for x in ("webhook", "queue", "consumer", "integration")):
            kinds.add("integration")
    return sorted(kinds)
