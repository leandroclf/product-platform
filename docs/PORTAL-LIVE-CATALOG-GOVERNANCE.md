# Auditoria recorrente do catálogo LF Soluções

## O que é verificado

O job de governança existente `.github/workflows/portfolio-governance.yml` executa `scripts/portfolio_governance.py` em dias úteis (cron já existente). A auditoria de cobertura `scripts/portal_live_catalog_audit.py` consulta **somente leitura** o conteúdo de `data/product-catalog.json` na `main` do repositório público `leandroclf/site-lf-solucoes`, via API GitHub **sem credenciais** (requisição anônima, timeout de 15 s e resposta limitada a 3 MB). Nenhum token do workflow é enviado nessa consulta.

Compara IDs, quantidade de produtos, runtime, wave, slug, URL de detalhes e visibilidade de produto com o registro local em `packages/kit/contracts/portfolio-products.json`. Seu resultado é incluído no **issue de inventário já atualizado periodicamente** em `product-platform`. Não abre outro issue, não publica um produto, não modifica o site e não cria PR.

O estado `CONSISTENT` significa que os dados coincidiram **no momento da leitura da API**. Não implica que o build do GitHub Pages foi publicado ou que o site externo já exibe essas páginas. `DRIFT` indica divergência; `BLOCKED` indica dados inválidos; `UNVERIFIED` significa que a consulta remota falhou (HTTP, transporte, timeout, tamanho, decodificação ou conteúdo que não é um objeto JSON); o relatório registra apenas o tipo do erro, nunca a mensagem ou o conteúdo recebido. Não interpretar `UNVERIFIED` como sucesso. Nenhum estado, inclusive `CONSISTENT`, é prova de deploy.

## Pré-requisitos e limites

- A consulta ao catálogo **não depende** de `PORTFOLIO_READ_TOKEN` nem de outra credencial. Limites de taxa da API anônima ou indisponibilidade resultam em `UNVERIFIED`, sem interromper o inventário público.
- O runner tem `gh` instalado como esperado pela rotina existente, usado apenas para o inventário e a issue; tokens não são registrados em log.
- A nova verificação só roda enquanto a rotina existente estiver habilitada e bem-sucedida.
- O programa não introduz credencial de escrita, alteração de workflow protegido, gatilho de push ou instalação de GitHub App.
- Há uma janela entre a criação de um produto na plataforma e sua publicação revisada no portal. O objetivo é tornar essa divergência rastreável; a issue #60 segue responsável pela abertura automática de PR editorial com credencial GitHub App de menor privilégio.

## Regressão offline

```bash
python3 scripts/test_portal_live_catalog_audit.py
python3 scripts/test_handoff_contract.py
python3 -m unittest discover -s tests -p test_portfolio_governance.py -v
```
