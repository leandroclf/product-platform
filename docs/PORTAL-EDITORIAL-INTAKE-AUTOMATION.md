# Portal LF — abertura de PR editorial para novos produtos

PR base do portal: site-lf-solucoes #15 (merged). O contrato de produtos é `packages/kit/contracts/portfolio-products.json`. O site principal permanece `leandroclf/site-lf-solucoes`.

## Operação segura do proponente

```bash
# Compare o registry com uma cópia atual de data/product-catalog.json do portal.
python3 scripts/propose_portal_intake.py --catalog /caminho/portal/data/product-catalog.json

# Somente depois de revisar a lista e configurar uma credencial restrita:
PORTAL_PR_TOKEN=<token-do-github-app> python3 scripts/propose_portal_intake.py \
  --catalog /caminho/portal/data/product-catalog.json --apply
```

O proponente cria um **draft PR com arquivos de intake não públicos** sob `data/portal-intake/`, nunca altera o catálogo visível sem revisão. A branch é derivada do SHA da `main` do portal e é rejeitada se já existir. A execução `--apply` confirma via API autenticada que a cópia do catálogo corresponde à versão publicada em `main`; prepara os blobs, a tree e um commit único antes de criar a referência da branch, reduzindo branches remotas incompletas em caso de falha intermediária. Não usa token para consultar ou alterar segredos, workflows ou outros repositórios.

**Permissões mínimas para GitHub App:** repositório `site-lf-solucoes` exclusivamente; Contents `read/write`, Pull requests `read/write`. A plataforma usa a credencial como variável `PORTAL_PR_TOKEN` em runner protegido; nunca inserir segredo em Git, `AGENTS.md`, logs ou mensagem de PR.

## Revisão obrigatória

Ao receber intake de novo produto, equipe editorial preenche título, categoria, descrição, funcionalidades e URL pública verificada; move o conteúdo aprovado para `data/product-catalog.json`, atualiza snapshot do registry, gera HTML, valida CI e revisa visualmente. Somente o merge da publicação normal do portal aciona GitHub Pages.

**Limitações atuais:** este script não está integrado a um evento de registro/cross-repo e não dispõe de credencial GitHub App instalada ou configurada. Ele permite planejamento read-only e abertura autenticada manual de draft PR. A automação disparada por alterações do registry será implementada em estágio separado, após autorização do GitHub App e revisão das regras de segurança. Uma execução sem --apply jamais cria PR.

## Regras de falha segura

- Não cria PR sem token explícito.
- Não aceita identidades arbitrárias como paths.
- Não substitui branch existente.
- Não considera registro de produto sinônimo de publicação comercial.
- Não cria URL pública fictícia ou assume produto pronto.
- Não implanta aplicações, Worker ou GitHub Pages.
