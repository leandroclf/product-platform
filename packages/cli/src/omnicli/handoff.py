"""Extrai o handoff da proposta final: capacidades (REUSE/EXTEND/CREATE) e o envelope PlatformHandoff.

Os contratos (JSON Schema) pertencem ao product-platform-kit; aqui só se produz JSON compatível, e a
validação autoritativa é `packages/kit/scripts/validate-platform-handoff.py`. O fingerprint do registry,
o `proposal_id`, o repositório, as versões de regras e o perfil vêm do OmniCLI e do operador, nunca do
texto do modelo.
"""
from __future__ import annotations

import json
import re

DECISIONS = {"REUSE", "EXTEND", "CREATE"}
BLOCK = re.compile(r"```capability-handoff[ \t]*\n(.*?)```", re.DOTALL)
CAPABILITY_KEYS = {"name", "decision", "owner", "version", "reason"}


def extract_capability_handoff(markdown: str, registry_fingerprint: str) -> dict[str, object]:
    blocks = BLOCK.findall(markdown)
    if not blocks:
        raise ValueError("a proposta não contém o bloco ```capability-handoff")
    try:
        data = json.loads(blocks[-1])  # o último bloco prevalece sobre rascunhos de etapas anteriores
    except json.JSONDecodeError as exc:
        raise ValueError(f"bloco capability-handoff com JSON inválido: {exc}") from exc
    if not isinstance(data, dict) or set(data) - {"product", "capabilities"}:
        raise ValueError("capability-handoff aceita somente 'product' e 'capabilities'")
    product, capabilities = data.get("product"), data.get("capabilities")
    if not isinstance(product, str) or not product.strip():
        raise ValueError("capability-handoff exige 'product' não vazio")
    if not isinstance(capabilities, list) or not capabilities:
        raise ValueError("capability-handoff exige ao menos uma capacidade")
    names: set[str] = set()
    for item in capabilities:
        if not isinstance(item, dict) or set(item) - CAPABILITY_KEYS or not {"name", "decision", "owner"} <= set(item):
            raise ValueError("cada capacidade exige name, decision e owner (e opcionalmente version, reason)")
        if item["decision"] not in DECISIONS:
            raise ValueError(f"decision inválida para {item['name']!r}: use REUSE, EXTEND ou CREATE")
        if not all(isinstance(item[k], str) and item[k].strip() for k in ("name", "owner")):
            raise ValueError("name e owner devem ser textos não vazios")
        if any(item.get(k) is not None and not isinstance(item[k], str) for k in ("version", "reason")):
            raise ValueError("version e reason devem ser texto ou null")
        if item["name"] in names:
            raise ValueError(f"capacidade duplicada: {item['name']!r}")
        names.add(item["name"])
    return {"registry_fingerprint": registry_fingerprint, "product": product, "capabilities": capabilities}


ENGINEERING_BLOCK = re.compile(r"```engineering-handoff[ \t]*\n(.*?)```", re.DOTALL)
RISK_LEVELS = {"low", "medium", "high", "critical"}
EVIDENCE = {"tests", "build", "ci", "security", "benchmark"}
PROFILES = {"core", "backend", "frontend", "devops", "security"}
SHA1 = re.compile(r"[0-9a-f]{40}")


def _text_list(value: object, name: str, *, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum or not all(isinstance(i, str) and i.strip() for i in value):
        suffix = f" com ao menos {minimum}" if minimum else ""
        raise ValueError(f"{name} deve ser uma lista de textos não vazios{suffix}")
    return value


def extract_engineering_handoff(markdown: str) -> dict[str, object]:
    blocks = ENGINEERING_BLOCK.findall(markdown)
    if not blocks:
        raise ValueError("a proposta não contém o bloco ```engineering-handoff")
    try:
        data = json.loads(blocks[-1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"bloco engineering-handoff com JSON inválido: {exc}") from exc
    keys = {"objective", "scope", "acceptance", "risk", "evidence"}
    if not isinstance(data, dict) or set(data) != keys:
        raise ValueError("engineering-handoff exige exatamente: " + ", ".join(sorted(keys)))
    objective = data["objective"]
    if not isinstance(objective, str) or not objective.strip():
        raise ValueError("objective deve ser um texto não vazio")
    shapes = {"scope": "allowed_paths", "acceptance": "criteria", "risk": "level", "evidence": "required"}
    for key, inner in shapes.items():
        if not isinstance(data[key], dict) or set(data[key]) != {inner}:
            raise ValueError(f"{key} exige exatamente a chave {inner}")
    allowed = _text_list(data["scope"]["allowed_paths"], "scope.allowed_paths")
    criteria = _text_list(data["acceptance"]["criteria"], "acceptance.criteria", minimum=1)
    level = data["risk"]["level"]
    if level not in RISK_LEVELS:
        raise ValueError("risk.level deve ser low, medium, high ou critical")
    required = _text_list(data["evidence"]["required"], "evidence.required")
    if set(required) - EVIDENCE:
        raise ValueError("evidence.required aceita apenas: " + ", ".join(sorted(EVIDENCE)))
    return {"objective": objective, "scope": {"allowed_paths": allowed}, "acceptance": {"criteria": criteria},
            "risk": {"level": level}, "evidence": {"required": required}}


def validate_envelope_options(*, repository_url: str | None, base_ref: str, base_sha: str | None,
                              kit_ref: str | None, harness_ref: str | None, profile: str | None) -> None:
    missing = [n for n, v in (("--repository-url", repository_url), ("--kit-ref", kit_ref),
                              ("--harness-ref", harness_ref), ("--profile", profile)) if not v]
    if missing:
        raise ValueError("--envelope-out exige também: " + ", ".join(missing))
    if not base_ref.strip():
        raise ValueError("--base-ref não pode ser vazio")
    for name, value in (("--base-sha", base_sha), ("--kit-ref", kit_ref), ("--harness-ref", harness_ref)):
        if value and not SHA1.fullmatch(value):
            raise ValueError(f"{name} deve ser um SHA completo de 40 caracteres hexadecimais (sem tags nem branches)")
    if profile not in PROFILES:
        raise ValueError("--profile deve ser um de: " + ", ".join(sorted(PROFILES)))


def build_platform_handoff(markdown: str, registry_fingerprint: str, *, proposal_id: str, repository_url: str,
                           base_ref: str, base_sha: str | None, kit_ref: str, harness_ref: str,
                           profile: str) -> dict[str, object]:
    validate_envelope_options(repository_url=repository_url, base_ref=base_ref, base_sha=base_sha,
                              kit_ref=kit_ref, harness_ref=harness_ref, profile=profile)
    repository: dict[str, str] = {"url": repository_url, "base_ref": base_ref}
    if base_sha:
        repository["base_sha"] = base_sha
    return {
        "schema_version": "1.0",
        "proposal": {"proposal_id": proposal_id, "repository": repository, **extract_engineering_handoff(markdown)},
        "portfolio": extract_capability_handoff(markdown, registry_fingerprint),
        "rules_refs": {"kit": {"ref": kit_ref}, "harness": {"ref": harness_ref}, "profile": profile},
    }
