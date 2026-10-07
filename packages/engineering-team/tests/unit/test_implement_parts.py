import json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from scripts import local_team as team
import task_insight as ti


def config(repo, parts=None):
    value = dict(version=2, repository=repo, provider_image='ai-eng-provider-cli:local', test_image='python:3.12-slim',
                 checks=['true'], timeout=30, max_cycles=2, max_seconds=300, models=json.loads(json.dumps(team.DEFAULT_MODELS)))
    if parts is not None:
        value['implement_parts'] = parts
    return value


def plan(sha):
    return dict(schema_version='1.0.0', base_sha=sha, status='READY', risk='R1', objective='Improve', out_of_scope=[], assumptions=[],
                validation=['checks'], tasks=[dict(id=f'T{i}', description=f'Change {i}', acceptance_ids=[f'AC{i}']) for i in (1, 2, 3)],
                acceptance_criteria=[dict(id=f'AC{i}', description=f'Done {i}') for i in (1, 2, 3)])


def assessment(role, sha, planned):
    gates = dict(quality='PASS', security='PASS', architecture='NOT_REQUESTED', observability='NOT_REQUESTED')
    return dict(schema_version='1.0.0', reviewer=role, head_sha=sha, verdict='PASS', gates=gates, findings=[], checks_executed=['x'],
                residual_risks=[], plan_id=team.plan_id(planned), plan_status='VALID',
                acceptance_results=[dict(id=f'AC{i}', status='PASS', evidence='inspected') for i in (1, 2, 3)])


class ImplementPartsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        env = patch.dict(os.environ, {'XDG_STATE_HOME': str(self.root / 'state')}); env.start(); self.addCleanup(env.stop)

    def setup_run(self, parts):
        target = self.root / 'target'; target.mkdir()
        subprocess.run(['git', 'init', '-q', str(target)], check=True)
        (target / 'file').write_text('before')
        subprocess.run(['git', '-C', str(target), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(target), '-c', 'user.name=t', '-c', 'user.email=t@l', 'commit', '-qm', 'base'], check=True)
        task = 'c' * 32; path = team.home() / 'runs' / task; path.mkdir(parents=True)
        team.atomic(path / 'state.json', dict(version=2, task=task, repository=str(target), config=config(str(target), parts),
            request='Improve file', base_sha=team.git(target, 'rev-parse', 'HEAD'), created_at=time.time(), status='RUNNING',
            phase='CLONE', cycle=0, active=None))
        return task, path

    def executor(self, fail_tests_once=None):
        def run(path, state, cmd, label, container=None):
            out = path / (label + '.stdout'); out.write_text('')
            if label.endswith('-plan'):
                team.atomic(path / ('staging-' + label) / 'result.json', plan(team.git(path / 'workspace', 'rev-parse', 'HEAD')))
            elif label.endswith('-implement'):
                with (path / 'workspace' / 'file').open('a') as fh:
                    fh.write(f' after {label}')
                out.write_text(json.dumps({'type': 'result', 'structured_output': dict(plan_id=state['plan_id'], status='COMPLETE', summary=f'did {label}')}))
            elif label.endswith('-validate'):
                team.atomic(path / ('staging-' + label) / 'result.json', assessment('sentinel', team.git(path / 'workspace', 'rev-parse', 'HEAD'), state['plan']))
            elif label.endswith('-review'):
                out.write_text(json.dumps({'type': 'result', 'structured_output': assessment('atlas', state['head_sha'], state['plan'])}))
            elif label.endswith('-tests') and fail_tests_once and not fail_tests_once.pop():
                return 1, out
            return 0, out
        return run

    def test_partition_is_contiguous_balanced_and_bounded(self):
        tasks = lambda n: {'tasks': [{'id': f'T{i}'} for i in range(1, n + 1)]}
        self.assertEqual(team.plan_parts(tasks(7), 3), [['T1', 'T2', 'T3'], ['T4', 'T5'], ['T6', 'T7']])
        self.assertEqual(team.plan_parts(tasks(2), 4), [['T1'], ['T2']])
        self.assertEqual(team.plan_parts(tasks(3), 1), [['T1', 'T2', 'T3']])
        self.assertEqual(team.stage_label(0, 'implement'), '0-implement'); self.assertEqual(team.stage_label(1, 'implement', 2), '1p2-implement')

    def test_config_accepts_optional_parts_only_in_range(self):
        for value in (1, 2, 4):
            team.validate_config(config('/tmp/p', value))
        team.validate_config(config('/tmp/p'))  # configs written before the option still load
        for value in (0, 5, True, '2'):
            with self.assertRaises(team.Blocked):
                team.validate_config(config('/tmp/p', value))

    def test_split_implementation_runs_fresh_sessions_with_progress_handoff(self):
        task, path = self.setup_run(2)
        with patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=self.executor()):
            team.worker(task)
        state = team.read(path / 'state.json')
        self.assertEqual(state['status'], 'REVIEWED')
        runs = state['stage_runs']
        self.assertEqual([r['stage'] for r in runs], ['plan', 'implement', 'implement', 'validate', 'review'])
        self.assertEqual([(r['label'], r['part'], r['parts']) for r in runs if r['stage'] == 'implement'], [('0-implement', 1, 2), ('0p2-implement', 2, 2)])
        first, second = (path / '0-implement.prompt').read_text(), (path / '0p2-implement.prompt').read_text()
        self.assertIn('session 1 of 2', first); self.assertIn('Implement ONLY these tasks: T1, T2', first)
        self.assertIn('Do not finalize the validation report', first)
        self.assertIn('Implement ONLY these tasks: T3', second); self.assertIn('Earlier sessions already applied T1, T2', second)
        self.assertIn('last session', second)
        self.assertFalse((path / 'handoff-0-implement' / 'progress.md').exists())
        note = (path / 'handoff-0p2-implement' / 'progress.md').read_text()
        self.assertIn('Tasks already implemented: T1, T2', note); self.assertIn('session 1: did 0-implement', note)
        combined = team.read(path / '0-implement.json')['summary']
        self.assertIn('[session 1/2] did 0-implement', combined); self.assertIn('[session 2/2] did 0p2-implement', combined)
        diff = (path / 'handoff-0-review' / 'changes.patch').read_text()
        self.assertIn('after 0-implement', diff); self.assertIn('after 0p2-implement', diff)  # both sessions are in the reviewed commit
        # the panels understand sessions
        self.assertEqual(dict((n, s) for n, s, _ in ti.steps(state, path))['implement'], 'done')
        self.assertEqual([ti.row_tag(r) for r in ti.efficiency(path, state) if r['stage'] == 'implement'], ['1/implement#1', '1/implement#2'])
        self.assertEqual(ti.stage_log(path, 'implement').name, '0p2-implement.stdout')

    def test_repair_cycle_uses_a_single_session(self):
        task, path = self.setup_run(2)
        with patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=self.executor(fail_tests_once=[False])):
            team.worker(task)
        state = team.read(path / 'state.json')
        implement = [r['label'] for r in state['stage_runs'] if r['stage'] == 'implement']
        self.assertEqual(implement, ['0-implement', '0p2-implement', '1-implement'])
        self.assertNotIn('Implement ONLY these tasks', (path / '1-implement.prompt').read_text())
        self.assertEqual(state['status'], 'REVIEWED')

    def test_single_session_is_unchanged_by_default(self):
        task, path = self.setup_run(None)
        with patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=self.executor()):
            team.worker(task)
        state = team.read(path / 'state.json')
        self.assertEqual([r['label'] for r in state['stage_runs'] if r['stage'] == 'implement'], ['0-implement'])
        self.assertNotIn('session 1 of', (path / '0-implement.prompt').read_text())
        self.assertFalse(list(path.glob('*p2-implement*')))


if __name__ == '__main__':
    unittest.main()
