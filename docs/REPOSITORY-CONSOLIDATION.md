# Consolidação por capacidade e consumidores

## Decisões aplicadas

`product-platform/packages/engineering-team` permanece o único executor canônico
de engenharia; Kit é dono de políticas/skills, CLI de proposta e harness de
runtime embutido nos produtos. Não há novo gateway, serviço de memória central
ou repositório a criar. AICP é referência de console/contexto/observabilidade;
ClawTeam é pesquisa de swarm. Não conectar outra autoridade de orçamento, estado
ou roteamento ao ai-team sem workload e benchmark. Agentes de domínio não são
agentes de engenharia e permanecem nos produtos.

## agents-workspace e claude-workspace

Árvores completas, não truncadas, confrontadas em:

- agents-workspace: `3712bd56d72bb597c44f73aec2fcf521add44462`;
- claude-workspace: `5a1da7e1a7ef26e834ebb5444dfd6871151ec8d9`.

Há 71 arquivos comuns: 47 com o mesmo blob SHA e 24 diferentes. O primeiro tem
11 arquivos adicionais e nenhum arquivo exclusivo foi encontrado no segundo.
Isso sustenta classificá-los como a mesma família legada, mas não afirma que o
primeiro contém toda a semântica do segundo.

Deltas relevantes: `api/app.py`, CLI, orchestrator, backends Claude/Codex,
memória, skill_manager, workflow engine, filesystem MCP, Compose e respectivos
testes. Adições no agents incluem code_analysis_agent, testes de API/CLI/workflow,
bootstrap e declaração de consolidação. Não extrair esses componentes para o
runtime canônico sem lacuna concreta. Preservar ambos para comparar os deltas;
nenhuma fusão ou arquivamento administrativo enquanto usos locais não forem
confirmados. Novas capacidades genéricas pertencem ao Kit e novas etapas de
engenharia ao ai-team.

Fontes: [agents tree](https://github.com/leandroclf/agents-workspace/tree/3712bd56d72bb597c44f73aec2fcf521add44462),
[claude tree](https://github.com/leandroclf/claude-workspace/tree/5a1da7e1a7ef26e834ebb5444dfd6871151ec8d9).

## ai-hub, protokit-core e harness

| Invariante | ai-hub (Go, 4e3d5c2) | protokit-core (TS, c8e1f95) | Decisão |
|---|---|---|---|
| Publicação durável | Outbox relay marca publicado após sucesso, admite repetição do event_id | CreateProtocol salva protocolo e depois enfileira persistência/notificação em chamadas separadas | Não assumir atomicidade equivalente nem copiar implementação |
| Recuperação concorrente | Migração callback_inbox tem claim_owner, claim_epoch e lease_until | Worker mostrado usa isProcessing em memória e busca pendências | Flag de processo não prova exclusão entre instâncias |
| Retry de bucket | Autoridades específicas de storage/delivery no domínio do hub | retryBucketPersist explicitamente não implementado no worker | Não escolher protokit como implementação canônica de entrega garantida |
| Tenancy e destino | Snapshot versionado de webhook com tenant/cell/application | client_id/service_name e webhook na entidade de protocolo | Contratos de isolamento diferentes; não intercambiáveis |
| Harness | Sem dependência de serviço externo para núcleo compartilhado | Não é biblioteca do harness | Implementar futuras garantias no dono canônico somente quando justificadas |

A auditoria antiga de setembro do ai-hub não descreve toda a implementação atual:
a árvore e as migrações atuais já contêm inbox com leases e novos controles.
Isso corrige a limitação da revisão inicial, que se baseou nesse documento antigo.
As evidências abaixo são código inspecionado, não execução contra PostgreSQL ou
certificação dos serviços. Não se conclui que não há outros controles no protokit.

Fontes:

- [relay](https://github.com/leandroclf/ai-hub/blob/4e3d5c21cbc1d8835f145e6110a49e849f76572f/hub/internal/outbox/relay.go)
- [leases](https://github.com/leandroclf/ai-hub/blob/4e3d5c21cbc1d8835f145e6110a49e849f76572f/hub/migrations/core/0036_callback_inbox_leases.sql)
- [destino](https://github.com/leandroclf/ai-hub/blob/4e3d5c21cbc1d8835f145e6110a49e849f76572f/hub/migrations/core/0040_webhook_application_snapshot.sql)
- [create protocol](https://github.com/leandroclf/protokit-core/blob/c8e1f953b29b8bac21081a08ba5a67d48b75203a/src/domain/usecases/create-protocol.usecase.ts)
- [retry worker](https://github.com/leandroclf/protokit-core/blob/c8e1f953b29b8bac21081a08ba5a67d48b75203a/src/infrastructure/workers/failure-retry.worker.ts)

## Gate antes de descontinuar qualquer legado

Inventariar consumidor, host e dados persistidos; comparar contratos e política
de licença; provar compatibilidade e recuperação no destino; oferecer migração e
rollback; só então arquivar, sem apagar histórico. Até lá, não ampliar runtimes
legados nem redirecionar tráfego. Estes gates evitam transformar simplificação de
código em perda de comportamento ou dados.
