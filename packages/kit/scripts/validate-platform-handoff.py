#!/usr/bin/env python3
"""Valida um handoff da plataforma contra o contrato e o registry canônico (gate G1).

Uso:
  validate-platform-handoff.py --fingerprint [--registry FILE]
  validate-platform-handoff.py HANDOFF.json [--registry FILE]

Aceita o envelope PlatformHandoff (contracts/platform-handoff/v1.schema.json) ou o JSON simples de
capacidades gerado por `omnicli conceive --handoff-out`. Requer PyYAML e jsonschema.
Saída 0 = válido; 1 = violações listadas em stderr; 2 = uso/ambiente inválido.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "contracts/capability-registry.yaml"
PORTFOLIO = ROOT / "contracts/portfolio-products.json"
SCHEMA = ROOT / "contracts/platform-handoff/v1.schema.json"
SHARED = {"product-platform-kit", "product-platform-harness"}


def fingerprint(registry: Path) -> str:
    return hashlib.sha256(registry.read_bytes()).hexdigest()  # mesmo cálculo do omnicli e do ai-team


def violations(doc: dict, registry_path: Path) -> list[str]:
    import yaml
    from jsonschema import Draft202012Validator

    schema = json.loads(SCHEMA.read_text())
    if "portfolio" in doc:
        found = [f"schema: {'/'.join(map(str, e.path)) or '<raiz>'}: {e.message}" for e in Draft202012Validator(schema).iter_errors(doc)]
        portfolio = doc.get("portfolio") if isinstance(doc.get("portfolio"), dict) else {}
    else:
        validator = Draft202012Validator({**schema["$defs"]["portfolio"], "$defs": schema["$defs"]})
        found = [f"schema: {'/'.join(map(str, e.path)) or '<raiz>'}: {e.message}" for e in validator.iter_errors(doc)]
        portfolio = doc
    if found:
        return found
    registry = yaml.safe_load(registry_path.read_text())
    catalog = registry.get("capabilities") or {}
    portfolio_json = json.loads(PORTFOLIO.read_text())
    repos = set(portfolio_json["platform_repositories"]) | {p["repository"] for p in portfolio_json["products"]}
    product_repos = {p["repository"] for p in portfolio_json["products"]}
    errors = []
    if portfolio["registry_fingerprint"] != fingerprint(registry_path):
        errors.append("registry defasado: o fingerprint do handoff difere do sha256 do registry atual")
    product = portfolio["product"]
    seen = set()
    for item in portfolio["capabilities"]:
        name, decision, owner = item["name"], item["decision"], item["owner"]
        if name in seen:
            errors.append(f"{name}: capacidade duplicada no handoff")
        seen.add(name)
        known = catalog.get(name)
        if decision == "CREATE":
            if known is not None:
                errors.append(f"{name}: CREATE duplica capacidade registrada (dono {known.get('owner')}); use REUSE ou EXTEND")
            if owner not in repos:
                errors.append(f"{name}: CREATE exige dono explícito entre os repositórios do portfólio, recebeu {owner!r}")
            continue
        if known is None:
            errors.append(f"{name}: {decision} exige capacidade registrada; ela não existe no registry")
            continue
        owners = {known.get("owner"), known.get("implementation_owner")} - {None}
        if owner not in owners:
            errors.append(f"{name}: {decision} deve mirar o dono canônico {sorted(owners)}, recebeu {owner!r}")
        if product in product_repos and owner in product_repos and owner != product:
            errors.append(f"{name}: dependência produto->produto proibida ({product} -> {owner})")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("handoff", nargs="?")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--fingerprint", action="store_true", help="imprime o sha256 do registry")
    args = parser.parse_args(argv)
    try:
        if args.fingerprint:
            print(fingerprint(args.registry))
            return 0
        if not args.handoff:
            parser.error("informe o arquivo de handoff ou --fingerprint")
        found = violations(json.loads(Path(args.handoff).read_text()), args.registry)
    except ImportError as exc:
        print(f"dependência ausente ({exc.name}); instale PyYAML e jsonschema", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"entrada inválida: {exc}", file=sys.stderr)
        return 2
    for line in found:
        print("VIOLAÇÃO " + line, file=sys.stderr)
    if not found:
        print("Platform handoff: OK")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
