#!/usr/bin/env python3
"""Validate pinned, read-only deployment discovery without granting authority."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "contracts/portfolio-deployment-discovery.json"
PORTFOLIO = ROOT / "contracts/portfolio-products.json"
DEPLOYMENT = ROOT / "contracts/portfolio-deployment-targets.json"
SHA1 = re.compile(r"^[0-9a-f]{40}$")
FALSE_CLAIMS = (
    "provider_runtime", "remote_deploy", "release_identity", "health",
    "rollback", "approval", "secret_isolation",
)


def validate(snapshot, portfolio, deployment):
    errors = []
    if snapshot.get("schema_version") != 1:
        errors.append("Unsupported discovery schema version")
    if not isinstance(snapshot.get("observed_at_utc"), str) or not snapshot["observed_at_utc"].endswith("Z"):
        errors.append("Discovery timestamp must be UTC")
    if not isinstance(snapshot.get("scope"), str) or not snapshot["scope"]:
        errors.append("Discovery scope must be explicit")
    if not isinstance(snapshot.get("interpretation"), str) or "do not prove" not in snapshot["interpretation"]:
        errors.append("Discovery limits must state that source files do not prove deployment")

    expected = {item.get("repository") for item in portfolio.get("products", []) if isinstance(item, dict)}
    product_records = snapshot.get("products")
    target_names = {item.get("product") for item in deployment.get("targets", []) if isinstance(item, dict)}
    if not isinstance(product_records, list):
        return errors + ["Discovery products must be a list"]
    observed = [item.get("repository") for item in product_records if isinstance(item, dict)]
    if len(observed) != len(product_records) or len(set(observed)) != len(observed) or set(observed) != expected:
        errors.append("Discovery must cover each portfolio product exactly once")
    if target_names != expected:
        errors.append("Deployment targets and portfolio products are inconsistent")

    portal = portfolio.get("portal", {})
    flagship = snapshot.get("flagship_portal")
    if not isinstance(flagship, dict) or flagship.get("repository") != portal.get("repository"):
        errors.append("Flagship portal discovery is missing or has the wrong owner")
    records = product_records + ([flagship] if isinstance(flagship, dict) else [])
    for item in records:
        name = item.get("repository", "<invalid>")
        source = item.get("source")
        if not isinstance(source, dict) or source.get("branch") != "main" or not SHA1.fullmatch(str(source.get("commit_sha", ""))):
            errors.append("Invalid pinned source revision for " + str(name))
            continue
        files = source.get("files")
        if not isinstance(files, list) or not files:
            errors.append("Pinned source files are required for " + str(name))
        else:
            paths = []
            for file in files:
                if not isinstance(file, dict) or not isinstance(file.get("path"), str) or not SHA1.fullmatch(str(file.get("git_blob_sha1", ""))):
                    errors.append("Invalid source file evidence for " + str(name))
                    continue
                paths.append(file["path"])
            if len(paths) != len(set(paths)):
                errors.append("Repeated source paths for " + str(name))
        declarations = item.get("declarations")
        verification = item.get("verification")
        if not isinstance(declarations, dict) or not isinstance(verification, dict):
            errors.append("Declarations and verification claims are required for " + str(name))
            continue
        if verification.get("source_configuration") is not True:
            errors.append("Source configuration must be marked inspected for " + str(name))
        for claim in FALSE_CLAIMS:
            if verification.get(claim) is not False:
                errors.append("Unproven deployment claim must remain false: " + str(name) + "/" + claim)
        if "health_url" in declarations or "production_url" in declarations:
            errors.append("Discovery must not invent endpoint URLs for " + str(name))

    # The known GitHub environment observation is a current native configuration
    # fact, not a grant to deploy or proof of any external provider state.
    vehicle = next((item for item in product_records if item.get("repository") == "vehicle-tracking"), None)
    if vehicle:
        environments = vehicle.get("observed_github_state", {}).get("environments", [])
        production = next((env for env in environments if env.get("name") == "production"), None)
        if not isinstance(production, dict) or production.get("required_reviewer_count") != 0:
            errors.append("Vehicle production environment observation must preserve the observed reviewer count")
    return errors


def main():
    snapshot, portfolio, deployment = [json.loads(path.read_text(encoding="utf-8")) for path in (DISCOVERY, PORTFOLIO, DEPLOYMENT)]
    errors = validate(snapshot, portfolio, deployment)
    if errors:
        print("PORTFOLIO_DEPLOYMENT_DISCOVERY_BLOCKED:", "; ".join(errors))
        raise SystemExit(1)
    print("PORTFOLIO_DEPLOYMENT_DISCOVERY_VALID: pinned source declarations only; no remote deployment authority")


if __name__ == "__main__":
    main()
