import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import update_provider_clis as updater


class CliUpdaterTests(unittest.TestCase):
    def test_stable_registry_only(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n): return b'{"name":"@openai/codex","version":"1.2.3"}'
        with patch.object(updater.urllib.request, "urlopen", return_value=Response()) as fetch:
            self.assertEqual(updater.latest("codex"), "1.2.3")
            self.assertIn("registry.npmjs.org", fetch.call_args.args[0].full_url)

    def test_prerelease_rejected(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n): return b'{"name":"@anthropic-ai/claude-code","version":"1.2.3-beta.2"}'
        with patch.object(updater.urllib.request, "urlopen", return_value=Response()):
            with self.assertRaises(ValueError):
                updater.latest("claude")

    def test_fingerprint_requires_exact_stable_versions(self):
        versions = {"codex": "1.2.3", "claude": "2.3.4"}
        digest = hashlib.sha256(json.dumps(versions, sort_keys=True).encode()).hexdigest()
        plan = updater.plan(versions, versions)
        self.assertEqual(plan["approval_fingerprint"], digest)
        self.assertFalse(any(plan["update_needed"].values()))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "approval hash"):
                updater.promote(Path(tmp), versions, "bad-hash", Path(tmp))

    def test_active_task_blocks_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            folder = home / "runs" / ("a" * 32)
            folder.mkdir(parents=True)
            (folder / "state.json").write_text('{"status":"RUNNING"}')
            self.assertEqual(updater.active_tasks(home), ["a" * 32])
            versions = {"codex": "1.2.3", "claude": "2.3.4"}
            fingerprint = updater.plan({}, versions)["approval_fingerprint"]
            with patch.object(updater, "run") as command:
                with self.assertRaisesRegex(ValueError, "Active"):
                    updater.promote(home, versions, fingerprint, home)
                command.assert_not_called()

    def test_candidate_does_not_promote_when_flags_missing(self):
        versions = {"codex": "1.2.3", "claude": "2.3.4"}
        token = updater.plan({}, versions)["approval_fingerprint"]
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(updater, "run") as command, \
             patch.object(updater, "inspect_versions", side_effect=ValueError("missing flag")):
            with self.assertRaises(ValueError):
                updater.promote(Path(tmp), versions, token, Path(tmp))
            self.assertTrue(any("build" in call.args[0] for call in command.call_args_list))
            self.assertFalse(any("tag" in call.args[0] for call in command.call_args_list))

    def test_promotion_only_after_both_checks(self):
        versions = {"codex": "1.2.3", "claude": "2.3.4"}
        token = updater.plan({}, versions)["approval_fingerprint"]
        def fake_run(argv, **kwargs):
            if argv[:3] == ["docker", "image", "inspect"]:
                return subprocess.CompletedProcess(argv, 0, "sha256:" + "a" * 64, "")
            return subprocess.CompletedProcess(argv, 0, "", "")
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(updater, "run", side_effect=fake_run) as command, \
             patch.object(updater, "inspect_versions", return_value=versions):
            result = updater.promote(Path(tmp), versions, token, Path(tmp))
            self.assertTrue(result["promoted"])
            commands = [call.args[0] for call in command.call_args_list]
            self.assertTrue(any("local_stage_isolation_smoke.py" in " ".join(cmd) for cmd in commands))
            self.assertEqual(commands[-1][0:2], ["docker", "tag"])


if __name__ == "__main__":
    unittest.main()
