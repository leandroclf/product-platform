import json, sys, tempfile, time, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import local_team as lt


class ClaudeArrayOutputTest(unittest.TestCase):
    def test_verbose_json_array_is_kept_as_events(self):
        events = [{'type': 'system', 'subtype': 'init', 'session_id': 's', 'model': 'm', 'api_key': 'k'},
                 {'type': 'result', 'is_error': False, 'structured_output': {'status': 'COMPLETE'}}]
        state = {'config': {'max_seconds': 99, 'timeout': 9}, 'created_at': time.time()}
        with tempfile.TemporaryDirectory() as d:
            cmd = [sys.executable, '-c', 'import json;print(json.dumps(%r))' % events]
            _, out = lt.execute(Path(d), state, cmd, '0-implement')
            lines = [json.loads(x) for x in out.read_text().splitlines()]
        self.assertEqual(len(lines), 2)
        self.assertNotIn('api_key', lines[0])
        self.assertEqual(lines[1]['structured_output'], {'status': 'COMPLETE'})

    def test_stream_json_lines_are_slimmed_and_result_found(self):
        lines = [{'type': 'system', 'subtype': 'init', 'session_id': 's', 'model': 'm'},
                 {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'content': 'x' * 5000}]}},
                 {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'content': [{'type': 'text', 'text': 'y' * 5000}]}]}, 'tool_use_result': {'file': {'content': 'z' * 5000}}},
                 {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Write', 'input': {'file_path': 'a', 'content': 'w' * 5000}}]}},
                 {'type': 'result', 'is_error': False, 'structured_output': {'status': 'COMPLETE'}}]
        state = {'config': {'max_seconds': 99, 'timeout': 9}, 'created_at': time.time()}
        with tempfile.TemporaryDirectory() as d:
            script = 'import json\nfor e in %r: print(json.dumps(e))' % lines
            _, out = lt.execute(Path(d), state, [sys.executable, '-c', script], '0-implement')
            text = out.read_text()
            events = [json.loads(x) for x in text.splitlines()]
        self.assertLess(len(text), 2500)  # 4 x 5000 chars in, ~300 kept each
        self.assertEqual(events[-1]['structured_output'], {'status': 'COMPLETE'})

    def test_provider_error_text_is_surfaced(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'o'
            f.write_text(json.dumps({'type': 'assistant'}) + '\n' + json.dumps(
                {'type': 'result', 'is_error': True, 'result': "You've hit your session limit · resets 5pm (UTC)"}) + '\n')
            self.assertIn('session limit', lt.provider_error_text(f))
            self.assertTrue(lt.provider_failed(f))
            f.write_text('')
            self.assertEqual(lt.provider_error_text(f), '')


if __name__ == '__main__':
    unittest.main()
