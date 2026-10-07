import json, subprocess, sys, tempfile, time, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import task_insight as ti


def write_events(path, events):
    path.write_text('\n'.join(json.dumps(e) for e in events) + '\n')


def make_task(d, request='r', status='RUNNING', **extra):
    ws = d / 'workspace'
    ws.mkdir()
    run = lambda *a: subprocess.run(['git', '-C', str(ws), '-c', 'user.name=t', '-c', 'user.email=t@t', *a], check=True, capture_output=True)
    run('init', '-q'); (ws / 'a.txt').write_text('1\n'); run('add', '.'); run('commit', '-qm', 'base')
    base = subprocess.run(['git', '-C', str(ws), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    (ws / 'a.txt').write_text('1\n2\n'); (ws / 'new.css').write_text('x\ny\n')
    state = {'task': 'a' * 32, 'status': status, 'phase': 'IMPLEMENT', 'cycle': 0, 'created_at': time.time() - 90,
             'request': request, 'repository': '/r', 'base_sha': base, 'config': {'max_cycles': 3, 'max_seconds': 7200, 'timeout': 900},
             'stage_runs': [{'stage': 'plan', 'cycle': 0, 'agent': 'atlas', 'requested_model': 'm', 'effort': 'e', 'started_at': 0, 'ended_at': 30},
                            {'stage': 'implement', 'cycle': 0, 'agent': 'argus', 'requested_model': 'c', 'effort': 'h', 'started_at': time.time() - 20}],
             'active': {'container': 'ai-team-' + 'a' * 32 + '-implement'},
             'plan': {'tasks': [{'id': 'T1', 'description': 'faz', 'acceptance_ids': ['AC1']}],
                      'acceptance_criteria': [{'id': 'AC1', 'description': 'ok'}]}}
    state.update(extra)
    return state


class InsightTest(unittest.TestCase):
    def test_usage_codex_and_claude(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            write_events(d / 'c.stdout', [{'type': 'turn.completed', 'usage': {'input_tokens': 10, 'output_tokens': 3}}])
            self.assertEqual((ti.usage(d / 'c.stdout')['in'], ti.usage(d / 'c.stdout')['out']), (10, 3))
            live = [{'type': 'assistant', 'message': {'id': 'm1', 'usage': {'input_tokens': 1, 'output_tokens': 2}}},
                    {'type': 'assistant', 'message': {'id': 'm1', 'usage': {'input_tokens': 1, 'output_tokens': 5}}}]
            write_events(d / 'l.stdout', live)  # same message id repeated: count once, latest wins
            self.assertEqual(ti.usage(d / 'l.stdout')['out'], 5)
            write_events(d / 'r.stdout', live + [{'type': 'result', 'total_cost_usd': 0.5, 'usage': {'input_tokens': 4, 'output_tokens': 9}}])
            self.assertEqual((ti.usage(d / 'r.stdout')['out'], ti.usage(d / 'r.stdout')['cost']), (9, 0.5))

    def test_describe_activity(self):
        self.assertIn('pwd', ti.describe({'type': 'item.started', 'item': {'type': 'command_execution', 'command': '/bin/bash -lc pwd'}}))
        edit = {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Edit', 'input': {'file_path': '/work/src/a.css'}}]}}
        self.assertEqual(ti.describe(edit), '✏️  editando src/a.css')
        self.assertIsNone(ti.describe({'type': 'user'}))

    def test_text_html_and_escaping(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            state = make_task(d, request='<script>alert(1)</script>')
            write_events(d / '0-implement.stdout', [{'type': 'assistant', 'message': {'id': 'm', 'content': [
                {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/work/AGENTS.md'}}]}}])
            names = [(n, s) for n, s, _ in ti.steps(state)]
            self.assertEqual(names[0][1], 'done'); self.assertEqual(names[1][1], 'running')
            files = {f[1]: f for f in ti.changes(d, state)}
            self.assertEqual(files['a.txt'][2:], (1, 0)); self.assertEqual(files['new.css'][2], 2)
            text = ti.render_text(d, state, idle=400)
            self.assertIn('lendo AGENTS.md', text); self.assertIn('possível travamento', text); self.assertIn('T1', text)
            page = ti.render_html(d, state)
            self.assertNotIn('<script>alert', page); self.assertIn('&lt;script&gt;', page)
            self.assertIn('+1', page)

    def test_text_fits_terminal_height(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            state = make_task(d)
            full = ti.render_text(d, state, idle=1, stats={'cpu': '1%', 'mem': '1MiB', 'net': '1kB / 1kB'}).splitlines()
            small = ti.render_text(d, state, idle=1, height=26).splitlines()
            self.assertLessEqual(len(small), 23)
            self.assertLess(len(small), len(full)); self.assertIn('ETAPAS', small[:14]); self.assertIn('SAÚDE', '\n'.join(small))
            self.assertIn('container: CPU 1%', '\n'.join(full))

    def test_prompt_block_feedback_and_collapsed_request(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            state = make_task(d, request='Pedido do usuario')
            (d / '0-implement.prompt').write_text('You are Argus. Read AGENTS.md first. Request: Pedido do usuario Previous validation/review feedback: []')
            (d / 'handoff-0-implement').mkdir(); (d / 'handoff-0-implement' / 'plan.json').write_text('{}')
            state['feedback'] = [{'findings': [{'severity': 'MEDIUM', 'status': 'OPEN', 'summary': 'falta build Pages'}]},
                                 {'tests': 'FAIL', 'output': 'a\nsh: tsc: Permission denied'}]
            text = ti.render_text(d, state, idle=1)
            self.assertIn('PROMPT em execução', text)
            self.assertIn('You are Argus. Read AGENTS.md first.', text)
            self.assertNotIn('Pedido do usuario Previous', text)
            self.assertIn('plan.json (2 B)', text)
            self.assertIn('MEDIUM: falta build Pages', text)
            self.assertIn('TESTES FALHARAM', text)
            self.assertIn('Prompts enviados', ti.render_html(d, state))
        self.assertIn('[Pedido: igual', ti.prompt_view('Do X. Original request: abc', 'abc')[0])
        self.assertEqual(ti.wrap('a b c d e f', 5, 2), ['a b c', 'd e f'])
        self.assertTrue(ti.wrap('a b c d e f', 3, 2)[-1].endswith('…'))

    def test_indicators_quota_eta_health_and_trend(self):
        self.assertEqual(ti.bar(0.5, 10), '▕█████░░░░░▏'); self.assertEqual(ti.bar(None, 4), '▕░░░░▏'); self.assertEqual(ti.bar(2, 4), '▕████▏')
        trend = ti.Trend(size=3)
        for n in (0, 5, 5, 20, 21):
            trend.push(n)
        self.assertEqual(trend.deltas, [0, 15, 1]); self.assertEqual(len(trend.line()), 3)
        with tempfile.TemporaryDirectory() as t:
            runs = Path(t); (runs / 'x').mkdir()
            event = {'type': 'rate_limit_event', 'rate_limit_info': {'status': 'allowed', 'unifiedWindows': {
                'five_hour': {'utilization': 0.31, 'resetsAt': 2_000_000_000}, 'seven_day': {'utilization': 0.38, 'resetsAt': 2_000_100_000}}}}
            (runs / 'x' / '0-implement.stdout').write_text('{"type":"assistant"}\n' + json.dumps(event) + '\n')
            quota = ti.quota_snapshot(runs)
            self.assertEqual((quota['five_hour'], quota['seven_day'], quota['status']), (0.31, 0.38, 'allowed'))
            self.assertIsNone(ti.quota_snapshot(runs / 'x' / 'nada'))
            # medians come from finished tasks and drive the ETA
            e0 = 1_000_000
            done = {'status': 'REVIEWED', 'stage_runs': [{'stage': 'plan', 'cycle': 0, 'started_at': e0, 'ended_at': e0 + 100},
                                                         {'stage': 'implement', 'cycle': 0, 'started_at': e0 + 100, 'ended_at': e0 + 700}],
                    'test_evidence': {'started_at': e0 + 700, 'ended_at': e0 + 710}}
            (runs / 'x' / 'state.json').write_text(json.dumps(done))
            medians = ti.stage_medians(runs)
            self.assertEqual((medians['plan'], medians['implement'], medians['tests']), (100, 600, 10))
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            state = make_task(d)
            write_events(d / '0-implement.stdout', [{'type': 'assistant', 'message': {'id': 'm1', 'usage': {'input_tokens': 1, 'cache_read_input_tokens': 5000},
                                                     'content': [{'type': 'tool_use', 'name': 'Read', 'input': {}}]}}])
            state['stage_runs'][-1]['max_turns'] = 60
            medians = {'plan': 100, 'implement': 600, 'tests': 10, 'validate': 300, 'review': 150}
            frac, eta = ti.progress(state, d, medians, time.time())
            self.assertTrue(0.2 <= frac < 0.5); self.assertGreater(eta, 400)
            self.assertIsNone(ti.progress(state, d, {}, time.time())[1])
            text = ti.render_text(d, state, idle=700, quota={'status': 'allowed', 'five_hour': 0.8, 'five_reset': 2_000_000_000,
                                  'seven_day': 0.1, 'seven_reset': None, 'age': 30}, medians=medians, trend=trend)
        for needle in ('● CRÍTICO', 'sem movimento há', 'cota Claude 5h em 80%', 'PROGRESSO', 'faltam ~', 'COTA CLAUDE', 'ETAPA ATUAL', 'turnos 1/60', 'contexto 5k', 'ritmo'):
            self.assertIn(needle, text)
        self.assertEqual(ti.health({'status': 'RUNNING', 'cycle': 0, 'config': {'max_cycles': 3}}, 1, None, 80, 10, 60), [])

    def test_exhausted_limits_are_parsed_and_surfaced(self):
        codex = "validate failed: You’ve hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Oct 5th, 2026 1:32 AM.; no implicit retry/model fallback"
        claude = "review failed: You've hit your session limit · resets 5pm (UTC); no implicit retry/model fallback"
        self.assertEqual(ti.parse_limit(codex), ('Codex', 'Oct 5th, 2026 1:32 AM'))
        self.assertEqual(ti.parse_limit(claude), ('Claude', '5pm (UTC)'))
        self.assertIsNone(ti.parse_limit('plan failed: invalid schema')); self.assertIsNone(ti.parse_limit(None))
        with tempfile.TemporaryDirectory() as t:
            runs = Path(t); (runs / 'a').mkdir()
            (runs / 'a' / 'state.json').write_text(json.dumps({'reason': codex}))
            notice = ti.limit_notice(runs)
            self.assertEqual((notice['provider'], notice['reset']), ('Codex', 'Oct 5th, 2026 1:32 AM'))
            self.assertIsNone(ti.limit_notice(runs, now=time.time() + 2 * 86400))  # stale after 24h
            d = Path(t) / 'task'; d.mkdir()
            state = make_task(d, status='FAILED', active=None, reason=codex)
            text = ti.render_text(d, state, limit=notice)
        self.assertIn('limite de uso do Codex esgotado; volta em Oct 5th, 2026 1:32 AM', text)
        self.assertIn('LIMITE     ⚠ Codex esgotado — volta em Oct 5th, 2026 1:32 AM', text)

    def test_failed_step_and_stall(self):
        with tempfile.TemporaryDirectory() as t:
            state = make_task(Path(t), status='FAILED', active=None, reason='x')
            self.assertEqual(dict((n, s) for n, s, _ in ti.steps(state))['implement'], 'failed')
        stall = ti.Stall()
        self.assertLess(stall.idle(1), 1); stall.since -= 100
        self.assertGreater(stall.idle(1), 99); self.assertLess(stall.idle(2), 1)


if __name__ == '__main__':
    unittest.main()
