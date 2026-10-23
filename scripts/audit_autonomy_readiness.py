#!/usr/bin/env python3
"""Read-only readiness assessment of GitHub autonomous merge controls.

Unknown / inaccessible settings are NOT interpreted as passing.
No secret values are read, and no GitHub mutations are made.
"""
import argparse
import json
import os
import subprocess

REQUIRED_SECRETS = {"INTEGRATOR_APP_PRIVATE_KEY"}
REQUIRED_VARIABLES = {"AGENT_TRUSTED_REVIEWERS", "INTEGRATOR_APP_ID", "AGENT_REVIEW_MODE"}


def gh_get(endpoint):
    output = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, check=True)
    return json.loads(output.stdout)


def probe(endpoint, getter):
    try:
        return getter(endpoint), None
    except Exception as exc:
        return None, type(exc).__name__


def assess(repo, getter=gh_get):
    info, err_info = probe(f"repos/{repo}", getter)
    secrets, err_secrets = probe(f"repos/{repo}/actions/secrets?per_page=100", getter)
    variables, err_vars = probe(f"repos/{repo}/actions/variables?per_page=100", getter)
    protection, err_protection = probe(f"repos/{repo}/branches/main/protection", getter)
    rulesets, err_rules = probe(f"repos/{repo}/rulesets?per_page=100", getter)
    branch_rules, err_branch_rules = probe(f"repos/{repo}/rules/branches/main", getter)
    checks = []

    def add(name, state, evidence):
        checks.append({"name": name, "state": state, "evidence": evidence})

    def state_for(probe_result, error):
        return "unknown" if error or not isinstance(probe_result, dict) else "known"

    if state_for(info, err_info) == "known":
        enabled = info.get("allow_auto_merge") is True
        add("auto_merge_enabled", "pass" if enabled else "fail", "GitHub repository setting")
    else:
        add("auto_merge_enabled", "unknown", err_info or "inaccessible repository settings")

    if state_for(secrets, err_secrets) == "known" and isinstance(secrets.get("secrets"), list):
        names = {x.get("name") for x in secrets["secrets"]}
        for secret in sorted(REQUIRED_SECRETS):
            add("secret_metadata:" + secret, "pass" if secret in names else "fail",
                "Name present only; does not verify secret value or permissions")
    else:
        for secret in sorted(REQUIRED_SECRETS):
            add("secret_metadata:" + secret, "unknown", err_secrets or "inaccessible metadata")

    if state_for(variables, err_vars) == "known" and isinstance(variables.get("variables"), list):
        names = {x.get("name"): x.get("value", "") for x in variables["variables"]}
        for variable in sorted(REQUIRED_VARIABLES):
            value = names.get(variable)
            valid = isinstance(value, str) and bool(value.strip())
            if variable == "AGENT_REVIEW_MODE":
                valid = value == "independent"
            if variable == "INTEGRATOR_APP_ID":
                valid = isinstance(value, str) and value.isdigit() and int(value) > 0
            add("variable:" + variable, "pass" if valid else "fail",
                "Nonempty variable; reviewer independence not verified")
    else:
        for variable in sorted(REQUIRED_VARIABLES):
            add("variable:" + variable, "unknown", err_vars or "inaccessible variables")

    if state_for(protection, err_protection) == "known":
        reviews = protection.get("required_pull_request_reviews") or {}
        status = protection.get("required_status_checks") or {}
        contexts = set(status.get("contexts") or [])
        contexts.update(x.get("context") for x in status.get("checks") or [] if isinstance(x, dict))
        add("required_pr_review", "pass" if reviews.get("required_approving_review_count", 0) >= 1 else "fail",
            "Branch protection approval requirement")
        add("stale_reviews_dismissed", "pass" if reviews.get("dismiss_stale_reviews") is True else "fail",
            "Branch protection stale review behavior")
        add("independent_review_check", "pass" if any("independent-review-gate" in str(c) for c in contexts) else "fail",
            "Required status checks in legacy branch protection")
    else:
        for field in ("required_pr_review", "stale_reviews_dismissed", "independent_review_check"):
            add(field, "unknown", err_protection or "branch protection inaccessible; rulesets may apply")

    # This endpoint resolves enforced rules applicable to main, unlike the catalog listing.
    if isinstance(branch_rules, list) and not err_branch_rules:
        reviews = [r.get("parameters", {}) for r in branch_rules if r.get("type") == "pull_request"]
        status = [r.get("parameters", {}) for r in branch_rules if r.get("type") == "required_status_checks"]
        enforced = {
            "required_pr_review": any(r.get("required_approving_review_count", 0) >= 1 for r in reviews),
            "stale_reviews_dismissed": any(r.get("dismiss_stale_reviews_on_push") is True for r in reviews),
            "independent_review_check": any(c.get("context") == "independent-review-gate"
                                             for r in status for c in r.get("required_status_checks", [])),
        }
        for check in checks:
            if check["name"] in enforced and check["state"] != "pass":
                check["state"] = "pass" if enforced[check["name"]] else "fail"
                check["evidence"] = "Effective enforced rules for main (legacy protection may add requirements)"

    # Listing rulesets is not enough to establish that any given rule applies to main.
    if isinstance(rulesets, list):
        add("ruleset_policy_audit", "unknown",
            f"{len(rulesets)} rulesets listed; each requires detailed inspection for applicability, bypass and enforcement")
    else:
        add("ruleset_policy_audit", "unknown", err_rules or "ruleset configuration inaccessible")

    for control in ("distinct_authenticated_agents", "specialized_review_evidence",
                    "real_end_to_end_pilot", "portfolio_rollout"):
        add(control, "unknown", "Requires independent operational evidence; GitHub settings alone cannot prove this")

    ready = all(x["state"] == "pass" for x in checks)
    return {"repository": repo, "ready_for_autonomous_merge": ready,
            "checks": checks,
            "note": "Read-only evidence snapshot. Unknown and failed controls prevent readiness."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="leandroclf/product-platform")
    args = parser.parse_args()
    if not os.environ.get("GH_TOKEN") and not os.environ.get("GITHUB_TOKEN"):
        # gh CLI may have locally cached authentication; do not require tokens in env.
        pass
    report = assess(args.repo)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ready_for_autonomous_merge"] else 2)


if __name__ == "__main__":
    main()
