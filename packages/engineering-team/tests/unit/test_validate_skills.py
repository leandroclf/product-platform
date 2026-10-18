import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import validate_skills


class SkillCatalogTests(unittest.TestCase):
    def test_current_catalog_is_publishable(self):
        self.assertEqual(validate_skills.main(), 0)

    def test_skill_snapshots_match_kit_except_documented_security(self):
        self.assertEqual(validate_skills.provenance_errors(validate_skills.ROOT), [])

    def test_unknown_snapshot_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            team = base / 'engineering-team'
            kit = base / 'kit'
            (team / 'skills' / 'backend').mkdir(parents=True)
            (kit / 'skills' / 'backend').mkdir(parents=True)
            (team / 'skills' / 'security').mkdir()
            (kit / 'skills' / 'security').mkdir()
            for name in ('backend', 'security'):
                (team / 'skills' / name / 'SKILL.md').write_text('same')
                (kit / 'skills' / name / 'SKILL.md').write_text('same')
            (team / 'skills' / 'backend' / 'SKILL.md').write_text('mutated')
            ownership = {
                'canonical_skill_repository': 'leandroclf/product-platform',
                'canonical_skill_path': 'packages/kit/skills',
                'allowed_divergences': {
                    'security': 'pending-structured-security-skill-reconciliation'
                },
            }
            errors = validate_skills.provenance_errors(team, ownership)
            self.assertTrue(any('backend: snapshot differs' in error for error in errors))

    def test_legacy_repository_ownership_is_rejected(self):
        legacy = {
            'canonical_skill_repository': 'leandroclf/ai-kit',
            'canonical_skill_path': 'packages/kit/skills',
            'allowed_divergences': {
                'security': 'pending-structured-security-skill-reconciliation'
            },
        }
        errors = validate_skills.provenance_errors(validate_skills.ROOT, legacy)
        self.assertTrue(any('canonical skill ownership' in error for error in errors))

    def test_cycle_and_unknown_dependency_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills = root / "skills"
            for name, dependency in (("one", "two"), ("two", "one")):
                folder = skills / name
                folder.mkdir(parents=True)
                (folder / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: test\n---\n# Skill\n"
                    "## Inputs\n- request\n## Outputs\n- result\n"
                    "## Boundaries\n- bounded\n## Validation\n- check\n"
                )
            (skills / "catalog.yaml").write_text(
                "catalog_version: 1.0.0\nskills:\n"
                "  - id: one\n    path: skills/one\n    version: 1.0.0\n"
                "    status: stable\n    category: implementation\n    risk: R1\n"
                "    tags: [x]\n    owner: test\n    requires: [two, missing]\n"
                "    composes_with: []\n    supported_surfaces: [codex]\n"
                "    inputs: [x]\n    outputs: [x]\n    quality_gates: [x]\n"
                "  - id: two\n    path: skills/two\n    version: 1.0.0\n"
                "    status: stable\n    category: implementation\n    risk: R1\n"
                "    tags: [x]\n    owner: test\n    requires: [one]\n"
                "    composes_with: []\n    supported_surfaces: [codex]\n"
                "    inputs: [x]\n    outputs: [x]\n    quality_gates: [x]\n"
            )
            with patch.object(validate_skills, "ROOT", root), patch.object(validate_skills, "CATALOG", skills / "catalog.yaml"):
                self.assertEqual(validate_skills.main(), 1)
