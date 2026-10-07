import json
import sys
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from omnicli.cli import app
from omnicli.handoff import extract_capability_handoff
from omnicli.models import OmniConfig, PipelineConfig, ProviderConfig, StageConfig
from omnicli.prompts import build_stage_prompt

FP = "a" * 64
BLOCK = (
    '```capability-handoff\n{"product": "meu-site", "capabilities": ['
    '{"name": "entitlements", "decision": "REUSE", "owner": "product-platform-harness", "version": null}]}\n```'
)


def test_extracts_last_block_and_takes_fingerprint_from_the_cli() -> None:
    draft = BLOCK.replace("REUSE", "CREATE")
    result = extract_capability_handoff(f"# Proposta\n{draft}\ntexto\n{BLOCK}\n", FP)
    assert result["registry_fingerprint"] == FP
    assert result["capabilities"][0]["decision"] == "REUSE"  # type: ignore[index]


@pytest.mark.parametrize(
    "text",
    [
        "sem bloco",
        "```capability-handoff\nnão é json\n```",
        '```capability-handoff\n{"product": "x", "capabilities": []}\n```',
        '```capability-handoff\n{"product": "x", "capabilities": '
        '[{"name": "a", "decision": "COPY", "owner": "o"}]}\n```',
        '```capability-handoff\n{"product": "x", "capabilities": [{"name": "a", "decision": "REUSE"}]}\n```',
        '```capability-handoff\n{"product": "x", "registry_fingerprint": "b", "capabilities": '
        '[{"name": "a", "decision": "REUSE", "owner": "o"}]}\n```',
        '```capability-handoff\n{"product": "x", "capabilities": ['
        '{"name": "a", "decision": "REUSE", "owner": "o"}, {"name": "a", "decision": "CREATE", "owner": "o"}]}\n```',
    ],
)
def test_invalid_blocks_are_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        extract_capability_handoff(text, FP)


def test_portfolio_prompt_asks_for_the_handoff_block() -> None:
    stage = StageConfig(name="m", provider="p", role="R", instruction="I")
    assert "capability-handoff" in build_stage_prompt(stage, "ideia", "", 1, 1, portfolio_context="registry")
    assert "capability-handoff" not in build_stage_prompt(stage, "ideia", "", 1, 1)


def _config(tmp_path: Path, markdown: str) -> Path:
    script = f"print({markdown!r})"
    config = OmniConfig(
        pipeline=PipelineConfig(stages=[StageConfig(name="master", provider="py", role="R", instruction="I")]),
        providers={"py": ProviderConfig(command=sys.executable, args=["-c", script, "{prompt}"])},
    )
    path = tmp_path / "omnicli.yaml"
    path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    return path


def _conceive(tmp_path: Path, markdown: str, *extra: str):
    registry = tmp_path / "registry.yaml"
    registry.write_text("capabilities: {}\n", encoding="utf-8")
    out = tmp_path / "handoff.json"
    result = CliRunner().invoke(app, [
        "conceive", "ideia", "--config", str(_config(tmp_path, markdown)), "--workspace", str(tmp_path / "ws"),
        "--output", str(tmp_path / "proposta.md"), "--skip-latest-check",
        "--portfolio-context", str(registry), "--handoff-out", str(out), *extra,
    ])
    return result, out, registry


def test_conceive_writes_handoff_with_registry_fingerprint(tmp_path: Path) -> None:
    result, out, registry = _conceive(tmp_path, "# Proposta\n" + BLOCK)
    assert result.exit_code == 0, result.output
    data = json.loads(out.read_text(encoding="utf-8"))
    import hashlib

    assert data["registry_fingerprint"] == hashlib.sha256(registry.read_bytes()).hexdigest()
    assert data["product"] == "meu-site"


def test_conceive_keeps_proposal_but_fails_when_block_is_missing(tmp_path: Path) -> None:
    result, out, _ = _conceive(tmp_path, "# Proposta sem bloco")
    assert result.exit_code == 1
    assert (tmp_path / "proposta.md").exists() and not out.exists()


def test_handoff_out_requires_portfolio_context(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["conceive", "ideia", "--handoff-out", str(tmp_path / "h.json")])
    assert result.exit_code == 1
