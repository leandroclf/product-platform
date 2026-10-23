import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cpb", ROOT / "scripts/check-package-boundaries.py")
cpb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpb)
CONFIG = json.loads((ROOT / "platform-packages.json").read_text())


class BoundaryTest(unittest.TestCase):
    def tree(self, files):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__('shutil').rmtree, tmp)
        for rel, text in files.items():
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / rel).write_text(text)
        return tmp

    def check(self, files):
        return cpb.violations(CONFIG, self.tree(files))

    def test_real_repository_respects_the_graph(self):
        self.assertEqual(cpb.violations(CONFIG), [])

    def test_allowed_dependencies_and_docs_are_not_violations(self):
        self.assertEqual(self.check({
            "packages/harness/src/a.ts": "// o harness depende do kit: packages/kit/contracts",
            "packages/kit/docs/GUIA.md": "veja packages/harness/ e ../cli/",
            "packages/cli/src/a.py": "p = 'packages/kit/contracts'",
        }), [])

    def test_kit_cannot_reference_other_packages(self):
        out = self.check({"packages/kit/scripts/x.cjs": "require('../../harness/dist/index.js')"})
        self.assertTrue(any("kit referencia o caminho do pacote harness" in v for v in out), out)

    def test_cli_cannot_reference_engineering_team_or_harness(self):
        out = self.check({"packages/cli/src/a.py": "open('packages/engineering-team/scripts/x.py')",
                          "packages/cli/src/b.py": "open('../harness/x')"})
        self.assertEqual(len(out), 2, out)

    def test_manifest_dependencies_are_checked(self):
        out = self.check({
            "packages/cli/pyproject.toml": '[project]\ndependencies = ["product-platform-harness>=0.2"]',
            "packages/engineering-team/package.json": json.dumps({"dependencies": {"@leandroclf/product-platform-cli": "1"}}),
        })
        self.assertEqual(len(out), 2, out)

    def test_real_python_distribution_and_imports_are_rejected(self):
        for path, content in {
            "packages/harness/pyproject.toml": '[project]\ndependencies = ["omnicli>=0.4"]',
            "packages/harness/requirements.txt": 'OmniCLI[dev]>=0.4; python_version>="3.11"',
            "packages/harness/a.py": 'from omnicli.cli import app',
            "packages/kit/b.py": 'import product_platform_harness.events',
        }.items():
            with self.subTest(path=path):
                self.assertTrue(self.check({path: content}))

    def test_nested_optional_manifests_and_package_subpaths(self):
        out = self.check({
            "packages/kit/nested/package.json": json.dumps({"optionalDependencies": {"@lf-solucoes/design-system": "1"}}),
            "packages/kit/a.ts": 'import { x } from "@leandroclf/product-platform-harness/events";',
            "packages/kit/nested/pyproject.toml": '[project.optional-dependencies]\ndev = ["product_platform_harness>=0.2"]',
        })
        self.assertEqual(len(out), 3, out)

    def test_allowed_imports_and_similar_names_are_not_rejected(self):
        self.assertEqual(self.check({
            "packages/harness/a.py": 'from .omnicli import local\nimport omnicli_helpers',
            "packages/harness/package.json": json.dumps({"dependencies": {"omnicli-helper": "1"}}),
            "packages/cli/a.ts": 'import x from "product-platform-kit";',
        }), [])

    def test_real_identity_is_discovered_without_manual_alias(self):
        out = self.check({
            "packages/cli/pyproject.toml": '[project]\nname = "proposal-tool"',
            "packages/harness/pyproject.toml": '[project]\ndependencies = ["proposal_tool>=1"]',
        })
        self.assertEqual(len(out), 1, out)

    def test_cycles_are_rejected(self):
        config = {"packages": {
            "a": {"path": "packages/a", "depends_on": ["b"]},
            "b": {"path": "packages/b", "depends_on": ["a"]},
        }}
        self.assertTrue(cpb.violations(config, self.tree({})))

    def test_invalid_graph_is_rejected(self):
        bad = {"packages": {"a": {"path": "packages/a", "depends_on": ["a"]}, "b": {"path": "packages/b", "depends_on": ["zzz"]}}}
        self.assertEqual(len(cpb.violations(bad, self.tree({"packages/a/x.py": "", "packages/b/x.py": ""}))), 2)


if __name__ == "__main__":
    unittest.main()
