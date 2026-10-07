#!/usr/bin/env python3
"""Verifica o grafo de dependências entre pacotes (ADR 004) em código e manifestos.

Documentação (.md) e dados de ownership podem citar outros pacotes; só contam como violação:
  1. caminhos para outro pacote (`packages/<outro>/` ou `../<outro>/`) em código, scripts e configs;
  2. dependências declaradas em package.json e pyproject.toml que nomeiem outro pacote.
Usa só a biblioteca padrão. Saída 0 = ok; 1 = violações.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = {".py", ".ts", ".js", ".cjs", ".mjs", ".sh", ".toml", ".yaml", ".yml", ".json"}
SKIP = {"node_modules", "dist", "build", ".git", "__pycache__", ".venv", ".pytest_cache", "fixtures", "artifacts", "validation"}


def violations(config: dict, root: Path = ROOT) -> list[str]:
    packages = config["packages"]
    found = []
    for name, spec in packages.items():
        allowed = {name, *spec["depends_on"]}
        others = [q for q in packages if q not in allowed]
        for file in (root / spec["path"]).rglob("*"):
            rel = file.relative_to(root)
            if not file.is_file() or file.suffix not in CODE or SKIP & set(file.relative_to(root / spec["path"]).parts):
                continue
            text = file.read_text(errors="ignore")
            for other in others:
                if re.search(rf"packages/{re.escape(other)}/|\.\./+{re.escape(other)}/", text):
                    found.append(f"{rel}: {name} referencia o caminho do pacote {other} (permitido: {sorted(allowed - {name}) or 'nenhum'})")
        found += manifest_violations(root / spec["path"], name, others, root)
    for name, spec in packages.items():
        if name in spec["depends_on"] or not set(spec["depends_on"]) <= set(packages):
            found.append(f"platform-packages.json: {name} tem dependência inválida")
    return found


def manifest_violations(path: Path, name: str, others: list[str], root: Path) -> list[str]:
    found = []
    package_json = path / "package.json"
    if package_json.is_file():
        data = json.loads(package_json.read_text())
        deps = {k for key in ("dependencies", "devDependencies", "peerDependencies") for k in data.get(key, {})}
        found += [f"{package_json.relative_to(root)}: dependência {d} aponta para o pacote {o}" for d in deps for o in others if d.endswith(f"product-platform-{o}")]
    pyprojects = [path / "pyproject.toml", *path.glob("packages/*/pyproject.toml")]
    for pyproject in pyprojects:
        if pyproject.is_file():
            for o in others:
                if re.search(rf'["\']product-platform-{re.escape(o)}[\s<>=!~\["\']', pyproject.read_text()):
                    found.append(f"{pyproject.relative_to(root)}: dependência aponta para o pacote {o}")
    return found


if __name__ == "__main__":
    problems = violations(json.loads((ROOT / "platform-packages.json").read_text()))
    for line in problems:
        print("VIOLAÇÃO " + line, file=sys.stderr)
    print("Fronteiras entre pacotes: " + ("VIOLADAS" if problems else "OK"))
    sys.exit(1 if problems else 0)
