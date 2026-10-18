#!/usr/bin/env python3
"""Read-only, deterministic, bounded backlog candidate queue.

Makes no triage authorization, model invocation, GitHub write or merge.
"""
import argparse
import json
from pathlib import Path
import subprocess

from autonomy_backlog import prepare

MAX_ISSUES = 1000
MAX_QUEUE = 25
PRIORITIES = ("priority-p0", "priority-p1", "priority-p2")


def labels(issue):
    raw = issue.get("labels") or []
    if not isinstance(raw, list):
        raise ValueError("Malformed GitHub issue labels")
    return {label.get("name", "").lower() for label in raw if isinstance(label, dict) and isinstance(label.get("name"), str)}


def build_queue(issues, repo, limit=10):
    if not 1 <= limit <= MAX_QUEUE:
        raise ValueError("Limit must be between 1 and 25")
    if not isinstance(issues, list) or len(issues) > MAX_ISSUES:
        raise ValueError("Invalid issue collection")
    selected, rejected = [], []
    for issue in issues:
        number = issue.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            raise ValueError("Malformed issue number")
        if "pull_request" in issue or issue.get("state") != "open":
            continue
        names = labels(issue)
        if "agent-candidate" not in names:
            continue
        if len(names.intersection(PRIORITIES)) > 1:
            rejected.append({"issue_number": number, "reason": "Conflicting priority labels"})
            continue
        try:
            # Reuse the canonical contract, including risk and bounded cycles.
            body = issue.get("body")
            url = issue.get("html_url")
            if not isinstance(body, str) or not isinstance(url, str):
                raise ValueError("Missing body or issue URL")
            preview = prepare(body, url)
        except (ValueError, TypeError, KeyError) as exc:
            rejected.append({"issue_number": number, "reason": str(exc)[:180]})
            continue
        task = preview["task"]
        priority = next((i for i, name in enumerate(PRIORITIES) if name in names), 3)
        selected.append({
            "issue_number": number, "issue_url": url,
            "target_repository": task["target_repository"],
            "risk_claim": task["risk"],
            "priority": PRIORITIES[priority] if priority < 3 else "unprioritized",
            "task_sha256": preview["task_sha256"],
            "max_cycles": task["max_cycles"],
            "mode": "PREVIEW_ONLY", "execution_allowed": False,
        })
    selected.sort(key=lambda item: (
        PRIORITIES.index(item["priority"]) if item["priority"] in PRIORITIES else 3,
        0 if item["risk_claim"] == "R0" else 1,
        item["issue_number"],
    ))
    return {
        "repository": repo, "schema_version": 1, "mode": "PREVIEW_ONLY",
        "execution_allowed": False, "items": selected[:limit],
        "eligible_total": len(selected),
        "rejected": sorted(rejected, key=lambda x: x["issue_number"]),
        "note": "Selection is not authorization. Reverify issue, source, risk and current SHA before any ai-team execution.",
    }


def render_summary(report):
    """Informational Markdown only; never a go/no-go or approval signal."""
    lines = [
        "## Backlog candidate queue — read-only",
        f"- Repository: `{report['repository']}`",
        f"- Eligible issues: {report['eligible_total']}",
        f"- Included in this bounded preview: {len(report['items'])}",
        f"- Rejected candidates: {len(report['rejected'])}",
        "- **No agent execution, no approval, no merge.**",
        "",
        "| Priority | Issue | Target | Claimed risk |",
        "|---|---|---|---|",
    ]
    for item in report["items"]:
        # Defensively render a normalized GitHub issue URL and repository.
        issue_number = item["issue_number"]
        url = item["issue_url"]
        target = item["target_repository"].replace("|", "/")
        lines.append(f"| {item['priority']} | [#{issue_number}]({url}) | `{target}` | {item['risk_claim']} |")
    if not report["items"]:
        lines.append("| — | No eligible issues | — | — |")
    if report["rejected"]:
        lines += ["", "### Excluded issues", ""]
        for item in report["rejected"]:
            reason = item["reason"].replace("|", "/").replace("\n", " ")
            lines.append(f"- #{item['issue_number']}: {reason}")
    lines += ["", "This is an issue-content snapshot, not a certification of actual risk, evidence or readiness."]
    return "\n".join(lines) + "\n"

def get_json(path):
    result = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def list_open(repo, get=get_json):
    issues = []
    for page in range(1, 12):
        batch = get(f"repos/{repo}/issues?state=open&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("Invalid GitHub issue page")
        issues.extend(batch)
        if len(issues) > MAX_ISSUES:
            raise ValueError("Too many issues; narrow the query")
        if len(batch) < 100:
            return issues
    raise ValueError("Issue pagination incomplete")


def main():
    parser = argparse.ArgumentParser(description="Read-only backlog queue preparation")
    parser.add_argument("--repo", default="leandroclf/product-platform")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    # Does not mark ready or start the local ai-team.
    result = build_queue(list_open(args.repo), args.repo, limit=args.limit)
    output = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    if args.summary:
        args.summary.write_text(render_summary(result), encoding="utf-8")


if __name__ == "__main__":
    main()
