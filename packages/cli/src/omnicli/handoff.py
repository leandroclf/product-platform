"""Extrai a resolução de capacidades da proposta final como PortfolioCapabilityHandoff.

O contrato (JSON Schema) pertence a product-platform-engineering-team; aqui só se produz um
JSON compatível. O fingerprint do registry vem do OmniCLI, nunca do texto do modelo.
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
