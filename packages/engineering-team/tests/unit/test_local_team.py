import json
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import local_team as team


def config(repo='/tmp/project'):
    return dict(version=2, repository=repo, provider_image='ai-eng-provider-cli:local',
                test_image='python:3.12-slim', checks=['python -m unittest discover -v'],
                timeout=30, max_cycles=2, max_seconds=300, models=json.loads(json.dumps(team.DEFAULT_MODELS)))


def review(role='sentinel', sha='a' * 40):
    return dict(schema_version='1.0.0', reviewer=role, head_sha=sha, verdict='PASS',
                gates=dict(quality='PASS', security='PASS', architecture='NOT_REQUESTED', observability='NOT_REQUESTED'),
                findings=[], checks_executed=['offline tests'], residual_risks=[])


def plan(sha='a' * 40, risk='R1'):
    return dict(schema_version='1.0.0', base_sha=sha, status='READY', risk=risk,
                objective='Improve file', out_of_scope=[], assumptions=[], validation=['offline checks'],
                tasks=[dict(id='T1', description='Change file', acceptance_ids=['AC1'])],
                acceptance_criteria=[dict(id='AC1', description='File improved')], capability_decisions=[])


def assessment(role, sha, planned):
    value = review(role, sha)
    value.update(plan_id=team.plan_id(planned), plan_status='VALID',
                 acceptance_results=[dict(id='AC1', status='PASS', evidence='file and offline checks inspected')])
    return value


class LocalTeamTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {'XDG_STATE_HOME': str(self.root / 'state')})
        self.env.start(); self.addCleanup(self.env.stop)

    def test_quality_family_missing_blocks_before_tests(self):
        workspace = self.root / 'ws'
        workspace.mkdir()
        state = {'base_sha': 'a' * 40, 'plan': {'risk': 'R1'},
                 'config': config()}
        def git_response(repo, *args):
            return 'src/api/routes.py' if 'diff' in args else 'b' * 40
        with patch.object(team, 'git', side_effect=git_response):
            with self.assertRaisesRegex(team.Blocked, 'api_contract'):
                team.verify_change_surface(workspace, state)
        self.assertNotIn('change_surface', state)

    def test_authorized_r2_sensitive_path_still_requires_specialized_check(self):
        workspace = self.root / 'ws'; workspace.mkdir()
        request = 'Inspect authorization'
        state = {'base_sha': 'a' * 40, 'plan': {'risk': 'R2'}, 'config': config(),
            'repository': '/repo', 'request': request, 'authorized_risk': 'R2',
            'risk_authorization': {'method': 'cli --authorize-r2', 'repository': '/repo',
                'base_sha': 'a' * 40, 'request_sha256': hashlib.sha256(request.encode()).hexdigest()}}
        def git_response(repo, *args):
            return 'src/auth/login.py' if 'diff' in args else 'b' * 40
        with patch.object(team, 'git', side_effect=git_response), self.assertRaisesRegex(team.Blocked, 'security_and_approval'):
            team.verify_change_surface(workspace, state)

    def test_named_quality_check_runs_in_offline_container(self):
        configuration = config()
        configuration['quality_checks'] = {'api_contract': 'python -m unittest tests.test_api'}
        self.assertEqual(team.validate_config(configuration), configuration)
        script = team.test_command('quality', configuration, Path('/task/workspace'))[-1]
        self.assertIn('python -m unittest discover -v', script)
        self.assertIn('python -m unittest tests.test_api', script)
        self.assertIn('--network', team.test_command('quality', configuration, Path('/task/workspace')))
        workspace = self.root / 'ws'
        workspace.mkdir()
        state = {'base_sha': 'a' * 40, 'plan': {'risk': 'R1'},
                 'config': configuration}
        def git_response(repo, *args):
            return 'src/api/routes.py' if 'diff' in args else 'b' * 40
        with patch.object(team, 'git', side_effect=git_response):
            self.assertEqual(team.verify_change_surface(workspace, state)['required_gates'], ['api_contract'])

    def test_named_quality_checks_require_known_unique_families(self):
        for bad in ({'bogus': 'echo ok'}, {'api_contract': ''},
                    {'frontend': 123}, {'infrastructure': None}):
            with self.subTest(bad=bad), self.assertRaises(team.Blocked):
                team.validate_config(dict(config(), quality_checks=bad))

    def test_invalid_config_rejects_extra_keys_empty_checks_bool_budget(self):
        for change in ({'checks': []}, {'timeout': True}, {'max_cycles': 6}, {'extra': 1}, {'test_image': '--privileged'}):
            with self.subTest(change=change), self.assertRaises(team.Blocked):
                team.validate_config(dict(config(), **change))

    def test_atomic_state_is_private_and_replaced(self):
        path = team.home() / 'state.json'
        team.atomic(path, {'revision': 1}); team.atomic(path, {'revision': 2})
        self.assertEqual(team.read(path), {'revision': 2})
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertFalse(list(path.parent.glob('*.tmp')))

    def test_exclusive_lock_blocks_another_owner(self):
        with team.lock(self.root / 'lock'), self.assertRaises(team.Blocked):
            with team.lock(self.root / 'lock'):
                pass

    def test_test_container_has_no_account_mount_or_network(self):
        cmd = team.test_command('ai-team-tests', config(), Path('/task/workspace'))
        self.assertEqual(cmd[cmd.index('--network') + 1], 'none')
        self.assertIn('/task/workspace:/source:ro', cmd)
        self.assertIn('--read-only', cmd)
        self.assertNotIn('--privileged', cmd)
        self.assertFalse(any('home:/home' in x or 'docker.sock' in x for x in cmd))

    def test_acl_checkout_access_is_narrow_and_excludes_git_metadata(self):
        workspace = self.root / 'clone'
        workspace.mkdir()
        (workspace / '.git').mkdir()
        (workspace / '.git' / 'config').write_text('private metadata')
        (workspace / 'src').mkdir()
        (workspace / 'src' / 'module.py').write_text('print(1)')
        (workspace / 'symlink').symlink_to(workspace / '.git', target_is_directory=True)
        calls = []
        def fake_run(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, '', '')
        with patch.object(team.shutil, 'which', return_value='/usr/bin/setfacl'), \
             patch.object(team.subprocess, 'run', side_effect=fake_run):
            team.grant_agent_checkout_access(workspace)
        self.assertTrue(calls)
        self.assertTrue(any('-d' in call for call in calls))
        self.assertTrue(all('u:1001:rwX' in call for call in calls))
        self.assertFalse(any(str(workspace / '.git') in entry
                             for call in calls for entry in call))
        self.assertFalse(any(str(workspace / 'symlink') in entry
                             for call in calls for entry in call))
        self.assertTrue(any(str(workspace / 'src' / 'module.py') in call for call in calls))
        self.assertFalse(any('a+rwX' in entry for call in calls for entry in call))

    def test_acl_missing_dependency_blocks_before_widening_permissions(self):
        workspace = self.root / 'clone'
        workspace.mkdir()
        (workspace / '.git').mkdir()
        with patch.object(team.shutil, 'which', return_value=None):
            with self.assertRaises(team.Blocked):
                team.grant_agent_checkout_access(workspace)

    def test_agent_git_metadata_is_read_only_and_reviews_have_no_bash(self):
        volumes = []
        for kind in team.STAGES:
            cmd = team.provider_command(kind, 'agent', config(), Path('/workspace'), Path('/stage'), 'request')
            self.assertIn('/workspace/.git:/work/.git:ro', cmd)
            self.assertIn('/workspace:/work' + ('' if kind == 'implement' else ':ro'), cmd)
            self.assertEqual(cmd[cmd.index('--model') + 1], config()['models'][kind]['model'])
            self.assertFalse(any(x in cmd for x in ('--resume', '--continue', '--dangerously-skip-permissions')))
            volumes.append(next(x for x in cmd if '-home:/home/agent' in x))
        self.assertEqual(len(set(volumes)), 4)
        cmd = team.provider_command('review', 'agent', config(), Path('/workspace'), Path('/stage'), 'request')
        self.assertEqual(cmd[cmd.index('--tools') + 1], 'Read,Grep,Glob')
        cmd = team.provider_command('implement', 'agent', config(), Path('/workspace'), Path('/stage'), 'request')
        self.assertEqual(cmd[cmd.index('--tools') + 1], 'Read,Grep,Glob,Edit,Write')
        self.assertIn('Bash,Agent,mcp__*', cmd)

    def test_review_requires_same_head_role_security_and_verified_findings(self):
        value = review()
        self.assertTrue(team.review_pass(value, 'a' * 40, 'sentinel'))
        self.assertFalse(team.review_pass(value, 'b' * 40, 'sentinel'))
        self.assertFalse(team.review_pass(value, 'a' * 40, 'argus'))
        value['gates']['security'] = 'NOT_REQUESTED'
        self.assertFalse(team.review_pass(value, 'a' * 40, 'sentinel'))
        value = review(); value['findings'] = [dict(id='F1', severity='HIGH', status='RESOLVED', verified=False, summary='risk')]
        self.assertFalse(team.review_pass(value, 'a' * 40, 'sentinel'))

    def test_medium_findings_require_verified_resolution(self):
        for severity in ('MEDIUM', 'HIGH', 'CRITICAL'):
            with self.subTest(severity=severity):
                value = review()
                value['verdict'] = 'PASS_WITH_FINDINGS'
                value['findings'] = [dict(id='F1', severity=severity, status='OPEN',
                                          verified=False, summary='Unresolved finding')]
                self.assertFalse(team.review_pass(value, 'a' * 40, 'sentinel'))
                value['findings'][0].update(status='RESOLVED', verified=False)
                self.assertFalse(team.review_pass(value, 'a' * 40, 'sentinel'))
                value['findings'][0]['verified'] = True
                self.assertTrue(team.review_pass(value, 'a' * 40, 'sentinel'))

    def test_low_open_findings_allowed_only_as_declared_residual(self):
        value = review()
        value['verdict'] = 'PASS_WITH_FINDINGS'
        value['findings'] = [dict(id='F1', severity='LOW', status='OPEN',
                                  verified=False, summary='Low residual impact')]
        self.assertTrue(team.review_pass(value, 'a' * 40, 'sentinel'))
        value['findings'][0]['status'] = 'RESOLVED'
        self.assertFalse(team.review_pass(value, 'a' * 40, 'sentinel'))
        value['findings'][0]['verified'] = True
        self.assertTrue(team.review_pass(value, 'a' * 40, 'sentinel'))

    def test_terminal_or_ambiguous_run_cannot_resume(self):
        path = self.root / 'task'; path.mkdir()
        for status in ('DELIVERY_PENDING', 'REVIEWED', 'STOPPED', 'FAILED'):
            team.atomic(path / 'state.json', {'status': status})
            with self.assertRaises(team.Blocked):
                team.start(path)

    def test_invalid_task_id_never_escapes_state_root(self):
        for value in ('../project', '/tmp/file', 'a' * 31, 'Z' * 32):
            with self.assertRaises(team.Blocked):
                team.run_path(value)

    def test_provider_env_does_not_inherit_api_or_transport_credentials(self):
        with patch.dict(os.environ, {'GH_TOKEN': 'private', 'OPENAI_API_KEY': 'private', 'ANTHROPIC_API_KEY': 'private', 'SSH_AUTH_SOCK': 'private'}):
            self.assertTrue(all(x not in team.env_without_authority() for x in ('GH_TOKEN', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'SSH_AUTH_SOCK')))

    def test_target_stays_unchanged_when_delivery_imports_branch(self):
        target = self.root / 'target'; target.mkdir()
        subprocess.run(['git', 'init', '-q', str(target)], check=True)
        (target / 'file').write_text('before')
        subprocess.run(['git', '-C', str(target), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(target), '-c', 'user.name=test', '-c', 'user.email=test@local', 'commit', '-qm', 'base'], check=True)
        base = team.git(target, 'rev-parse', 'HEAD')
        task = 'a' * 32; path = team.home() / 'runs' / task; path.mkdir(parents=True)
        workspace = path / 'workspace'
        subprocess.run(['git', 'clone', '-q', str(target), str(workspace)], check=True)
        (workspace / 'file').write_text('after')
        sha = team.snapshot(workspace, {'request': 'change'})
        planned = plan(base)
        team.atomic(path / 'state.json', dict(version=2, repository=str(target), status='REVIEWED',
                    head_sha=sha, base_sha=base, plan=planned, plan_id=team.plan_id(planned),
                    config=config(str(target)), cycle=0))
        team.atomic(path / '0-tests.json', dict(head_sha=sha, exit_code=0))
        for kind in ('validate', 'review'):
            team.atomic(path / f'0-{kind}.json', assessment(team.STAGES[kind][0], sha, planned))
        team.deliver(task)
        self.assertEqual(team.git(target, 'rev-parse', 'HEAD'), base)
        self.assertEqual((target / 'file').read_text(), 'before')
        self.assertEqual(team.git(target, 'rev-parse', 'ai-team/' + task), sha)
        team.deliver(task)  # Repeated local delivery is idempotent.

    def test_execute_preserves_nonzero_exit_hash_and_timeout(self):
        path = self.root / 'evidence'; path.mkdir()
        state = dict(config=config(), created_at=__import__('time').time())
        code, output = team.execute(path, state, ['sh', '-c', 'printf evidence; exit 9'], 'failure')
        self.assertEqual(code, 9); self.assertEqual(output.read_text(), 'evidence')
        self.assertEqual(state['commands'][0]['exit_code'], 9)
        state['config']['timeout'] = 1
        with self.assertRaises(team.Blocked):
            team.execute(path, state, ['sh', '-c', 'sleep 10'], 'timeout')
        self.assertIsNone(state['active'])

    def test_provider_error_event_is_failure_even_without_nonzero_exit(self):
        path = self.root / 'events'
        path.write_text('{"type":"turn.failed","error":"controlled"}\n')
        self.assertTrue(team.provider_failed(path))
        path.write_text('{"type":"turn.completed"}\n')
        self.assertFalse(team.provider_failed(path))

    def setup_run(self):
        target = self.root / 'target'; target.mkdir()
        subprocess.run(['git', 'init', '-q', str(target)], check=True)
        (target / 'file').write_text('before')
        subprocess.run(['git', '-C', str(target), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(target), '-c', 'user.name=test', '-c', 'user.email=test@local', 'commit', '-qm', 'base'], check=True)
        base = team.git(target, 'rev-parse', 'HEAD')
        task = 'b' * 32; path = team.home() / 'runs' / task; path.mkdir(parents=True)
        team.atomic(path / 'state.json', dict(version=2, task=task, repository=str(target), config=config(str(target)),
            request='Improve file', base_sha=base, created_at=__import__('time').time(), status='RUNNING', phase='CLONE', cycle=0, active=None))
        return task, path, target, base

    def controlled_executor(self, path, state, cmd, label, container=None):
        output = path / (label + '.stdout')
        output.write_text('')
        if label.endswith('-plan'):
            sha = team.git(path / 'workspace', 'rev-parse', 'HEAD')
            result = dict(plan(sha, getattr(self, 'planned_risk', 'R1')),
                          capability_decisions=getattr(self, 'plan_decisions', []))
            result['status'] = getattr(self, 'planned_status', 'READY')
            result['assumptions'] = getattr(self, 'planned_assumptions', ['test assumption'])
            team.atomic(path / ('staging-' + label) / 'result.json', result)
        elif label.endswith('-implement'):
            if not getattr(self, 'skip_default_file_change', False):
                (path / 'workspace' / 'file').write_text('after ' + label)
            extra_path = getattr(self, 'extra_changed_path', None)
            if extra_path:
                extra = path / 'workspace' / extra_path
                extra.parent.mkdir(parents=True, exist_ok=True)
                extra.write_text('security policy change')
            output.write_text(json.dumps({'structured_output': dict(plan_id=state['plan_id'], status='COMPLETE', summary='Implemented')}))
        elif label.endswith('-validate'):
            sha = team.git(path / 'workspace', 'rev-parse', 'HEAD')
            team.atomic(path / ('staging-' + label) / 'result.json', assessment('sentinel', sha, state['plan']))
        elif label.endswith('-review'):
            output.write_text(json.dumps({'structured_output': assessment('atlas', state['head_sha'], state['plan'])}))
        return 0, output

    def test_complete_local_workflow_with_controlled_providers_preserves_target(self):
        task, path, target, base = self.setup_run()
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=self.controlled_executor):
            team.worker(task)
        state = team.read(path / 'state.json')
        self.assertEqual(state['status'], 'REVIEWED')
        self.assertNotEqual(state['head_sha'], base)
        self.assertEqual(team.git(target, 'rev-parse', 'HEAD'), base)
        self.assertEqual((target / 'file').read_text(), 'before')
        self.assertEqual(team.read(path / '0-validate.json')['head_sha'], state['head_sha'])
        self.assertEqual(team.read(path / '0-review.json')['head_sha'], state['head_sha'])
        self.assertEqual([x['stage'] for x in state['stage_runs']], ['plan', 'implement', 'validate', 'review'])
        self.assertTrue((path / 'workspace' / 'openspec' / 'changes' / ('ai-team-' + task) / '0' / 'tasks.md').exists())
        generated = path / 'workspace' / 'openspec' / 'changes' / ('ai-team-' + task) / '0'
        self.assertEqual(generated.stat().st_mode & 0o002, 0)
        self.assertEqual((generated / 'tasks.md').stat().st_mode & 0o002, 0)
        self.assertTrue(all(x['resolved_model'] is None for x in state['stage_runs']))
        self.assertIn('after 0-implement', (path / 'handoff-0-review' / 'changes.patch').read_text())
        self.assertFalse((path / 'handoff-0-review' / 'validate.json').exists())

    def test_r0_document_task_with_unchanged_host_records_reaches_review(self):
        task, path, target, base = self.setup_run()
        self.skip_default_file_change = True
        self.extra_changed_path = 'docs/audit.md'
        self.planned_risk = 'R0'
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=self.controlled_executor):
            team.worker(task)
        state = team.read(path / 'state.json')
        self.assertEqual(state['status'], 'REVIEWED')
        self.assertEqual(state['change_surface']['risk'], 'R0')
        self.assertEqual(state['change_surface']['paths'], ['docs/audit.md'])
        review_patch = (path / 'handoff-0-review' / 'changes.patch').read_text()
        self.assertIn('docs/audit.md', review_patch)
        self.assertIn('openspec/changes/ai-team-' + task + '/0/tasks.md', review_patch)
        self.assertEqual(team.git(target, 'rev-parse', 'HEAD'), base)

    def test_modified_host_openspec_record_blocks_change_surface(self):
        workspace = self.root / 'ws'; workspace.mkdir()
        relative = 'openspec/changes/ai-team-' + ('b' * 32) + '/0/tasks.md'
        artifact = workspace / relative
        artifact.parent.mkdir(parents=True)
        artifact.write_text('modified')
        state = {'task': 'b' * 32, 'base_sha': 'a' * 40, 'plan': {'risk': 'R0'},
            'repository': '/repo', 'request': 'R0 docs', 'config': config(),
            'host_openspec_sha256': {relative: hashlib.sha256(b'host content').hexdigest()}}
        with patch.object(team, 'git', return_value=relative), self.assertRaisesRegex(team.Blocked, 'changed after coordinator generation'):
            team.verify_change_surface(workspace, state)

    def test_review_handoff_and_quality_gates_include_ai_team_prefixed_product_changes(self):
        task, path, target, base = self.setup_run()
        self.extra_changed_path = 'openspec/changes/ai-team-older/security-policy.md'
        state = team.read(path / 'state.json')
        state['authorized_risk'] = 'R2'
        state['risk_authorization'] = dict(method='cli --authorize-r2', repository=str(target), base_sha=base,
            request_sha256=hashlib.sha256(state['request'].encode()).hexdigest())
        state['config']['quality_checks'] = {'security_and_approval': 'python -m unittest tests.test_security'}
        team.atomic(path / 'state.json', state)
        self.planned_risk = 'R2'
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=self.controlled_executor):
            team.worker(task)
        result = team.read(path / 'state.json')
        self.assertEqual(result['status'], 'REVIEWED')
        self.assertIn('openspec/changes/ai-team-older/security-policy.md', result['change_surface']['paths'])
        self.assertIn('security_and_approval', result['change_surface']['required_gates'])
        review_patch = (path / 'handoff-0-review' / 'changes.patch').read_text()
        self.assertIn('openspec/changes/ai-team-older/security-policy.md', review_patch)
        self.assertIn('openspec/changes/ai-team-' + task + '/0/tasks.md', review_patch)

    def test_review_handoff_contains_product_and_coordinator_openspec(self):
        task, path, target, base = self.setup_run()
        workspace = path / 'workspace'
        subprocess.run(['git', 'clone', '-q', str(target), str(workspace)], check=True)
        (workspace / 'docs/audits').mkdir(parents=True)
        (workspace / 'docs/audits/report.md').write_text('audit')
        generated = workspace / 'openspec' / 'changes' / ('ai-team-' + task) / '0'
        generated.mkdir(parents=True)
        (generated / 'proposal.md').write_text('coordinator plan')
        project_spec = workspace / 'openspec/changes/product-change'
        project_spec.mkdir(parents=True)
        (project_spec / 'proposal.md').write_text('product proposal')
        subprocess.run(['git', '-C', str(workspace), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(workspace), '-c', 'user.name=test', '-c', 'user.email=test@local', 'commit', '-qm', 'fixture'], check=True)
        diff = team.git(workspace, 'diff', '--no-ext-diff', '--no-textconv', base, 'HEAD')
        self.assertIn('docs/audits/report.md', diff)
        self.assertIn('openspec/changes/ai-team-' + task + '/0/proposal.md', diff)
        self.assertIn('openspec/changes/product-change/proposal.md', diff)

    def test_explicit_r2_authorization_allows_plan_but_keeps_target_isolated(self):
        task, path, target, base = self.setup_run()
        state = team.read(path / 'state.json'); state['authorized_risk'] = 'R2'
        state['risk_authorization'] = dict(method='cli --authorize-r2', repository=str(target), base_sha=base,
            request_sha256=hashlib.sha256(state['request'].encode()).hexdigest())
        team.atomic(path / 'state.json', state)
        self.planned_risk = 'R2'
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=self.controlled_executor):
            team.worker(task)
        result = team.read(path / 'state.json')
        self.assertEqual(result['status'], 'REVIEWED')
        self.assertEqual(result['authorized_risk'], 'R2')
        self.assertEqual(team.git(target, 'rev-parse', 'HEAD'), base)

    def test_r2_authorization_is_bound_to_request_and_base(self):
        task, path, target, base = self.setup_run()
        state = team.read(path / 'state.json'); state['authorized_risk'] = 'R2'
        state['risk_authorization'] = dict(method='cli --authorize-r2', repository=str(target), base_sha=base,
            request_sha256=hashlib.sha256(state['request'].encode()).hexdigest())
        state['request'] = 'Different request'
        with self.assertRaisesRegex(team.Blocked, 'mismatched'):
            team.risk_authorization_ceiling(state)

    def test_r2_plan_without_explicit_authorization_stops_before_implementation(self):
        task, path, target, base = self.setup_run()
        self.planned_risk = 'R2'
        calls = []
        def execute(*args, **kwargs):
            calls.append(args[3])
            return self.controlled_executor(*args, **kwargs)
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute), self.assertRaisesRegex(team.Blocked, 'operator-authorized'):
            team.worker(task)
        self.assertEqual(calls, ['0-plan'])
        self.assertEqual(team.read(path / 'state.json')['status'], 'FAILED')
        self.assertEqual(team.git(target, 'rev-parse', 'HEAD'), base)

    def test_blocked_r2_plan_reports_missing_context_before_authorization(self):
        task, path, target, base = self.setup_run()
        self.planned_risk = 'R2'
        self.planned_status = 'BLOCKED'
        self.planned_assumptions = ['provider contract is missing']
        calls = []
        def execute(*args, **kwargs):
            calls.append(args[3])
            return self.controlled_executor(*args, **kwargs)
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute), self.assertRaisesRegex(team.Blocked, 'provider contract is missing'):
            team.worker(task)
        self.assertEqual(calls, ['0-plan'])
        self.assertEqual(team.read(path / 'state.json')['status'], 'FAILED')
        self.assertEqual(team.git(target, 'rev-parse', 'HEAD'), base)

    def test_legacy_in_progress_task_without_openspec_hashes_fails_closed(self):
        task, path, target, base = self.setup_run()
        state = team.read(path / 'state.json')
        state.update(phase='IMPLEMENT', plan=plan(base))
        team.atomic(path / 'state.json', state)
        calls = []
        def execute(*args, **kwargs):
            calls.append(args[3])
            return self.controlled_executor(*args, **kwargs)
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute), self.assertRaisesRegex(team.Blocked, 'lacks coordinator OpenSpec hashes'):
            team.worker(task)
        self.assertEqual(calls, [])
        self.assertEqual(team.read(path / 'state.json')['status'], 'FAILED')
        self.assertEqual(team.git(target, 'rev-parse', 'HEAD'), base)

    def test_plan_capability_decisions_must_match_the_platform_handoff(self):
        handoff = {'registry_fingerprint': 'a' * 64, 'product': 'site',
                   'capabilities': [{'name': 'entitlements', 'decision': 'REUSE', 'owner': 'product-platform-harness'}]}
        ok = dict(plan(), capability_decisions=[{'name': 'entitlements', 'decision': 'REUSE', 'owner': 'product-platform-harness'}])
        team.validate_plan(ok, 'a' * 40, handoff)
        team.validate_plan(plan(), 'a' * 40)  # no handoff: nothing to enforce
        for bad in ([], [{'name': 'entitlements', 'decision': 'CREATE', 'owner': 'product-platform-harness'}],
                    ok['capability_decisions'] * 2,
                    ok['capability_decisions'] + [{'name': 'payments', 'decision': 'CREATE', 'owner': 'site'}]):
            with self.assertRaises(ValueError):
                team.validate_plan(dict(plan(), capability_decisions=bad), 'a' * 40, handoff)

    def test_blocked_plan_is_not_masked_by_the_capability_gate(self):
        handoff = {'registry_fingerprint': 'a' * 64, 'product': 'site',
                   'capabilities': [{'name': 'entitlements', 'decision': 'REUSE', 'owner': 'product-platform-harness'}]}
        blocked = dict(plan(), status='BLOCKED', assumptions=['Sem leitura do filesystem: bwrap sem permissão.'])
        # Um plano BLOCKED não declara capacidades (o agente não leu o handoff): o motivo real do bloqueio deve prevalecer.
        self.assertEqual(team.validate_plan(blocked, 'a' * 40, handoff)['status'], 'BLOCKED')
        with self.assertRaises(ValueError):  # um plano READY continua obrigado a declarar as capacidades do handoff
            team.validate_plan(dict(plan(), status='READY'), 'a' * 40, handoff)

    def test_stale_registry_blocks_run_inputs(self):
        registry = self.root / 'registry.yaml'; registry.write_text('capabilities: []')
        digest = __import__('hashlib').sha256(registry.read_bytes()).hexdigest()
        h = self.root / 'handoff.json'
        h.write_text(json.dumps({'registry_fingerprint': digest, 'product': 'site',
            'capabilities': [{'name': 'x', 'decision': 'CREATE', 'owner': 'site'}]}))
        self.assertIn('capabilities.json', team.platform_inputs(str(h), [], str(registry)))
        registry.write_text('capabilities: [changed]')
        with self.assertRaises(team.Blocked):
            team.platform_inputs(str(h), [], str(registry))
        with self.assertRaises(team.Blocked):
            team.platform_inputs(None, [], str(registry))

    def test_platform_rules_reach_every_stage_and_are_recorded(self):
        task, path, target, base = self.setup_run()
        handoff = {'registry_fingerprint': 'a' * 64, 'product': 'site',
                   'capabilities': [{'name': 'entitlements', 'decision': 'REUSE', 'owner': 'product-platform-harness'}]}
        rules = self.root / 'DELIVERY.md'; rules.write_text('# regras')
        h = self.root / 'handoff.json'; h.write_text(json.dumps(handoff))
        state = team.read(path / 'state.json')
        self.plan_decisions = handoff['capabilities']
        state['platform'] = team.freeze_platform(path, team.platform_inputs(str(h), [str(rules)]))
        team.atomic(path / 'state.json', state)
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=self.controlled_executor):
            team.worker(task)
        state = team.read(path / 'state.json')
        self.assertEqual(state['status'], 'REVIEWED')
        self.assertTrue(all(x['platform'] == state['platform']['fingerprint'] for x in state['stage_runs']))
        for label in ('0-plan', '0-implement', '0-validate', '0-review'):
            self.assertEqual((path / ('handoff-' + label) / 'rules' / 'DELIVERY.md').read_text(), '# regras')
            self.assertEqual(json.loads((path / ('handoff-' + label) / 'capabilities.json').read_text()), handoff)
            self.assertIn('Platform delivery rules', (path / (label + '.prompt')).read_text())

    def test_failed_checks_trigger_bounded_repair_before_reviews(self):
        task, path, _, _ = self.setup_run()
        calls = []
        def execute(*args, **kwargs):
            label = args[3]; calls.append(label)
            code, out = self.controlled_executor(*args, **kwargs)
            return (1 if label == '0-tests' else code), out
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute):
            team.worker(task)
        self.assertNotIn('0-validate', calls)
        self.assertEqual(calls.count('0-plan'), 1)
        self.assertNotIn('1-plan', calls)
        self.assertEqual(team.read(path / 'state.json')['cycle'], 1)
        self.assertEqual(team.read(path / 'state.json')['status'], 'REVIEWED')

    def test_repeated_failed_checks_exhaust_cycles_without_delivery(self):
        task, path, _, _ = self.setup_run()
        def execute(*args, **kwargs):
            code, out = self.controlled_executor(*args, **kwargs)
            return (1 if args[3].endswith('-tests') else code), out
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute), self.assertRaises(team.Blocked):
            team.worker(task)
        self.assertEqual(team.read(path / 'state.json')['status'], 'FAILED')
        self.assertEqual(team.read(path / 'state.json')['cycle'], 2)
        with self.assertRaises(team.Blocked):
            team.deliver(task)

    def test_tampered_review_sha_blocks_even_when_review_claims_pass(self):
        task, path, _, _ = self.setup_run()
        def execute(*args, **kwargs):
            code, out = self.controlled_executor(*args, **kwargs)
            if args[3].endswith('-validate'):
                team.atomic(path / ('staging-' + args[3]) / 'result.json', assessment('sentinel', 'c' * 40, args[1]['plan']))
            return code, out
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute), self.assertRaises(team.Blocked):
            team.worker(task)
        self.assertEqual(team.read(path / 'state.json')['status'], 'FAILED')

    def test_resume_completed_implementation_checkpoint_without_replaying_argus(self):
        task, path, _, _ = self.setup_run()
        def interrupt(*args, **kwargs):
            if args[3].endswith('-tests'):
                raise SystemExit('controlled crash before test launch')
            return self.controlled_executor(*args, **kwargs)
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=interrupt), self.assertRaises(SystemExit):
            team.worker(task)
        self.assertEqual(team.read(path / 'state.json')['phase'], 'TEST')
        calls = []
        def resume(*args, **kwargs):
            calls.append(args[3]); return self.controlled_executor(*args, **kwargs)
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=resume):
            team.worker(task)
        self.assertNotIn('0-plan', calls)
        self.assertNotIn('0-implement', calls)
        self.assertEqual(team.read(path / 'state.json')['status'], 'REVIEWED')

    def test_dead_process_identity_is_not_confused_with_current_process(self):
        self.assertIsNone(team.proc_identity(999999999))
        # Hosted execution can virtualize getpid differently from procfs. Exercise
        # the Linux parser deterministically; real process visibility is checked on CI/host.
        record = '123 (name with spaces) ' + ' '.join(str(x) for x in range(30))
        with patch.object(Path, 'read_text', return_value=record):
            self.assertEqual(team.proc_identity(123), '19')

    def test_provider_evidence_drops_thinking_but_retains_structured_output(self):
        path = self.root / 'private'; path.mkdir()
        state = dict(config=config(), created_at=__import__('time').time())
        payload = json.dumps({'type': 'result', 'structured_output': review('argus'),
                              'content': [{'type': 'thinking', 'thinking': 'PRIVATE'}]})
        code, output = team.execute(path, state, ['printf', payload], '0-review')
        self.assertEqual(code, 0)
        self.assertNotIn('PRIVATE', output.read_text())
        self.assertEqual(json.loads(output.read_text())['structured_output']['reviewer'], 'argus')

    def test_invalid_plan_blocks_implementation_and_delivery(self):
        for mutation in ('head', 'coverage', 'approval', 'blocked'):
            with self.subTest(mutation=mutation):
                task, path, target, base = self.setup_run()
                calls = []
                def execute(*args, **kwargs):
                    calls.append(args[3])
                    code, out = self.controlled_executor(*args, **kwargs)
                    value = plan(base)
                    if mutation == 'head':
                        value['base_sha'] = 'c' * 40
                    elif mutation == 'coverage':
                        value['tasks'][0]['acceptance_ids'] = ['AC99']
                    elif mutation == 'approval':
                        value['risk'] = 'R3'
                    else:
                        value['status'] = 'BLOCKED'
                    team.atomic(path / 'staging-0-plan' / 'result.json', value)
                    return code, out
                with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute), self.assertRaises(team.Blocked):
                    team.worker(task)
                self.assertEqual(calls, ['0-plan'])
                self.assertEqual(team.git(target, 'rev-parse', 'HEAD'), base)
                self.assertEqual(team.read(path / 'state.json')['status'], 'FAILED')
                # Each subcase uses a new temporary fixture.
                __import__('shutil').rmtree(target)
                __import__('shutil').rmtree(path)

    def test_assessments_require_complete_acceptance_and_current_plan(self):
        planned = plan()
        for mutation in ('plan', 'missing', 'duplicate', 'unverified', 'replan'):
            value = assessment('sentinel', 'a' * 40, planned)
            if mutation == 'plan':
                value['plan_id'] = 'c' * 64
            elif mutation == 'missing':
                value['acceptance_results'] = []
            elif mutation == 'duplicate':
                value['acceptance_results'] *= 2
            elif mutation == 'unverified':
                value['acceptance_results'][0]['status'] = 'INCONCLUSIVE'
            else:
                value['plan_status'] = 'REPLAN_REQUIRED'
            try:
                passed = team.review_pass(value, 'a' * 40, 'sentinel', planned, team.plan_id(planned))
            except (ValueError, team.ValidationError):
                passed = False
            self.assertFalse(passed, mutation)

    def test_replan_required_returns_to_atlas_with_same_bounded_budget(self):
        task, path, _, _ = self.setup_run()
        calls = []
        def execute(*args, **kwargs):
            label = args[3]; calls.append(label)
            code, out = self.controlled_executor(*args, **kwargs)
            if label == '0-validate':
                value = assessment('sentinel', args[1]['head_sha'], args[1]['plan'])
                value['plan_status'] = 'REPLAN_REQUIRED'
                value['verdict'] = 'FAIL'
                team.atomic(path / 'staging-0-validate' / 'result.json', value)
            return code, out
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute):
            team.worker(task)
        self.assertEqual(calls, ['0-plan', '0-implement', '0-tests', '0-validate', '0-review',
                                 '1-plan', '1-implement', '1-tests', '1-validate', '1-review'])
        self.assertNotEqual(team.plan_id(team.read(path / '0-plan.json')), team.plan_id(team.read(path / '1-plan.json')))
        self.assertEqual(team.read(path / 'state.json')['status'], 'REVIEWED')

    def test_implementation_blocked_does_not_run_checks_or_review(self):
        task, path, _, _ = self.setup_run()
        calls = []
        def execute(*args, **kwargs):
            calls.append(args[3])
            code, out = self.controlled_executor(*args, **kwargs)
            if args[3] == '0-implement':
                out.write_text(json.dumps({'structured_output': dict(plan_id=args[1]['plan_id'], status='BLOCKED', summary='Need approval')}))
            return code, out
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute), self.assertRaises(team.Blocked):
            team.worker(task)
        self.assertEqual(calls, ['0-plan', '0-implement'])

    def test_delivery_rechecks_persisted_assessment(self):
        task, path, _, _ = self.setup_run()
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=self.controlled_executor):
            team.worker(task)
        value = team.read(path / '0-review.json')
        value['plan_id'] = 'c' * 64
        team.atomic(path / '0-review.json', value)
        with self.assertRaises(ValueError):
            team.deliver(task)

    def test_openspec_symlink_cannot_escape_workspace(self):
        workspace = self.root / 'workspace'; workspace.mkdir()
        outside = self.root / 'outside'; outside.mkdir()
        (workspace / 'openspec').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(team.Blocked):
            team.record_openspec(workspace, dict(task='a' * 32, cycle=0, plan=plan(), plan_id=team.plan_id(plan()), request='change'))
        self.assertEqual(list(outside.iterdir()), [])

    def test_legacy_tasks_cannot_resume_or_deliver(self):
        path = self.root / 'legacy'; path.mkdir()
        team.atomic(path / 'state.json', dict(version=1, status='RUNNING'))
        with self.assertRaises(team.Blocked):
            team.start(path)
        old = config(); old.pop('models'); old['version'] = 1
        with self.assertRaises(team.Blocked):
            team.validate_config(old)

    def test_login_requires_atlas_stage_and_rejects_role_mismatch(self):
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team.subprocess, 'call', return_value=0) as call:
            self.assertEqual(team.main(['login', 'atlas', '--stage', 'review']), 0)
            cmd = call.call_args.args[0]
            self.assertIn('ai-team-atlas-review-home:/home/agent', cmd)
            self.assertEqual(cmd[-3:], ['claude', 'auth', 'login'])
            for args in (['login', 'atlas'], ['login', 'argus', '--stage', 'plan']):
                with self.assertRaises(team.Blocked):
                    team.main(args)

    def test_init_upgrade_preserves_previous_config_and_fixed_models(self):
        repo = self.root / 'repo'; repo.mkdir()
        stored = team.project_path(repo) / 'config.json'
        old = config(str(repo)); old.pop('models'); old['version'] = 1
        team.atomic(stored, old)
        args = ['init', '--test-image', 'tests:local', '--check', 'true']
        with patch.object(team, 'target', return_value=repo):
            with self.assertRaises(team.Blocked):
                team.main(args)
            self.assertEqual(team.main(args + ['--upgrade']), 0)
        self.assertEqual(team.read(stored)['models'], team.DEFAULT_MODELS)
        backups = list(stored.parent.glob('config-backup-*.json'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(team.read(backups[0]), old)

    def test_implementer_can_request_replan_without_running_stale_checks(self):
        task, path, _, _ = self.setup_run()
        calls = []
        def execute(*args, **kwargs):
            label = args[3]; calls.append(label)
            code, out = self.controlled_executor(*args, **kwargs)
            if label == '0-implement':
                out.write_text(json.dumps({'structured_output': dict(plan_id=args[1]['plan_id'],
                    status='REPLAN_REQUIRED', summary='Plan needs adjustment')}))
            return code, out
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute):
            team.worker(task)
        self.assertNotIn('0-tests', calls)
        self.assertIn('1-plan', calls)
        self.assertEqual(team.read(path / 'state.json')['status'], 'REVIEWED')

    def test_interrupted_review_is_not_replayed(self):
        task, path, _, _ = self.setup_run()
        def execute(*args, **kwargs):
            if args[3] == '0-review':
                raise SystemExit('crash after staging creation')
            return self.controlled_executor(*args, **kwargs)
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute', side_effect=execute), self.assertRaises(SystemExit):
            team.worker(task)
        self.assertEqual(team.read(path / 'state.json')['phase'], 'REVIEW')
        with patch.object(team, 'grant_agent_checkout_access'), patch.object(team, 'image_present'), patch.object(team, 'execute') as run, self.assertRaises(team.Blocked):
            team.worker(task)
        run.assert_not_called()

    def test_model_profiles_cannot_cross_provider_or_inject_cli_options(self):
        for kind, model in [('plan', 'claude-opus-5-5'), ('implement', 'gpt-6-astra'),
                            ('review', '--model'), ('validate', 'gpt-6-astra --flag')]:
            value = config(); value['models'][kind]['model'] = model
            with self.assertRaises(team.Blocked):
                team.validate_config(value)


if __name__ == '__main__':
    unittest.main()
