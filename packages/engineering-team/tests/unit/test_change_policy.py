import unittest
from pathlib import Path
from scripts import change_policy


class RiskAndQualityPolicyTests(unittest.TestCase):
    def test_sensitive_paths_escalate_without_trusting_issue(self):
        paths = [
            '.github/workflows/deploy.yml',
            'src/auth/login.ts',
            'prisma/schema.prisma',
            'infra/main.tf',
            'Dockerfile',
            '.env.production',
            'package-lock.json',
            'src/security/access.py',
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(change_policy.classify_path(path), 'R2')
                with self.assertRaisesRegex(ValueError, 'R2'):
                    change_policy.ensure_authorized('R1', [path])

    def test_safe_scope_passes_and_docs_are_r0(self):
        self.assertEqual(change_policy.classify_paths(['docs/README.md']), 'R0')
        self.assertEqual(change_policy.ensure_authorized('R0', ['docs/README.md']), 'R0')
        self.assertEqual(change_policy.ensure_authorized('R1', ['src/parser.py']), 'R1')

    def test_s01_r0_fixture_target_exists_under_docs_path(self):
        team_root = Path(__file__).resolve().parents[2]
        target = team_root / 'validation/fixtures/s01-doc-task/docs/target.md'
        self.assertTrue(target.is_file(), 'S01 R0 target must exist under a docs/ path')
        relative = target.relative_to(team_root).as_posix()
        self.assertEqual(change_policy.classify_path(relative), 'R0')

    def test_claimed_r0_cannot_mutate_code(self):
        with self.assertRaises(ValueError):
            change_policy.ensure_authorized('R0', ['src/parser.py'])

    def test_untrusted_paths_fail_closed(self):
        for path in ('../etc/shadow', '/root/key', 'a\\evil', '', None):
            with self.subTest(path=path):
                self.assertEqual(change_policy.classify_path(path), 'R2')

    def test_r2_r3_require_separate_authorization(self):
        for risk in ('R2', 'R3', 'unexpected'):
            with self.assertRaises(ValueError):
                change_policy.ensure_authorized(risk, ['README.md'])

    def test_explicit_r2_authorization_is_bounded_and_never_authorizes_r3(self):
        self.assertEqual(change_policy.ensure_authorized('R2', ['docs/audits/report.md'], 'R2'), 'R0')
        self.assertEqual(change_policy.ensure_authorized('R2', ['src/auth/login.py'], 'R2'), 'R2')
        with self.assertRaisesRegex(ValueError, 'R2'):
            change_policy.ensure_authorized('R2', ['docs/audits/report.md'])
        with self.assertRaisesRegex(ValueError, 'R3'):
            change_policy.ensure_authorized('R3', ['docs/audits/report.md'], 'R2')

    def test_change_families_select_relevant_required_gates(self):
        result = change_policy.required_quality_surfaces([
            'src/api/routes.py', 'src/database/migration_1.sql',
            'src/components/App.tsx', 'src/integration/queue.py', 'infra/main.tf'
        ])
        for expected in ('api_contract', 'database_migration', 'frontend',
                         'integration', 'infrastructure', 'security_and_approval'):
            self.assertIn(expected, result)

    def test_static_sites_and_visual_assets_require_frontend_checks(self):
        for path in ['index.html', 'styles.css', 'src/theme.scss', 'src/Product.vue',
                     'src/Card.svelte', 'assets/hero.webp', 'public/logo.svg']:
            with self.subTest(path=path):
                self.assertIn('frontend', change_policy.required_quality_surfaces([path]))
        for path in ['src/parser.py', 'docs/guide.md', 'tests/fixtures/reference.png',
                     'tests/fixtures/sample.html', 'tests/fixtures/theme.css', 'docs/architecture.svg']:
            with self.subTest(path=path):
                self.assertNotIn('frontend', change_policy.required_quality_surfaces([path]))


if __name__ == '__main__':
    unittest.main()
