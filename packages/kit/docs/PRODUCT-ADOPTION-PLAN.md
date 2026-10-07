# Plano de adoção da plataforma pelos produtos

Estado em 2026-10-07, levantado nos repositórios locais. A adoção é capacidade por capacidade (`contracts/portfolio-products.json`): um produto só adota o que usa, nunca todo o harness.

| Produto | Runtime | Wave | Estado | Próximo passo |
|---|---|---|---|---|
| vehicle-tracking | TypeScript | 1 | Adotou `harness-v0.2.0` (tarball) | Migrar para a release com eventos e pagamentos conforme novas capacidades do harness saírem |
| bussola-financeira | Python | 1 | Adotou `harness-v0.2.1` (wheel); adaptador de eventos | Aplicar migrações no ambiente de teste: 8 testes de `tests/test_api.py` já falhavam por banco SQLite não migrado, e o CI só executa os testes de eventos |
| ai-docs | Python | 2 | Adotou `harness-v0.2.1` (wheel); adaptador de eventos | Nenhum bloqueio de plataforma; o CI instala os requisitos completos e passou com o wheel por caminho relativo |
| lf-worldbank-risk-pricing | Python | 2 | Sem eventos; CI e testes existem | Adicionar `AGENTS.md` da plataforma; adotar eventos só quando houver sinal de produto a medir |
| lf-openalex-enrichment-mvp | Python | 2 | Sem eventos; CI e testes existem | Idem |
| lf-wikidata-entity-graph | Python | 2 | Sem eventos; CI e testes existem | Idem |
| agentic-travel-engine | Python | 3 | Sem eventos e sem CI configurado | Criar CI mínimo antes de qualquer adoção; depois `AGENTS.md` |
| fivem-server-monitor-pro | Lua (self-hosted) | 3 | Fora do escopo do harness: o runtime atual é TypeScript e Python | Manter só a conformance de contrato; telemetria externa desligada por padrão |
| professional-english-coach | JavaScript local-first | 3 | Sem eventos; telemetria externa desligada por padrão | Reavaliar um adaptador TypeScript do harness apenas se houver telemetria opt-in |

## Regras para cada adoção

1. Regras da plataforma no `AGENTS.md` do produto (modelo em `templates/TARGET-AGENTS.md`).
2. Artefato do harness vendorizado, verificado por checksum e referenciado por uma release `harness-v*`; nunca o código-fonte do repositório da plataforma.
3. Um adaptador fino por capacidade, sem cópia da implementação, e CI que roda o validador do artefato e os testes de conformance.
4. PR por produto, com CI verde antes do merge.

## Lacunas da plataforma que limitam a adoção

- O harness só cobre eventos em Python. Pagamentos, entitlements com persistência, inbox/outbox e métricas seguem como planejados no registry.
- Produtos Lua e local-first não têm adaptador.
