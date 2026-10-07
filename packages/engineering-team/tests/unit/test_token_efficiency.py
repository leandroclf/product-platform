import json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import local_team as lt
import task_insight as ti

CONFIG = {'provider_image': 'img', 'models': {k: {'model': 'm', 'effort': 'e'} for k in ('plan', 'implement', 'validate', 'review')}}


class TokenEfficiencyTest(unittest.TestCase):
    def test_rules_are_inserted_once_before_the_request(self):
        for marker in ('Original request: ', 'Request: '):
            out = lt.with_efficiency(f'Do X. {marker}pedido')
            self.assertLess(out.index('Token discipline'), out.index(marker))
            self.assertEqual(lt.with_efficiency(out), out)
        self.assertEqual(lt.with_efficiency('sem pedido'), 'sem pedido')

    def test_rtk_is_mounted_read_only_for_codex_only_with_telemetry_off(self):
        with tempfile.TemporaryDirectory() as t:
            fake = Path(t) / 'rtk'; fake.write_bytes(b'binary')
            with mock.patch.object(lt, 'rtk_binary', return_value=fake):
                mounts, fingerprint = lt.codex_tooling()
                self.assertIn(f'{fake}:/usr/local/bin/rtk:ro', mounts)
                self.assertTrue(any(m.endswith('/home/agent/.codex/AGENTS.md:ro') for m in mounts))
                self.assertIn('RTK_TELEMETRY_DISABLED=1', mounts)
                self.assertEqual(len(fingerprint), 16)
                codex = lt.provider_command('plan', 'n', CONFIG, Path(t), Path(t), 'p')
                claude = lt.provider_command('implement', 'n', CONFIG, Path(t), Path(t), 'p')
            self.assertTrue(any(x.endswith(':/usr/local/bin/rtk:ro') for x in codex))
            self.assertFalse(any('rtk' in x for x in claude))  # Claude stages have no shell
            with mock.patch.object(lt, 'rtk_binary', return_value=None):
                self.assertEqual(lt.codex_tooling(), ([], None))

    def test_tool_profile_separates_identical_rereads_from_windows(self):
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / '0-validate.stdout'
            cmd = lambda c, out: {'type': 'item.completed', 'item': {'type': 'command_execution', 'command': f"/bin/bash -lc '{c}'", 'aggregated_output': out}}
            read = lambda f, off: {'type': 'assistant', 'message': {'id': f'{f}{off}', 'content': [{'type': 'tool_use', 'name': 'Read', 'input': {'file_path': f, 'offset': off, 'limit': 100}}]}}
            rows = [cmd('cat /work/a.css', 'x' * 3000), cmd('cat /work/a.css', 'x' * 3000),
                    cmd('sed -n 1,50p /work/p.patch', 'y'), cmd('sed -n 51,100p /work/p.patch', 'y'), cmd('sed -n 101,150p /work/p.patch', 'y'),
                    cmd('rtk git status', 'z' * 10),
                    read('/work/b.astro', 0), read('/work/b.astro', 100), read('/work/b.astro', 200), read('/work/c.css', 0), read('/work/c.css', 0),
                    {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'content': 'k' * 300 + '… [9000 chars]'}]}}]
            log.write_text('\n'.join(json.dumps(r) for r in rows))
            prof = ti.tool_profile(log)
        self.assertEqual(prof['top'][0], ('cat', 6000))
        identical = dict(prof['identical'])
        self.assertEqual(identical["cat /work/a.css"], 2)       # same command twice: real waste
        self.assertEqual(identical['/work/c.css@0:100'], 2)     # same Read twice: real waste
        self.assertNotIn('/work/b.astro@0:100', identical)      # different windows: not waste
        windows = dict(prof['windows'])
        self.assertEqual(windows['/work/p.patch'], 3); self.assertEqual(windows['/work/b.astro'], 3)
        self.assertGreaterEqual(prof['bytes'], 6000 + 9000)

    def test_session_profile_and_recommendations(self):
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / '0-implement.stdout'
            usage = lambda i: {'input_tokens': 1, 'cache_read_input_tokens': i, 'cache_creation_input_tokens': 10}
            rows = [{'type': 'assistant', 'message': {'id': f'm{i}', 'usage': usage(i * 1000), 'content': [{'type': 'tool_use', 'name': 'Read', 'input': {}}] * (2 if i % 2 else 1)}} for i in range(1, 5)]
            rows += [{'type': 'system', 'subtype': 'thinking_tokens', 'estimated_tokens_delta': 500}] * 4
            log.write_text('\n'.join(json.dumps(r) for r in rows))
            sess = ti.session_profile(log)
        self.assertEqual((sess['turns'], sess['thinking'], sess['parallel_pct']), (4, 2000, 50))
        self.assertEqual(sess['ctx_last'], 4000 + 11); self.assertEqual(sess['ctx_peak'], sess['ctx_last'])
        base = {'cycle': 0, 'stage': 'implement', 'provider': 'claude', 'turns': 27, 'commands': 0, 'ctx_peak': 150_000, 'ctx_sum': 2_500_000,
                'out': 75_000, 'thinking': 40_000, 'identical': [('/w/a.css@0:1', 3)], 'max_turns': 30, 'cache_pct': 94, 'in': 2_500_000}
        text = ' '.join(ti.recommendations([base]))
        for needle in ('sessão longa', '53%', 'idêntica repetida 3', '27/30 turnos'):
            self.assertIn(needle, text)
        self.assertEqual(ti.recommendations([{**base, 'turns': 5, 'ctx_sum': 1, 'thinking': 0, 'identical': [], 'max_turns': 60}]), [])

    def test_usage_reports_cache_and_efficiency_view(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / '0-plan.stdout').write_text(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 5}}) + '\n')
            (d / '0-implement.stdout').write_text(json.dumps({'type': 'result', 'total_cost_usd': 1.0, 'usage': {
                'input_tokens': 1, 'cache_read_input_tokens': 90, 'cache_creation_input_tokens': 9, 'output_tokens': 7}}) + '\n')
            self.assertEqual(ti.usage(d / '0-plan.stdout')['cached'], 80)
            state = {'task': 'a' * 32, 'status': 'REVIEWED', 'stage_runs': [
                {'stage': 'plan', 'cycle': 0, 'agent': 'atlas', 'provider': 'codex', 'tools': {'rtk': 'abc123'}, 'started_at': 0, 'ended_at': 1},
                {'stage': 'implement', 'cycle': 0, 'agent': 'argus', 'provider': 'claude', 'tools': {}, 'started_at': 0, 'ended_at': 1}]}
            with mock.patch.object(ti, 'host_tools', return_value={'rtk': 'rtk 0.49.0', 'headroom': None}):
                text = ti.render_efficiency(d, state)
        self.assertIn('80%', text); self.assertIn('90%', text)
        self.assertIn('aplicado (abc123)', text); self.assertIn('n/a (sem shell)', text)
        self.assertIn('headroom: não instalado', text)


if __name__ == '__main__':
    unittest.main()
