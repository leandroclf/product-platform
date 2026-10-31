# Evolução autônoma dos produtos

## Objetivo e responsabilidade

A missão da Product Platform é executar continuamente trabalho autorizado de evolução dos produtos da empresa: transformar objetivos em critérios de aceite, selecionar capacidades existentes, implementar, testar, corrigir, validar e preparar entregas demonstráveis. O humano define objetivos, prioridades e autorizações relevantes. Os agentes conduzem as etapas executáveis sem confirmação redundante.

Instruções são uma política de comportamento; não mantêm processos vivos nem constituem evidência de autonomia operacional. A operação contínua exige um executor disponível com autenticação válida, isolamento, backlog elegível e controles efetivamente configurados.

## Arquitetura adotada

Reutilizar a fila e os componentes existentes, sem adicionar gateway, Agent Server ou outro orquestrador:

| Responsabilidade | Componente canônico |
| --- | --- |
| Entrada e elegibilidade | `scripts/portfolio_backlog_intake.py`, `backlog_candidate_queue.py` |
| Atualidade e hash de escopo | `fresh_queue_handoff.py`, `verified_ai_team_handoff.py` |
| Preflight e execução local | `local_ai_team_launcher.py`, `run_backlog_pilot.py` |
| Planejamento, implementação, validação e revisão | `packages/engineering-team/scripts/local_team.py` |
| Identidade, risco, isolamento, checkpoints e budgets de tempo | Controles já existentes do `ai-team` |
| Revisão GitHub e integração | `docs/AUTOMERGE-OPERATIONS.md` e gates nativos |
| Capacidades de produto | Kit e harness; produtos consomem releases imutáveis |

Manter o mapeamento de estágios já existente: OpenAI planeja e valida; Claude implementa e revisa, em sessões isoladas. O fluxo automático de backlog bloqueia R2/R3. O CLI local permite autorizar individualmente planos até R2 com `ai-team run --authorize-r2`, mas R3 continua bloqueado e planos R2 não podem ser entregues pelo CLI. Não ampliar a fila automática com essa autorização por tarefa.



A comparação com o runtime Hive está registrada em [docs/research/HIVE-ANALYSIS.md](research/HIVE-ANALYSIS.md). Ela confirma o desenho atual: estender o supervisor de backlog já previsto, iniciando com uma tarefa por invocação; reutilizar checkpoints, hashes, locks e gates existentes; e condicionar qualquer paralelismo ou promoção automática de skills a evidência operacional. Não adicionar um segundo orquestrador, banco de estado ou runtime de agentes.

## Contrato de execução

1. Fixar tarefa, produto, repositório, base, escopo autorizado e critérios de aceite. Resolver REUSE > EXTEND > CREATE.
2. Verificar ferramentas, autenticação, imagem e comandos reais do produto; executar o doctor do fluxo existente.
3. Executar o ciclo plan → implement → testes offline → validate → review. Falha corrigível volta à implementação; plano inadequado volta ao planejamento, dentro dos limites existentes.
4. Persistir evidências e checkpoints no estado atômico existente. Locks impedem duas execuções locais concorrentes no mesmo projeto. Esses locks não coordenam múltiplos hosts.
5. O guard de progresso compara o diff de conteúdo do produto com a base. Três resultados iguais ou quatro resultados alternados A/B/A/B interrompem novas tentativas. Os seis últimos fingerprints sobrevivem aos checkpoints. Notas geradas em `openspec/changes/ai-team-*` não contam como progresso; mudanças legítimas de specs contam.
6. `REVIEWED` significa revisão local concluída. Entregar PR, integrar e publicar são etapas distintas, com seus controles e autorização aplicáveis.
7. Ao terminar uma tarefa, só selecionar outra se ela também estiver elegível e coberta pela autorização. O piloto atual executa uma tarefa por invocação; este documento não instala um scheduler de implementação.

Um fingerprint diferente não demonstra melhora semântica. O guard reduz repetição evidente; testes, validação e revisão continuam sendo a prova de aceite. Erros transitórios com efeitos incertos não podem ser repetidos automaticamente.

## Operação real e aceite

Começar pelo procedimento em `docs/ONE-COMMAND-BACKLOG-PILOT.md`. O modo preview continua padrão; `--execute --confirm-hash` conserva a autorização específica do piloto. A autorização dada nesta mudança não instala um serviço permanente nem autoriza tarefas futuras arbitrárias.

A primeira execução real deve demonstrar, em produto escolhido e tarefa R1 elegível: autenticação válida, workspace isolado, teste que falha antes e passa após a correção, revisão independente no HEAD atual, evidências preservadas e PR vinculado à tarefa. Testar cancelamento e interrupção sem duplicar efeitos. Só depois ampliar a janela de execução e a quantidade de tarefas, mantendo budgets e opt-out.

Para operação independente do notebook, usar host dedicado disponível. Os timers de revisão existentes não equivalem a um worker de implementação instalado. Não afirmar operação 24/7 enquanto esse piloto e a instalação do executor não tiverem evidências reais.

## Próximas capacidades, com critérios

| Prioridade | Trabalho | Aceite / limite |
| --- | --- | --- |
| P0 | Piloto autenticado ponta a ponta | Links de tarefa, run, checks e PR; falhas e custo efetivo registrados |
| P1 | Supervisor local de backlog autorizado | Allowlist de produtos, scope/hash, orçamento agregado, lock, cancelamento; sem replay de estado incerto; revisão do contrato de autorização antes de remover confirmação por tarefa |
| P1 | Métricas de autonomia | Tempo até entrega, taxa de aceite, intervenções humanas, custo por tarefa aceita, loops e retrabalho; sem exportar prompts/segredos |
| P2 | Budget monetário | Contabilizar uso dos dois provedores, inclusive falhas e revisões; dados ausentes nunca significam custo zero |
| P2 | Retomada reconciliada | Classificar checkpoint seguro versus chamada remota incerta; testar crash em cada fronteira antes de ampliar replay |
| Condicional | Painel operacional | Somente após demanda comprovada; consumir evidências existentes, sem duplicar runtime |

Análises de referência e decisões: [OpenHands](research/OPENHANDS-ANALYSIS.md) e [Hive](research/HIVE-ANALYSIS.md).
