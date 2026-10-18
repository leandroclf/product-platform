#!/usr/bin/env python3
"""Conservative GitHub portfolio inventory; never modifies repositories."""
import json
import os
import subprocess
from datetime import datetime, timezone

OWNER = os.environ.get("GH_OWNER", "leandroclf")
REPO = os.environ.get("GH_REPO", "product-platform")
MARKER = "<!-- portfolio-governance-inventory -->"

def gh(*args):
    result = subprocess.run(["gh", "api", *args], check=True, text=True, capture_output=True)
    return json.loads(result.stdout)

def inventory():
    repos = []
    page = 1
    while True:
        batch = gh(f"user/repos?per_page=100&page={page}&affiliation=owner")
        repos.extend(r for r in batch if r.get("owner", {}).get("login", "").lower() == OWNER.lower())
        if len(batch) < 100:
            break
        page += 1
    return sorted(repos, key=lambda x: x["name"].lower())

def render(repos):
    active = [r for r in repos if not r.get("archived")]
    archived = [r for r in repos if r.get("archived")]
    lines = [
        MARKER, "# Inventário automatizado do portfólio",
        f"Gerado em {datetime.now(timezone.utc).isoformat()} (UTC).",
        f"Total visível: {len(repos)}; não arquivados: {len(active)}; arquivados: {len(archived)}.",
        "",
        "| Repositório | Estado | Atualização | Descrição |",
        "|---|---|---|---|",
    ]
    for r in repos:
        desc = (r.get("description") or "Não informada").replace("|", "/").replace("\n", " ")[:140]
        lines.append(f"| [{r['name']}]({r['html_url']}) | {'Arquivado' if r.get('archived') else 'Ativo'} | {r.get('pushed_at') or '-'} | {desc} |")
    lines += [
        "", "## Próximas verificações (requerem evidências)",
        "- Confirmar proprietário, domínio, clientes e capacidade reutilizável por repositório.",
        "- Inspecionar manifests, workflows e contratos antes de declarar duplicações.",
        "- Propor ADRs e PRs antes de qualquer consolidação; nunca excluir automaticamente.",
        "- Não inferir ausência de atividade apenas por pushed_at.",
    ]
    return "\n".join(lines)

def main():
    repos = inventory()
    body = render(repos)
    issues = gh(f"repos/{OWNER}/{REPO}/issues?state=open&per_page=100")
    existing = next((i for i in issues if "pull_request" not in i and MARKER in (i.get("body") or "")), None)
    if existing:
        number = existing["number"]
        subprocess.run(["gh", "api", "-X", "PATCH", f"repos/{OWNER}/{REPO}/issues/{number}", "-f", f"body={body}"], check=True)
        print(f"Updated inventory issue #{number}")
    else:
        subprocess.run(["gh", "api", "-X", "POST", f"repos/{OWNER}/{REPO}/issues", "-f", "title=Portfolio inventory (automated)", "-f", f"body={body}"], check=True)
        print("Created portfolio inventory issue")

if __name__ == "__main__":
    main()
