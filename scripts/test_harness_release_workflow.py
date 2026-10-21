"""Exercise the release's effective test cwd, without tag, credentials or publication."""
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseWorkflowTest(unittest.TestCase):
    def test_provenance_step_resolves_module_from_effective_directory(self):
        source = (ROOT / '.github/workflows/harness-release.yml').read_text()
        default = re.search(r'defaults:\n  run:\n    working-directory: (.+)', source).group(1)
        step = source.split('      - name: Test provenance manifest builder\n')[1].split('      - ', 1)[0]
        override = re.search(r'working-directory: (.+)', step)
        cwd = ROOT / (override.group(1) if override else default)
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        result = subprocess.run([sys.executable, '-m', 'unittest', 'scripts.test_build_release_manifest', '-v'],
                                cwd=cwd, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('scripts.test_harness_release_workflow', step)

    def test_ci_and_release_freeze_build_toolchain(self):
        for name in ('harness.yml', 'harness-release.yml'):
            source = (ROOT / '.github/workflows' / name).read_text()
            with self.subTest(workflow=name):
                self.assertIn('run: npm ci', source)
                self.assertNotIn('run: npm install', source)
                self.assertIn('pip install -r ../../requirements-build.txt', source)
                self.assertIn('pip wheel --no-deps --no-build-isolation', source)
                self.assertIn("python-version: '3.12'", source)


if __name__ == '__main__':
    unittest.main()
