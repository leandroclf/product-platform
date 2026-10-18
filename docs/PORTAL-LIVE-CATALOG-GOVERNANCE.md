# Auditoria recorrente do catálogo LF Soluções

## O que é verificado

O job de governança existente `.github/workflows/portfolio-governance.yml` executa `scripts/portfolio_governance.py` em dias úteis (cron já existente). A auditoria de cobertura `scripts/portal_live_catalog_audit.py` consulta **somente leitura** o conteúdo de `data/product-catalog.json` na `main` do repositório `leandroclf/site-lf-solucoes`, via API GitHub e credencial que o workflow de governança já usa.

Compara IDs, quantidade de produtos, runtime, wave, slug, URL de detalhes e visibilidade de produto com o registro local em `packages/kit/contracts/portfolio-products.json`. Seu resultado é incluído no **issue de inventário já atualizado periodicamente** em `product-platform`. Não abre outro issue, não publica um produto, não modifica o site e não cria PR.

O estado `CONSISTENT` significa que os dados coincidiram **no momento da leitura da API**. Não implica que o build do GitHub Pages foi publicado ou que o site externo já exibe essas páginas. `DRIFT` indica divergência; `BLOCKED` indica dados inválidos; `UNVERIFIED` significa que a consulta remota falhou. Não interpretar `UNVERIFIED` como sucesso.

## Pré-requisitos e limites

- O workflow de governança **já exige** `PORTFOLIO_READ_TOKEN`. Se não estiver configurado ou não possuir leitura do repositório `site-lf-solucoes`, o job pode falhar ou o relatório ficará `UNVERIFIED`.
- O runner tem `gh` instalado como esperado pela rotina existente; o token não é registrado em log.
- A nova verificação só roda enquanto a rotina existente estiver habilitada e bem-sucedida.
- O programa não introduz credencial de escrita, alteração de workflow protegido, gatilho de push ou instalação de GitHub App.
- Há uma janela entre a criação de um produto na plataforma e sua publicação revisada no portal. O objetivo é tornar essa divergência rastreável; a issue #60 segue responsável pela abertura automática de PR editorial com credencial GitHub App de menor privilégio.

## Regressão offline

```bash
python3 scripts/test_portal_live_catalog_audit.py
python3 scripts/test_handoff_contract.py
```
