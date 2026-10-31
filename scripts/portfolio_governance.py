#!/usr/bin/env python3
"""Read portfolio metadata; write only the canonical inventory issue."""
import json
import http.client
from pathlib import Path
from portal_live_catalog_audit import PORTAL_PATH, audit, decode_github_content, summarize
from portal_editorial_packet import editorial_packet, render_packet
import os
import subprocess
import urllib.request
from datetime import datetime, timezone

OWNER = os.environ.get("GH_OWNER", "leandroclf")
REPO = os.environ.get("GH_REPO", "product-platform")
MARKER = "<!-- portfolio-governance-inventory -->"
# Any user can open an issue containing MARKER in a public repository; only issues
# created by the workflow identity or by trusted repository members are canonical.
TRUSTED_ISSUE_AUTHORS = {"github-actions[bot]"}
TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}

def gh(*args, read_portfolio=False):
    env = os.environ.copy()
    if read_portfolio and env.get("PORTFOLIO_READ_TOKEN"):
        env["GH_TOKEN"] = env["PORTFOLIO_READ_TOKEN"]
    result = subprocess.run(["gh", "api", *args], check=True, text=True, capture_output=True, env=env)
    return json.loads(result.stdout)

def public_catalog():
    request = urllib.request.Request('https://api.github.com/' + PORTAL_PATH,
                                     headers={'Accept': 'application/vnd.github+json',
                                              'User-Agent': 'portfolio-governance'})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read(3_000_001)
    if len(data) > 3_000_000:
        raise ValueError('Portal response too large')
    catalog = decode_github_content(json.loads(data))
    if not isinstance(catalog, dict):
        raise ValueError('Portal catalog must be a JSON object')
    return catalog

def is_public(repo):
    """Only repositories explicitly reported as public may be published."""
    return (isinstance(repo, dict) and repo.get("private") is False
            and repo.get("visibility", "public") == "public")

def is_canonical_issue(issue):
    if not isinstance(issue, dict) or "pull_request" in issue:
        return False
    body = issue.get("body")
    if not isinstance(body, str) or MARKER not in body:
        return False
    login = str((issue.get("user") or {}).get("login") or "").lower()
    return (login in TRUSTED_ISSUE_AUTHORS or login == OWNER.lower()
            or issue.get("author_association") in TRUSTED_ASSOCIATIONS)

def inventory():
    repos = []
    page = 1
    while True:
        path = (f"user/repos?per_page=100&page={page}&affiliation=owner"
                if os.environ.get("PORTFOLIO_READ_TOKEN") else
                f"users/{OWNER}/repos?type=owner&per_page=100&page={page}")
        batch = gh(path, read_portfolio=True)
        if not isinstance(batch, list):
            raise ValueError("Invalid inventory response")
        repos.extend(r for r in batch if isinstance(r, dict)
                     and str((r.get("owner") or {}).get("login") or "").lower() == OWNER.lower())
        if len(batch) < 100:
            break
        page += 1
    return sorted(repos, key=lambda x: x["name"].lower())

def render(repos, portal_report=None, editorial_report=None, coverage="unverified"):
    repos = [r for r in repos if is_public(r)]
    active = [r for r in repos if not r.get("archived")]
    archived = [r for r in repos if r.get("archived")]
    lines = [
        MARKER, "# Inventário automatizado do portfólio",
        f"Gerado em {datetime.now(timezone.utc).isoformat()} (UTC).",
        f"Total visível: {len(repos)}; não arquivados: {len(active)}; arquivados: {len(archived)}.",
        f"Cobertura: {coverage}. Ausência na resposta não prova inexistência de repositório privado.",
        "",
        "| Repositório | Estado | Atualização | Descrição |",
        "|---|---|---|---|",
    ]
    for r in repos:
        desc = (r.get("description") or "Não informada").replace("|", "/").replace("\n", " ")[:140]
        lines.append(f"| [{r['name']}]({r['html_url']}) | {'Arquivado' if r.get('archived') else 'Ativo'} | {r.get('pushed_at') or '-'} | {desc} |")
    lines += ["", "## Cobertura do portal corporativo LF Soluções (leitura remota)"]
    lines.append(summarize(portal_report or {"state": "UNVERIFIED", "issues": ["Live catalog not checked"]}))
    lines += ["", "## Ações editoriais de inclusão no portal (sem publicação)"]
    lines.append(render_packet(editorial_report or {"status": "UNVERIFIED"}))
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
    try:
        registry = json.loads((Path(__file__).resolve().parents[1] / "packages/kit/contracts/portfolio-products.json").read_text(encoding="utf-8"))
        catalog = public_catalog()
        portal_report = audit(registry, catalog)
        editorial_report = editorial_packet(registry, catalog) if portal_report["state"] in ("CONSISTENT", "DRIFT") else {"status": "UNVERIFIED"}
    except (ValueError, OSError, http.client.HTTPException, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        portal_report = {"state": "UNVERIFIED", "issues": ["Não foi possível confirmar a versão remota do catálogo: " + type(exc).__name__]}
        editorial_report = {"status": "UNVERIFIED"}
    coverage = "public-only (dados privados omitidos)" if os.environ.get("PORTFOLIO_READ_TOKEN") else "public-only (privados não verificados)"
    body = render(repos, portal_report, editorial_report, coverage)
    issues = []
    for page in range(1, 11):
        batch = gh(f"repos/{OWNER}/{REPO}/issues?state=open&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("Invalid issue list response; refusing to write inventory")
        issues.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise ValueError("Issue pagination incomplete; refusing to create inventory")
    matches = [i for i in issues if is_canonical_issue(i)]
    if len(matches) > 1:
        raise ValueError("Multiple inventory issues; reconcile before updating")
    existing = matches[0] if matches else None
    if existing:
        number = existing["number"]
        subprocess.run(["gh", "api", "-X", "PATCH", f"repos/{OWNER}/{REPO}/issues/{number}", "--input", "-"], input=json.dumps({"body":body}), text=True, check=True)
        print(f"Updated inventory issue #{number}")
    else:
        subprocess.run(["gh", "api", "-X", "POST", f"repos/{OWNER}/{REPO}/issues", "--input", "-"], input=json.dumps({"title":"Portfolio inventory (automated)","body":body}), text=True, check=True)
        print("Created portfolio inventory issue")

if __name__ == "__main__":
    main()
