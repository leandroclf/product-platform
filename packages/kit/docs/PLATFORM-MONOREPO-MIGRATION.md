# Plano de migração para o repositório da plataforma

Decisão: `docs/adr/004-platform-monorepo.md`. Este plano não move nada por si só; cada fase exige confirmação.

## Layout proposto (a confirmar)

```
<repositório-da-plataforma>/
  packages/
    contracts/          contratos, registry, políticas, skills, perfis (hoje o kit)
    harness/            runtime TypeScript e Python
    cli/                geração de propostas e handoff
    engineering-team/   ai-team
  docs/                 fluxo da plataforma, ADRs
  .github/workflows/    um workflow por pacote, com filtro de caminho
  CODEOWNERS
```

## Precondições de segurança (antes de qualquer push)

- **Visibilidade**: cumprida em 2026-10-07. O `leandroclf/product-platform` estava público e vazio e foi tornado PRIVADO a pedido do dono, igual a kit, harness, cli, engineering-team e vehicle-tracking. Nenhum conteúdo foi enviado. Qualquer mudança futura para público exige confirmação explícita e a varredura abaixo concluída.
- **Varredura de conteúdo**: antes de importar, revisar o que os históricos carregam além do código: artefatos de benchmark e execuções gravadas (`product-platform-cli/artifacts/benchmark`, `product-platform-engineering-team/validation/runs`), caminhos locais, logs de provedores e qualquer credencial. Decidir caso a caso o que entra, é filtrado do histórico ou fica de fora.

## Fases

**Fase 0: pré-requisitos, nos repositórios atuais (reversível, sem mover código)**
- Fonte única de cada contrato: o harness valida contra o fixture do kit no CI (hoje por variável de ambiente, manual); remover as cópias legadas do schema de ProductEvent na raiz de `contracts/`.
- Gate de CI do harness conforme a especificação do kit (lint, conformance, testes).
- Concluir a troca de nomes legados e decidir a fonte única das skills (kit versus engineering-team).
- Congelar PRs e branches abertos ou decidir migrá-los.

**Fase 1: importar com histórico, em clone de trabalho**
- Criar o repositório novo vazio e trazer cada repositório para `packages/<nome>/` preservando o histórico (`git subtree add` ou `git filter-repo`). Os históricos são pequenos (6 a 17 commits), então o custo é baixo.
- Os repositórios atuais ficam intactos. Nada de force-push.

**Fase 2: religar**
- CI por pacote com filtro de caminho; releases por tag de pacote com artefato e checksum (o harness mantém o padrão de `harness-v*` e `SHA256SUMS`).
- Verificador de fronteiras no nível de pacote (generalizar `scripts/validate-architecture.cjs` e `contracts/repository-boundaries.yaml`), mais `CODEOWNERS`.
- Atualizar `vehicle-tracking/vendor/harness-artifact.json` para apontar para o artefato de release do repositório novo, não para um SHA de código-fonte.

**Fase 3: documentação e registry**
- Atualizar `portfolio-products.json`, `ARCHITECTURE-OWNERSHIP.yaml`, o registry e `PLATFORM-DELIVERY-FLOW.md` (dentro da plataforma, regras e handoff entre pacotes passam a ser contrato interno; o fingerprint do registry segue válido para o `ai-team` que atua em produtos).
- O `ai-team` passa a tratar a plataforma como um único alvo para mudanças que cruzam pacotes.

**Fase 4: virada e arquivamento**
- Seguir `docs/LEGACY-CUTOVER-GATE.md`: `main` com o conjunto completo de fontes, CI verde, PRs migrados ou rejeitados, nenhuma referência ativa aos repositórios antigos. Arquivar como somente leitura; apagar é uma operação separada e explícita.

## Decisões em aberto

| Decisão | Opções |
| --- | --- |
| Nome do repositório | **Decidido**: `leandroclf/product-platform` (criado, vazio) |
| Pacote de contratos | manter o nome `kit` ou renomear para `contracts` |
| Consumo do harness pelos produtos | artefato de release (recomendado) ou subdiretório Git com SHA |
| Histórico | preservar (recomendado) ou começar limpo |
| Calendário | antes ou depois de o `vehicle-tracking` adotar a versão 0.2.0 do harness |

## Reversão

Enquanto a Fase 4 não ocorrer, os repositórios atuais permanecem a fonte de verdade e a migração pode ser descartada sem perda.
