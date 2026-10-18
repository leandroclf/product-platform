import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import local_team as team
from scripts import update_provider_clis as updater


class RuntimeFreezeTests(unittest.TestCase):
    def test_run_inspects_and_saves_the_same_immutable_provider_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            frozen = "sha256:" + "b" * 64
            configuration = {
                "version": 2, "repository": str(target),
                "provider_image": "ai-eng-provider-cli:local",
                "test_image": "offline-tests:local",
                "checks": ["python -m unittest"],
                "timeout": 30, "max_cycles": 2, "max_seconds": 300,
                "models": json.loads(json.dumps(team.DEFAULT_MODELS)),
            }
            versions = {"codex": "1.2.3", "claude": "2.3.4"}
            def image_lookup(image):
                return frozen if image == "ai-eng-provider-cli:local" else "sha256:" + "c" * 64
            with patch.dict("os.environ", {"XDG_STATE_HOME": str(Path(tmp) / "state")}), \
                 patch.object(team, "target", return_value=target), \
                 patch.object(team, "clean"), \
                 patch.object(team, "image_present", side_effect=image_lookup) as images, \
                 patch.object(team, "read", return_value=configuration), \
                 patch.object(team, "require_valid_models"), \
                 patch.object(team, "warn_quota"), \
                 patch.object(team, "platform_inputs", return_value=None), \
                 patch.object(team, "freeze_platform", return_value=None), \
                 patch.object(team, "start", return_value=0) as started, \
                 patch.object(team, "git", side_effect=lambda *a: "a" * 40 if a[1] == "rev-parse" else "main" if a[1] == "branch" else "git@github.com:owner/repo.git"), \
                 patch.object(updater, "latest", side_effect=lambda name: versions[name]), \
                 patch.object(updater, "inspect_versions", return_value=versions) as checked:
                self.assertEqual(team.main(["run", "Change a fixture"]), 0)
                checked.assert_called_once_with(frozen)
                self.assertEqual(images.call_count, 2)
                task_path = started.call_args.args[0]
                state = json.loads((task_path / "state.json").read_text())
                self.assertEqual(state["config"]["provider_image"], frozen)
                self.assertEqual(state["config"]["test_image"], "sha256:" + "c" * 64)

    def test_stale_frozen_image_fails_without_creating_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            configuration = {
                "version": 2, "repository": str(target),
                "provider_image": "provider:local", "test_image": "tests:local",
                "checks": ["true"], "timeout": 30, "max_cycles": 2,
                "max_seconds": 300, "models": json.loads(json.dumps(team.DEFAULT_MODELS)),
            }
            with patch.dict("os.environ", {"XDG_STATE_HOME": str(Path(tmp) / "state")}), \
                 patch.object(team, "target", return_value=target), \
                 patch.object(team, "clean"), \
                 patch.object(team, "image_present", return_value="sha256:" + "a" * 64), \
                 patch.object(team, "read", return_value=configuration), \
                 patch.object(updater, "latest", return_value="9.9.9"), \
                 patch.object(updater, "inspect_versions", return_value={"codex": "1.0.0", "claude": "1.0.0"}), \
                 patch.object(team, "start") as started:
                with self.assertRaisesRegex(team.Blocked, "not the current stable"):
                    team.main(["run", "Change a fixture"])
                started.assert_not_called()


if __name__ == "__main__":
    unittest.main()
