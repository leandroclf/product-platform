# OpenHands: análise para evolução autônoma de produtos

Data: 2026-10-31. Plataforma analisada a partir de `45dc09745969c59eb5cd2876d073d758e61cc9be`.

## Conclusão arquitetural

A inteligência mais útil é o controle do ciclo de trabalho: objetivo explícito, execução isolada, estado persistido, julgamento de conclusão, feedback, limites e detecção de estagnação. Copiar a interface ou instalar outro runtime não produz autonomia por si só. A plataforma já implementa parte relevante desses mecanismos no `ai-team`; a estratégia é estendê-los no dono canônico e validar operação real.

O repositório indicado atualmente é **Agent Canvas**, não o antigo backend monolítico Python. Seu README delimita outros donos: SDK/Agent Server e Automation. Uma análise que procurasse apenas o antigo agent controller no Canvas erraria o componente.

## Fontes fixadas e cobertura

| Repositório | Commit analisado | Arquivos inventariados | Texto UTF-8 |
| --- | --- | ---: | ---: |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands/tree/2e92e7ec6935f31e36f08eb8dd2c5cef347df120) | `2e92e7ec6935f31e36f08eb8dd2c5cef347df120` | 2852 | 2696 |
| [OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk/tree/98de8bf3aca7e59eedebd7a97c423986ea1c4c05) | `98de8bf3aca7e59eedebd7a97c423986ea1c4c05` | 1965 | 1965 |
| [OpenHands/automation](https://github.com/OpenHands/automation/tree/407bf8a021cce90656ee8d92292bd742b550080f) | `407bf8a021cce90656ee8d92292bd742b550080f` | 309 | 309 |

Todos os arquivos rastreados disponíveis foram inventariados por caminho, tamanho e SHA256 em `openhands/*-inventory.json`; `coverage.json` agrega diretórios e extensões. O inventário cobre 5126 arquivos e permite verificar o snapshot, **não equivale a auditoria semântica manual de todas as linhas**. A leitura aprofundada se concentrou nos caminhos de arquitetura, execução, estado, metas, repetição, segurança, agendamento e integração abaixo. Não foram executados os três sistemas upstream nem seus testes; suas garantias são contratos/código observados, não certificação independente. Os clones são shallow; histórico de vulnerabilidades e todos os releases não foram auditados. O cliente TypeScript separado não foi clonado; os consumidores e o cliente presente no SDK foram apenas localizados.

## Mapa dos arquivos e decisões

Os caminhos abaixo são relativos a cada snapshot fixado; podem ser abertos nos links acima.

| Área | Evidência principal | O que faz / consequência |
| --- | --- | --- |
| Limites do Canvas | `README.md`, `AGENTS.md`, `docs/architecture.md` | UI e orquestração de stack; SDK executa ações; Automation decide quando iniciar |
| Distribuição e dependências | `package.json`, lockfile, `bin/`, `scripts/`, `docker/`, `helm/`, `.github/workflows/` | Instalação local, container e infraestrutura; não transportar a árvore de dependências para a plataforma |
| UI operacional | `src/components/features/conversation/`, `conversation-panel/`, `automations/`, `backends/` | Conversas, uso, estado, automações e backends; útil como referência futura, fora da lacuna imediata de execução |
| Adaptadores de backend | `src/api/backend-registry/`, `conversation-service/`, `runtime-service/` | Separar visualização e transporte do mecanismo de execução; a plataforma já tem estágios fixos, não precisa de ACP agora |
| Histórico completo | `src/api/event-service/event-service.api.ts`, `src/utils/transcript-export/load-complete-events.ts` | Paginação, deduplicação por ID e detecção de cursor repetido; logs incompletos não devem ser evidência de conclusão |
| Goal loop | SDK `conversation/goal/controller.py`, `runner.py`, `judge.py` | Um juiz avalia o objetivo, devolve faltantes e limita iterações; já há equivalência parcial no aceite e nas revisões independentes do ai-team |
| Execução e budgets | SDK `conversation/impl/local_conversation.py` | Limites de iterações e custo acumulado; custo inclui agente e condenser; tempo/ciclos existentes na plataforma não equivalem a limite monetário |
| Falta de progresso | SDK `conversation/stuck_detector.py` | Ações/observações repetidas, erros, monólogos, alternância e janela de contexto; a granularidade é evento, distinta dos ciclos do ai-team |
| Persistência | SDK `conversation/state.py`, `event_store.py`, `events_list_base.py`, `persistence_const.py` | Estado e eventos persistentes, sequência durável e locks; o próprio código ressalva flock em NFS |
| Memória | SDK `context/condenser/` | Compactação contextual; manter artefatos verificáveis como fonte de verdade, nunca resumir uma aprovação como se fosse a identidade original |
| Segurança | SDK `security/confirmation_policy.py`, `analyzer.py`, `risk.py`, `defense_in_depth/` | Políticas e análise em camadas; não presumir que um classificador LLM seja uma fronteira suficiente |
| Workspaces | SDK `workspace/`, Canvas README Docker por conversa | Local/remoto e isolamento por conversa; mesmo container não elimina conflito se o workspace de host for compartilhado |
| Agendamento | Automation `scheduler.py` | Polling com lotes e `FOR UPDATE SKIP LOCKED` em PostgreSQL; SQLite assume processo único |
| Dedupe por assunto | Automation `conversations.py` | Advisory lock transacional por automation/subject para serializar criação; evita confiar em lock de linha quando a linha ainda não existe |
| Execução externa | Automation `execution.py`, `backends/local.py`, `backends/base.py` | Backends, timeout, workspace por run e tratamento de rate limit; confirmação perdida exige reconciliar estado remoto |
| Triggers e operação | Automation `webhook_router.py`, `models.py`, `trigger_matcher.py`, `streams/` | Modelo persistido de runs, integração e eventos; copiar tudo adicionaria banco/serviço e superfície operacional |
| Testes e qualidade | Canvas `__tests__/`, `tests/`, Playwright/Vitest; SDK `tests/cross/test_stuck_detector.py`, integração; Automation `tests/` | Upstream possui testes, mas sua aprovação não foi executada nesta análise; a adaptação usa testes próprios e reais de Git |
| Ativos e apresentação | Canvas `public/`, `src/i18n/`, estilos, Electron; SDK/Automation exemplos e docs | Inventariados; não há justificativa para copiá-los ao runtime de produtos |

## Comparação com a plataforma

| Capacidade | Situação observada na plataforma | Decisão |
| --- | --- | --- |
| Missão inequívoca de autonomia | Regras técnicas mais explícitas que o objetivo empresarial | Incluir missão e continuidade nos AGENTS de raiz, kit, harness, time e templates |
| Agente implementar até terminar | Plan/implement/test/validate/review já encadeados | Preservar o runtime e evitar camada paralela |
| Critério independente de conclusão | Plano com critérios, `acceptance_results`, SHA e plan_id | Reutilizar; não adicionar juiz que apenas aceita relato do implementador |
| Feedback e replanejamento | `REPLAN_REQUIRED`, correção após testes/review | Reutilizar budgets existentes; não aumentar ciclos indiscriminadamente |
| Estado e retomada | Estado atômico, locks, proteção contra replay de estágio ativo | Preservar; não habilitar retry irrestrito |
| Estagnação | Bloqueia implementação sem commit; alterações só de notas e alternância ainda podem consumir ciclos | Adicionar fingerprints de conteúdo e histórico persistido |
| Orçamento | Timeout, max_seconds, max_cycles e limites de turnos | Preservar; custo monetário agregado é lacuna explícita |
| Backlog → execução | Fila, elegibilidade, hash, launcher e piloto de uma tarefa | Já existe; operação contínua autorizada e instalada precisa de piloto/supervisor, não de mais um framework |
| Concurrency | Lock local por projeto | Suficiente para piloto de um host; não afirmar coordenação distribuída |
| Entrega | Revisão local, PR e integração separados | Manter gates de identidade e SHA, sem tratar REVIEWED como deploy |

## Adaptação entregue

1. Missão e contrato de continuidade nos arquivos de instrução e templates reais, sem alterar fixtures de testes para simular conformidade.
2. `record_product_progress` no coordenador existente, executado após snapshot de implementação e antes de replanejar ou testar: bloqueia três conteúdos iguais ou alternância A/B/A/B. Exclui somente notas geradas de runs. Histórico de seis hashes no checkpoint, sem dependência nova, prompts ou código de produto nos fingerprints.
3. Testes em repositórios Git reais: progresso legítimo, notas sem progresso com reload de estado, alternância e mudanças de specs legítimas.
4. Contrato operacional e prioridades em `docs/AUTONOMOUS-PRODUCT-EVOLUTION.md`.

Essa adaptação é implementação própria inspirada no padrão upstream. Não é o detector completo do SDK: não vê monólogos, chamadas individuais ou loops dentro de uma sessão do provider. Commits com mudanças cosméticas também podem gerar fingerprints diferentes. Os limites existentes continuam necessários.

## O que não copiar e por quê

- Canvas/React/Electron/Helm para resolver continuidade do backend: alto custo de integração sem fechar a lacuna operacional.
- SDK completo, Agent Server e Automation juntos: duplicariam o ai-team, o launcher e os contratos; novos serviços e dependências precisam de benefício medido.
- Execução local irrestrita, autoaprovação ou replay de chamadas incertas: comprometem os controles existentes.
- Políticas de modelo dinâmico/ACP como requisito de autonomia: o fluxo isolado existente já permite executar os quatro papéis.
- Estado de conversa ou eventos internos como ProductEvent: eventos técnicos de engenharia e eventos de produto têm contratos e públicos diferentes.

## Sequência recomendada e medida de sucesso

Priorizar piloto real autenticado, supervisor local com autorização delimitada, métricas de intervenções e custo por entrega aceita, orçamento monetário e retomada reconciliada. O backlog detalhado e critérios estão no documento operacional. Medir autonomia pela entrega aceita e pelo trabalho humano necessário, não pelo número de agentes ou horas gastas.

O ambiente desta análise não demonstrou logins dos providers nem Docker operacional. Portanto os testes offline deste PR não comprovam implantação de um time que opera 24/7. Uma execução real será necessária para essa afirmação.

## Licença e proveniência

Os arquivos LICENSE dos três snapshots declaram MIT. Nenhum código-fonte upstream foi incorporado ou dependência OpenHands instalada; os inventários contêm metadados. Os padrões foram adaptados na implementação existente. Se uma evolução futura copiar trechos substanciais, preservar integralmente copyright e licença MIT da origem e registrar commit/caminho; componentes de outros repositórios ou serviços comerciais devem ter licença verificada separadamente.
