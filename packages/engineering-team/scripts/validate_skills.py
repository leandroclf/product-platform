"""Validate the publishable skill catalog and package contracts."""
from collections import defaultdict
from pathlib import Path
import re
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "skills" / "catalog.yaml"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
STATUSES = {"experimental", "beta", "stable", "deprecated"}
CATEGORIES = {"orchestration", "design", "implementation", "quality", "security", "assurance", "operations", "stack", "platform", "delivery"}
RISKS = {"R0", "R1", "R2", "R3"}
REQUIRED_SECTIONS = ("Inputs", "Outputs", "Boundaries", "Validation")


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("missing YAML frontmatter")
    value = yaml.safe_load(match.group(1))
    if not isinstance(value, dict):
        raise ValueError("frontmatter must be a mapping")
    return value, text[match.end():]



def provenance_errors(root, ownership=None):
    """Catch silent drift between compatibility snapshots and canonical kit.

    Explicit security exception remains visible until deliberately reconciled.
    """
    errors = []
    ownership_file = root / "skills" / "ownership.yaml"
    try:
        owner = ownership if ownership is not None else yaml.safe_load(ownership_file.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"invalid skill ownership: {exc}"]
    if not isinstance(owner, dict):
        return ["skill ownership must be a mapping"]
    if owner.get("canonical_skill_repository") != "leandroclf/product-platform" or (
        owner.get("canonical_skill_path") != "packages/kit/skills"
    ):
        errors.append("canonical skill ownership must target product-platform/packages/kit/skills")
    exceptions = owner.get("allowed_divergences", {})
    if exceptions != {"security": "pending-structured-security-skill-reconciliation"}:
        errors.append("unexpected skill divergence exception; require a documented review")
    kit = root.parent / "kit" / "skills"
    team = root / "skills"
    if not kit.is_dir():
        return errors + ["canonical kit skills missing; cannot certify snapshot parity"]
    for skill in sorted(team.glob("*/SKILL.md")):
        counterpart = kit / skill.parent.name / "SKILL.md"
        if not counterpart.is_file():
            errors.append(f"{skill.parent.name}: canonical kit skill missing")
        elif skill.read_bytes() != counterpart.read_bytes() and skill.parent.name not in exceptions:
            errors.append(f"{skill.parent.name}: snapshot differs from canonical kit skill")
    # Never allow a disappeared exception to go unnoticed either.
    for name in exceptions:
        a, b = team / name / "SKILL.md", kit / name / "SKILL.md"
        if not a.is_file() or not b.is_file():
            errors.append(f"{name}: documented divergence has missing source")
    return errors


def main():
    errors = provenance_errors(ROOT)
    try:
        catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"catalog invalid: {exc}", file=sys.stderr)
        return 1
    if not isinstance(catalog, dict) or not SEMVER.match(str(catalog.get("catalog_version", ""))):
        errors.append("catalog_version must be semantic version")
    entries = catalog.get("skills") if isinstance(catalog, dict) else None
    if not isinstance(entries, list) or not entries:
        errors.append("catalog must contain non-empty skills list")
        entries = []
    ids = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    if len(ids) != len(set(ids)):
        errors.append("skill ids must be unique")
    known = set(ids)
    graph = defaultdict(set)
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("each catalog entry must be a mapping")
            continue
        skill_id = entry.get("id", "<missing>")
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", str(skill_id)):
            errors.append(f"{skill_id}: invalid id")
        if not SEMVER.match(str(entry.get("version", ""))):
            errors.append(f"{skill_id}: invalid version")
        if entry.get("status") not in STATUSES:
            errors.append(f"{skill_id}: invalid status")
        if entry.get("category") not in CATEGORIES:
            errors.append(f"{skill_id}: invalid category")
        if entry.get("risk") not in RISKS:
            errors.append(f"{skill_id}: invalid risk")
        path = ROOT / str(entry.get("path", ""))
        if not (path / "SKILL.md").is_file():
            errors.append(f"{skill_id}: missing {entry.get('path')}/SKILL.md")
            continue
        try:
            metadata, body = frontmatter(path / "SKILL.md")
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{skill_id}: {exc}")
            continue
        if metadata.get("name") != skill_id:
            errors.append(f"{skill_id}: catalog id differs from frontmatter name")
        if not metadata.get("description"):
            errors.append(f"{skill_id}: missing frontmatter description")
        for section in REQUIRED_SECTIONS:
            if not re.search(rf"^## {re.escape(section)}\s*$", body, re.M):
                errors.append(f"{skill_id}: missing ## {section}")
        for dep in entry.get("requires", []) or []:
            if dep not in known:
                errors.append(f"{skill_id}: unknown dependency {dep}")
            graph[skill_id].add(dep)
        if skill_id in (entry.get("requires", []) or []):
            errors.append(f"{skill_id}: cannot require itself")
        for field in ("tags", "inputs", "outputs", "quality_gates", "supported_surfaces"):
            if not isinstance(entry.get(field), list) or not entry[field]:
                errors.append(f"{skill_id}: {field} must be a non-empty list")
    # Detect dependency cycles before a marketplace resolver can loop.
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            errors.append(f"dependency cycle includes {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in graph[node]:
            visit(dep)
        visiting.remove(node)
        visited.add(node)
    for skill_id in known:
        visit(skill_id)
    catalog_ids = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    if catalog_ids != known:
        errors.append(f"catalog/package mismatch: filesystem={sorted(catalog_ids)} catalog={sorted(known)}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {len(known)} publishable skills; metadata, contracts, dependencies and cycles validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
