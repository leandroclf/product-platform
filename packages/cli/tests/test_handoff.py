import json
import sys
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from omnicli.cli import app
from omnicli.handoff import (
    build_platform_handoff,
    extract_capability_handoff,
    extract_engineering_handoff,
    validate_envelope_options,
)
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


ENGINEERING = (
    '```engineering-handoff\n{"objective": "Exportar viagens", "scope": {"allowed_paths": ["src/", "docs/"]}, '
    '"acceptance": {"criteria": ["Exporta CSV"]}, "risk": {"level": "medium"}, '
    '"evidence": {"required": ["tests", "ci"]}}\n```'
)
SHA = "b" * 40
OPTIONS = {"repository_url": "https://github.com/leandroclf/vehicle-tracking.git", "base_ref": "main",
           "base_sha": "c" * 40, "kit_ref": SHA, "harness_ref": "d" * 40, "profile": "backend"}


def test_envelope_combines_proposal_capabilities_and_rules_without_model_controlled_identity() -> None:
    envelope = build_platform_handoff(BLOCK + "\n" + ENGINEERING, FP, proposal_id="run-1", **OPTIONS)  # type: ignore[arg-type]
    assert envelope["schema_version"] == "1.0"
    assert envelope["proposal"]["proposal_id"] == "run-1"  # type: ignore[index]
    assert envelope["proposal"]["repository"] == {  # type: ignore[index]
        "url": OPTIONS["repository_url"], "base_ref": "main", "base_sha": "c" * 40}
    assert envelope["portfolio"]["registry_fingerprint"] == FP  # type: ignore[index]
    assert envelope["rules_refs"] == {"kit": {"ref": SHA}, "harness": {"ref": "d" * 40}, "profile": "backend"}


@pytest.mark.parametrize(
    "text",
    [
        "sem bloco",
        "```engineering-handoff\nnão é json\n```",
        '```engineering-handoff\n{"objective": "x"}\n```',
        ENGINEERING.replace('"medium"', '"urgent"'),
        ENGINEERING.replace('"tests", "ci"', '"tests", "magic"'),
        ENGINEERING.replace('["Exporta CSV"]', "[]"),
        ENGINEERING.replace('"objective": "Exportar viagens"', '"objective": "x", "extra": 1'),
        ENGINEERING.replace('"allowed_paths"', '"paths"'),
    ],
)
def test_invalid_engineering_blocks_are_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        extract_engineering_handoff(text)


@pytest.mark.parametrize(
    "override",
    [{"kit_ref": "main"}, {"harness_ref": "v0.2.1"}, {"base_sha": "abc"}, {"profile": "fullstack"},
     {"repository_url": None}, {"base_ref": " "}],
)
def test_envelope_options_reject_floating_refs_and_unknown_profiles(override: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        validate_envelope_options(**{**OPTIONS, **override})  # type: ignore[arg-type]


def test_conceive_writes_the_envelope_next_to_the_capability_handoff(tmp_path: Path) -> None:
    result, out, registry = _conceive(
        tmp_path, "# Proposta\n" + BLOCK + "\n" + ENGINEERING,
        "--envelope-out", str(tmp_path / "envelope.json"), "--repository-url", str(OPTIONS["repository_url"]),
        "--kit-ref", SHA, "--harness-ref", "d" * 40, "--profile", "backend")
    assert result.exit_code == 0, result.output
    envelope = json.loads((tmp_path / "envelope.json").read_text(encoding="utf-8"))
    assert envelope["portfolio"] == json.loads(out.read_text(encoding="utf-8"))
    assert envelope["proposal"]["proposal_id"]  # run_id do OmniCLI


def test_envelope_options_are_checked_before_any_provider_runs(tmp_path: Path) -> None:
    result, _, _ = _conceive(tmp_path, "# Proposta\n" + BLOCK, "--envelope-out", str(tmp_path / "e.json"))
    assert result.exit_code == 1
    assert not (tmp_path / "ws").exists()  # nenhuma execução foi iniciada


def test_missing_engineering_block_keeps_the_proposal_but_fails(tmp_path: Path) -> None:
    result, _, _ = _conceive(
        tmp_path, "# Proposta\n" + BLOCK, "--envelope-out", str(tmp_path / "e.json"),
        "--repository-url", "https://x/y.git", "--kit-ref", SHA, "--harness-ref", SHA, "--profile", "core")
    assert result.exit_code == 1
    assert (tmp_path / "proposta.md").exists() and not (tmp_path / "e.json").exists()
