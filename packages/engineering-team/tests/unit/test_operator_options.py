import json, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from scripts import local_team as team


def config(**extra):
    value = dict(version=2, repository='/tmp/p', provider_image='img', test_image='py:3', checks=['true'], timeout=30, max_cycles=2,
                 max_seconds=300, models=json.loads(json.dumps(team.DEFAULT_MODELS)))
    value.update(extra)
    return value


def value_after(cmd, flag):
    return cmd[cmd.index(flag) + 1]


class OperatorOptionsTests(unittest.TestCase):
    def test_secure_defaults_do_not_relax_the_stage_boundary(self):
        codex = team.provider_command('plan', 'n', config(), Path('/w'), Path('/s'), 'p')
        self.assertEqual(value_after(codex, '--sandbox'), 'read-only')
        tests = team.test_command('n', config(), Path('/w'))
        self.assertIn('/work:uid=1001,gid=1001,mode=700', tests)
        self.assertFalse(any(x.startswith('/work:exec') for x in tests))

    def test_operator_opt_in_is_explicit_and_scoped(self):
        codex = team.provider_command('plan', 'n', config(codex_sandbox='danger-full-access'), Path('/w'), Path('/s'), 'p')
        self.assertEqual(value_after(codex, '--sandbox'), 'danger-full-access')
        # the container hardening stays regardless of the sandbox choice
        for flag in ('--read-only', '--cap-drop', '--security-opt'):
            self.assertIn(flag, codex)
        self.assertIn('/work:exec,uid=1001,gid=1001,mode=700', team.test_command('n', config(test_tmpfs_exec=True), Path('/w')))
        claude = team.provider_command('implement', 'n', config(codex_sandbox='danger-full-access'), Path('/w'), Path('/s'), 'p')
        self.assertNotIn('danger-full-access', claude)
        self.assertNotIn('--sandbox', claude)

    def test_config_validation_of_the_options(self):
        team.validate_config(config())
        team.validate_config(config(codex_sandbox='danger-full-access', test_tmpfs_exec=True, implement_parts=2))
        for bad in ({'codex_sandbox': 'workspace-write'}, {'codex_sandbox': True}, {'test_tmpfs_exec': 1}, {'test_tmpfs_exec': 'yes'}, {'unknown': 1}):
            with self.assertRaises(team.Blocked, msg=str(bad)):
                team.validate_config(config(**bad))


if __name__ == '__main__':
    unittest.main()
