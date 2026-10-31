# Análise e proposta: runtimes de execução de agentes

**Data da pesquisa:** 2026-10-31  
**Escopo:** comparar Symphony, Ralph, Open SWE e Gas Town com a arquitetura vigente da Product Platform e recomendar apenas mudanças incrementais que melhorem sua estrutura atual.

## Decisão executiva

A Product Platform já implementa os elementos centrais da continuidade do Ralph: contexto novo por etapa, estado e artefatos persistidos, ciclos limitados, checks independentes e bloqueio quando o estado fica incerto. Não há justificativa atual para instalar um loop Ralph à parte.

O melhor padrão para evoluir o que existe é o **supervisor local serial inspirado na especificação do Symphony**: seleção de trabalho elegível, execução isolada com limite de concorrência, observabilidade e reconciliação antes de retomar. Isso complementa o supervisor de backlog já previsto, sem introduzir outro runtime ou banco de estado.

Do Open SWE, a única lacuna potencialmente nova é o ciclo posterior de **diagnóstico de CI e retorno limitado à correção**. A proposta é mantê-la como hipótese condicionada ao piloto e à triagem de segurança, sem executar novamente workflows ou modificar PRs automaticamente nesta etapa.

Gas Town oferece mecanismos úteis quando paralelismo e coordenação multi-repositório forem gargalos medidos. Seus papéis, banco e ferramentas duplicariam a estrutura atual hoje.

## Base atual da Product Platform

Esta análise considera a documentação corrente da branch `main`:

- [Evolução autônoma dos produtos](../AUTONOMOUS-PRODUCT-EVOLUTION.md) determina reuso dos componentes existentes, uma tarefa por invocação no piloto, fila automática limitada a R0/R1, budgets, locks e interrupção diante de repetição ou estado incerto.
- [Etapas isoladas do ai-team](../../packages/engineering-team/docs/ISOLATED-AGENT-STAGES.md) já usa sessões novas para planejar, implementar, validar e revisar; preserva estado e artefatos por ciclo e não retoma conversas de agentes.
- [Ciclo de entrega](../../packages/engineering-team/docs/DELIVERY-LIFECYCLE.md) separa revisão, PR, CI, merge e deploy. O CLI pode abrir PR draft, mas não faz merge ou deploy automático.
- [Contrato de backlog](../AUTONOMOUS-BACKLOG-CONTRACT.md) mantém a fila em preview e requer evidência, orçamento e aceite explícito antes da promoção.
- A issue [#34 — auditoria do ai-team](https://github.com/leandroclf/product-platform/issues/34) já exige prova operacional real, falhas controladas e aferição de limites multi-host. A issue [#58 — G6](https://github.com/leandroclf/product-platform/issues/58) cobre publicação e saúde dos runtimes, sem propor reparo de CI de PR.

Consequência: referências externas são padrões para avaliar, não autorização para instalar dependências, conceder permissões ou alterar gates. Esta análise não promove automaticamente novas tarefas à fila.

## Comparação orientada à decisão

| Projeto | Mecanismo relevante | Já coberto na plataforma | Ganho incremental possível | Decisão |
| --- | --- | --- | --- | --- |
| [OpenHands](https://github.com/OpenHands/OpenHands) | Agent Canvas para operação, SDK/Agent Server para execução e Automation para agendamento/dispatch; goal loop, budget acumulado, event store e stuck detector | Sessões isoladas, acceptance independente, estado/checkpoints e fingerprints por ciclo já existem; backlog supervisor e budget monetário estão no plano atual | Usar a leitura como referência para a retomada reconciliada e budget P2; só considerar detector por evento se o piloto provar loops longos dentro de uma sessão | **Não importar SDK/Canvas/Automation; reaproveitar as adaptações e prioridades já existentes** |
| [OpenAI Symphony](https://github.com/openai/symphony) | Scheduler que consulta tracker, despacha tarefas elegíveis com concorrência limitada, workspace por tarefa, parada quando deixa de ser elegível, logs e recuperação orientada a tracker/arquivos | Handoff, launcher, fila, checkpoints, hashes e piloto já existem; execução ainda é uma tarefa por invocação | Completar o supervisor local previsto com ciclo de seleção/reconciliação, começando serial | **Adotar padrões na evolução do supervisor; não adotar implementação ou serviço agora** |
| [Ralph](https://github.com/KLIEBHAN/ralph-loop) | Loop externo simples, sessões novas e progresso comunicado por arquivos/Git | Sessões por etapa, estado por ciclo, limite de prazo/ciclos e guard de repetição já existem | Reafirmar que conclusão precisa de validação verificável, nunca só de marcador do agente | **Não adicionar runner; conservar o princípio onde já está implementado** |
| [Open SWE](https://github.com/langchain-ai/open-swe) | Fluxo de issue até PR, revisão, monitoramento de CI e follow-up; sandbox por thread e integrações | Implementação, validação, revisão isolada, entrega draft e CI GitHub são fases existentes, mas CI fica após a entrega | Futuro diagnóstico limitado de falha de CI como nova entrada de reparo, com gates completos no SHA atualizado | **Candidato pós-piloto; estudar apenas a função de feedback** |
| [Gas Town](https://github.com/gastownhall/gastown) | Coordenação de múltiplos workers e worktrees, supervisores, fila/merge queue e estado de trabalho próprio | Workspaces isolados, fila autorizada, checkpoints e fluxo Git existem; locks atuais são locais | Coordenação distribuída e merge queue podem ser úteis se throughput multi-host for gargalo demonstrado | **Adiar até haver métricas que justifiquem paralelismo** |

## Análise dos projetos

### OpenHands: capacidades separadas, com pouca lacuna nova

A análise aprofundada já integrada na plataforma está em [OPENHANDS-ANALYSIS.md](OPENHANDS-ANALYSIS.md). Ela inventariou 5.126 arquivos em três snapshots fixados: `OpenHands/OpenHands` (Agent Canvas), `OpenHands/software-agent-sdk` (SDK e Agent Server) e `OpenHands/automation`. O inventário de caminhos/SHA permite auditar escopo e proveniência, mas não equivale à leitura semântica linha a linha de todo o monorepo; a análise aprofundada focou runtime, estado, segurança, execução, loops, scheduler e integrações. Os sistemas e testes upstream não foram executados como parte dessa análise.

A separação de responsabilidades é uma lição útil: Canvas cuida da experiência e dos backends; SDK/Agent Server executa conversas; Automation mantém triggers, histórico e dispatch. Essa modularidade não é razão para reproduzir a topologia na Product Platform: o `ai-team` já é o executor canônico, enquanto a fila/handoff existentes coordenam o backlog. Importar Agent Server, SDK e Automation aumentaria dependências, serviços, modelos de estado e esforço de operação, sem preencher uma lacuna demonstrada.

**O que já foi aproveitado:** missão explícita de evolução autônoma, evidências/checkpoints e detector de falta de progresso por fingerprints persistidos foram incorporados no trabalho anterior documentado em `OPENHANDS-ANALYSIS.md`. Logo, essa capacidade não deve ser cadastrada novamente como recomendação nova.

**O que ainda pode evoluir, dentro do plano existente:** OpenHands agrega budgets de execução ao longo de turns e custo de componentes auxiliares; isso reforça a prioridade P2 de contabilizar custo monetário dos provedores e revisões no `ai-team`. O detector OpenHands observa padrões de ações/observações repetidas durante a conversa, enquanto o guard da plataforma trabalha no diff após ciclos. A diferença é real, mas adicionar hooks eventuais no provider/runtime pode ampliar acoplamento e falsos positivos. Só vale prototipar se o piloto registrar loops intrassessão que os limites de turnos e ciclos não resolvam; até lá, manter a proteção atual e o backlog P2 de budget/retomada reconciliada.

O Automation oferece polling/dispatch com locks de banco e deduplicação transacional por assunto. Isso é relevante se a plataforma precisar de workers distribuídos ou dedupe concorrente entre hosts. No estado atual, o supervisor é local e serial, e a fila tem contratos de autorização próprios. Não substituir esses contratos por um segundo scheduler nem adicionar PostgreSQL só para espelhar OpenHands. Reavaliar com evidência de contenção, duplicação ou throughput insuficiente em multi-host.

As políticas de confirmação e classificação de risco do SDK são defesa em profundidade; um classificador de risco não deve virar fronteira de segurança. A Product Platform já bloqueia R2/R3 fora das autorizações específicas. Preservar os gates nativos e usar a análise OpenHands apenas como referência para auditar ferramentas/permissões, sem trocar autorização determinística por julgamento do agente.

### Symphony: o melhor encaixe para o próximo incremento

A especificação do Symphony separa leitura de backlog e execução, define concorrência limitada, workspaces determinísticos por issue, interrupção quando a tarefa deixa de ser elegível, backoff para falhas transitórias e logs operacionais. A especificação prevê reconstruir parte do estado por tracker e filesystem após reinício, sem exigir banco persistente.

Isso se alinha à decisão já documentada de estender o supervisor local existente. O incremento recomendado é pequeno: consolidar elegibilidade e autorização, adquirir lock, abrir/validar workspace da tarefa, executar uma tarefa por vez, registrar eventos e resultado, então reconciliar estado antes de retomar. Só erros comprovadamente transitórios e sem efeito externo conhecido podem usar retry limitado. Alteração de elegibilidade, cancelamento, hash divergente ou efeito remoto incerto interrompe a execução para reconciliação.

A concorrência deve permanecer em **1** até que a issue #34 e o piloto comprovem isolamento, budgets agregados e comportamento sob falha. Não se deve copiar um mecanismo de retry isolado do restante dos guardrails.

**Maturidade:** o repositório identifica-se como preview para ambientes confiáveis e a implementação Elixir como protótipo para avaliação; a própria documentação recomenda implementar uma versão endurecida baseada na especificação. Portanto, a referência é o contrato arquitetural, não o runtime de referência.

### Ralph: simplicidade correta, mas sem lacuna estrutural

Ralph mantém o loop fora da conversa do agente: cada iteração começa limpa e recebe o progresso através dos arquivos e do histórico Git. Isso reduz o acúmulo de contexto e mantém o mecanismo simples.

A plataforma já oferece essa propriedade de modo mais controlado: cada etapa recebe uma sessão isolada, os resultados são persistidos em artefatos, replanejamento consome o limite de ciclo e saídas inválidas ou estados incertos bloqueiam. Adicionar um segundo loop shell criaria outro ponto de entrada e poderia contornar identidade, autorização, estado, budgets e revisão.

Uma regra útil a preservar: mensagem de conclusão do agente é apenas dado de saída. O aceite depende de checks, validação, revisão no HEAD e evidências vinculadas. O guard atual reduz repetição, mas fingerprint diferente não comprova progresso semântico.

### Open SWE: feedback de CI é a hipótese que merece medir

Open SWE combina execução de código com PR, revisão somente leitura, monitoramento de CI e follow-up em contexto. Seu monitor de PR pode diagnosticar falhas e repetir jobs classificados com evidência como flaky.

O incremento distinto para a Product Platform seria observar o CI de um PR draft já entregue e encaminhar uma falha de código para uma nova implementação limitada. Esse fluxo não deve se tornar um “rerun até verde”: deve correlacionar cada check ao SHA atual, classificar falha de código versus infraestrutura, limitar ciclos e custo, e então repetir offline checks, validação e revisão independente em cada novo SHA. Reexecução de job remoto é efeito externo e precisa de política explícita.

A adoção da plataforma completa não se justifica: Open SWE possui superfície de integração e operação maior, e a documentação alerta que credenciais GitHub da instalação podem permitir acesso ao repositório inteiro instalado, independentemente do acesso pessoal do usuário. Seus sandboxes podem ter rede e ferramentas poderosas. O desenho local atual mantém fronteiras explícitas entre CLI, estágios, provedor e autorização; não ampliar credenciais para obter apenas monitoramento.

### Gas Town: coordenação valiosa com custo de infraestrutura

Gas Town organiza town/rigs, papéis de coordenação e workers, worktrees, estado em Beads/Dolt e uma fila de integração chamada Refinery. Isso ataca problemas de paralelismo, retomada e integração que só aparecem em escala operacional maior.

A Product Platform já tem fonte autorizada de backlog, isolamento de tarefa, controle de estágio e lifecycle Git. Importar papéis, mailbox, Beads/Dolt e gerenciadores paralelos duplicaria mecanismos e aumentaria operação. A instalação também requer toolchain e serviços adicionais (incluindo Go, Dolt, Beads e, no modo completo, tmux). Não há ainda evidência de que o limite atual seja paralelismo, nem de que o lock local esteja causando perda de throughput.

Reavaliar quando houver dados de fila/tempo de espera, tarefas prontas independentes, capacidade multi-host e colisões de integração. Nesse cenário, testar primeiro leases distribuídos e worktrees isolados no desenho atual; só depois comparar com uma plataforma externa.

## Proposta incremental

### P0 — concluir o piloto que já está no plano

Não criar nova plataforma antes de provar uma tarefa R1 real, ponta a ponta, no ambiente autenticado. Registrar tarefa, hash, run, checks, uso, revisão, PR e tratamento de interrupções. A issue #34 já contém os critérios operacionais e testes de falha necessários.

### P1 — supervisor serial, inspirado pela especificação do Symphony

Estender os componentes declarados no documento canônico — intake/queue, handoff atualizado, launcher e `run_backlog_pilot.py` — com este contrato:

1. Recalcular elegibilidade e autorização antes de cada tarefa; selecionar somente allowlist R0/R1 autorizada.
2. Fixar produto, repo, base, hash de escopo e critérios antes de iniciar. Um hash divergente invalida o handoff.
3. Manter concorrência 1, workspace e lock por tarefa, orçamento agregado, prazo e cancelamento verificáveis.
4. Registrar eventos estruturados de início, estágio, checkpoint, falha, retry, bloqueio e término, com ligação à evidência da tarefa.
5. Em reinício, reconciliar tracker, lock, workspace e checkpoint. Se chamada remota puder ter ocorrido, parar e inspecionar; não repetir às cegas.
6. Repetir apenas falhas transitórias classificadas e sem efeito externo incerto, com espera limitada; cancelar ao perder elegibilidade.
7. Entregar para PR e CI existentes. Merge e deploy permanecem etapas separadas sob os gates nativos.

**Aceite para ampliar além de uma tarefa por execução:** piloto real bem-sucedido, cenários de crash/cancelamento sem duplicação, medição de custo, auditoria de logs e limite de execução demonstrado. Sem essa evidência, a fila permanece preview/opt-in e serial.

### P2 candidato — retorno de falhas de CI para reparo

Após o P0 e uma triagem explícita, avaliar um pequeno monitor ligado ao PR draft do `ai-team`:

- Ler check runs e logs apenas do PR e do SHA registrados.
- Diferenciar falha de código, falha de infraestrutura e cancelamento; classificar como desconhecido quando evidência não bastar.
- Reexecutar um job apenas se política permitir e houver evidência de falha transitória; caso contrário, encaminhar diagnóstico.
- Para reparo, iniciar novo ciclo dentro do orçamento autorizado e com o mesmo escopo. Em novo SHA, rodar novamente checks offline, validação OpenAI, revisão Claude e CI.
- Parar em limite, mudança de base/escopo, credencial ausente, achado de segurança ou estado inconsistente.
- Nunca aprovar review, fazer merge, alterar workflow, acessar secrets ou fazer deploy automaticamente.

Essa proposta é **candidata para triagem**, não issue pronta nem autorização de execução. A issue #34 já abrange qualidade, segurança e prova operacional; antes de abrir issue separada, deduplicar com o backlog e verificar se o piloto revelou essa lacuna. Reexecução remota, permissões Actions ou mudança em workflows podem ser R2.

### Condicional — paralelismo coordenado

Só investigar se métricas demonstrarem gargalo serial e houver tarefas independentes suficientes. Critérios mínimos: lease distribuído testado em múltiplos hosts, limites globais de concorrência e custo, worktrees sem compartilhamento de escrita, cancelamento coordenado, reconciliação sem duplicar efeitos e integração ordenada. Comparar custo e confiabilidade com Gas Town nessa fase; não incorporar agora a hierarquia completa nem outra base de estado.

## Sequência recomendada

1. **Symphony primeiro, como referência para completar o supervisor já planejado.**
2. **Ralph como confirmação do desenho atual**, sem adicionar dependência ou nova superfície operacional.
3. **Open SWE para avaliar CI→diagnóstico→reparo**, somente após evidência do piloto e triagem de permissões.
4. **Gas Town depois de medir necessidade real de paralelismo** e validar coordenação multi-host na plataforma atual.

## Fontes primárias

- [OpenHands — análise profunda e inventários fixados](OPENHANDS-ANALYSIS.md), [Agent Canvas](https://github.com/OpenHands/OpenHands), [SDK/Agent Server](https://github.com/OpenHands/software-agent-sdk) e [Automation](https://github.com/OpenHands/automation).
- [Symphony — especificação](https://github.com/openai/symphony/blob/main/SPEC.md) e [status do projeto](https://github.com/openai/symphony/blob/main/README.md).
- [Ralph Loop — implementação e comportamento](https://github.com/KLIEBHAN/ralph-loop).
- [Open SWE — arquitetura e capacidades](https://github.com/langchain-ai/open-swe) e [guia de instalação e confiança](https://github.com/langchain-ai/open-swe/blob/main/docs/INSTALLATION.md).
- [Gas Town — arquitetura](https://github.com/gastownhall/gastown) e [requisitos de instalação](https://github.com/gastownhall/gastown/blob/main/docs/INSTALLING.md).
