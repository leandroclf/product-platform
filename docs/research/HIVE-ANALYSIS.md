# Hive: comparação e decisões para a Product Platform

Data da análise: 2026-10-31.

## Escopo e evidência

A análise do Hive usa o snapshot de `aden-hive/hive` no commit [3ee47a3384ea5b3da0bed9a8e9284c7e9ebf987a](https://github.com/aden-hive/hive/tree/3ee47a3384ea5b3da0bed9a8e9284c7e9ebf987a). A comparação da plataforma usa `leandroclf/product-platform` no commit [7a64095274b6d2b4c947395d7b99b5a3603ffbc1](https://github.com/leandroclf/product-platform/tree/7a64095274b6d2b4c947395d7b99b5a3603ffbc1).

Foram examinados os READMEs e contratos de arquitetura, o ciclo de agentes, persistência, workers, ferramentas de terminal, orçamento, segurança, CI e documentos de backlog da plataforma. Esta é uma revisão arquitetural estática: não executei Hive, a plataforma ou suas suítes de testes. Configurações e garantias descritas pelos projetos não equivalem a uma aceitação operacional independente.

## Conclusão

O Hive é um runtime local amplo para agentes persistentes que aprendem um procedimento durante um piloto, distribuem unidades semelhantes para workers e acompanham resultados em um tracker compartilhado. Sua melhor contribuição para a Product Platform é validar padrões de coordenação e retomada.

A Product Platform já implementa escolhas mais adequadas ao seu problema de engenharia de produtos: papéis fixos por etapa, provedores separados, regras e capacidades congeladas por hash, execução com workspace isolado, testes sem rede e gates explícitos para entrega. Ela também já prevê supervisor de backlog, orçamento agregado, métricas e retomada reconciliada. Portanto, boa parte do valor do Hive já está coberta ou planejada.

**Decisão:** aproveitar os conceitos como critérios de evolução do supervisor e dos controles de execução. Não portar o runtime, não criar outro orquestrador, serviço always-on, tracker SQLite ou camada de routing. Não abrir tarefa duplicada para capacidades que já aparecem no roadmap. O primeiro supervisor continua serial e deve provar operação ponta a ponta antes de qualquer fan-out.

## Comparação de arquitetura

| Dimensão | Hive | Product Platform atual | Decisão para a plataforma |
|---|---|---|---|
| Unidade de execução | Uma `AgentLoop`; a queen é persistente e workers são clones com tarefa, ferramentas e orçamento próprios. A queen decide a decomposição em runtime. | `ai-team` executa `plan → implement → validate → review`, com sessões e ferramentas isoladas por papel. Os contratos fixam objetivo, base, hash, risco e aceite. | Manter o ciclo especializado por etapa. Usar a ideia de supervisor para selecionar trabalho autorizado do backlog, sem substituir o contrato de handoff por uma queen autônoma que redefine escopo. |
| Coordenação | Workers paralelos reportam para a queen; o tracker SQLite é o estado compartilhado e pode ser consultado por SQL. | GitHub Issues é o backlog persistente; handoff/manifest congelam escopo e capacidades; `state.json`, checkpoints e artefatos guardam o estado da tarefa. | Reusar estado e artefatos existentes. O tracker do Hive resolve coordenação de lotes homogêneos, mas criaria uma segunda fonte de verdade na plataforma. |
| Retomada | Estado de agentes e colônias é salvo em disco; playbook consulta o tracker para descobrir o trabalho ainda pendente e repete com retry/backoff/dead-letter. | O `ai-team` preserva etapa, plano, hashes e evidências; bloqueia retomada de estado incerto e já prevê reconciliação de checkpoints como P2. | Incorporar a disciplina de identificar o que está pendente por tarefa. Não repetir automaticamente uma chamada remota de efeito incerto. A retomada reconciliada existente é o lugar para isso. |
| Paralelismo | Quatro workers simultâneos por padrão; fila de workers adicionais. | O piloto de backlog executa uma tarefa por invocação. O lock atual é local por projeto; não coordena hosts. | Conservar execução serial no primeiro supervisor. Só avaliar concorrência entre repositórios distintos após medir recursos, quota agregada, isolamento, cancelamento e recuperação. Não compartilhar um mesmo working tree entre workers. |
| Aprendizado de procedimentos | O piloto pode produzir uma skill e um playbook para repetir o método em itens semelhantes. | Skills canônicas ficam no Kit, com snapshots de compatibilidade, validação e benchmark. O harness é publicado imutavelmente e produtos consomem releases fixados. | Não permitir que execuções alterem skills canônicas automaticamente. Uma futura proposta de skill/playbook deve derivar de tarefas repetidas com aceite, ser avaliada em fixtures e passar por revisão e distribuição versionada. Sem workload recorrente demonstrado, manter como hipótese condicional. |
| Modelos e papéis | Configurações distintas para queen e workers; worker pode usar outro modelo, mas a topologia é uma queen e clones. | Papéis explícitos: OpenAI planeja e valida; Claude implementa e revisa em sessão isolada. Não há roteador dinâmico; os modelos são verificados contra o catálogo da conta antes de consumir cota. | Manter a política por etapa da plataforma. Hive não oferece motivo para substituir a revisão independente por fan-out de agentes de mesmo papel ou para adicionar gateway. |
| Orçamento | Limites de turnos, chamadas de ferramentas e concorrência; o README informa que o produto não impõe limite monetário em dólares. | A plataforma controla ciclos e prazo e já lista budget monetário e custo por tarefa entre as capacidades pendentes. O custo precisa contemplar as quatro etapas, erros e revisão. | Priorizar o P2 de budget monetário já previsto. Limite de chamadas não substitui teto de gasto. Não importar os defaults numéricos do Hive sem workload e medição. |
| Segurança de execução | Terminal e MCP ampliam a superfície de ação; `cwd` é explicitamente descrito como diretório livre, não sandbox. O runtime local herda autoridade do usuário. | Implementação roda em container com ferramentas restritas; testes são offline, sem credenciais e sem volumes de contas; riscos R2/R3 e produção têm gates próprios. A documentação reconhece limites do isolamento. | Preservar a fronteira atual e não adotar o terminal do Hive como substituto do runner. Orçamento, confirmação e prompt não substituem isolamento do sistema operacional. |
| Implantação e estado | Aplicação local integrada, com arquivos sob `HIVE_HOME`, SQLite e componentes como dashboard, browser bridge e integrações. | Monorepo com donos separados (Kit, Harness, CLI, Engineering Team); runtime comum é embutido nos produtos via artefato imutável. Nenhum serviço central é obrigatório. | Não transformar Hive em dependência de runtime. Seu modelo local e integrado não corresponde ao contrato de produtos independentes e releases reproduzíveis. |

## O que já está coberto na plataforma

A comparação não deve virar backlog duplicado:

- **Pipeline por papéis e revisão separada:** `packages/engineering-team/docs/ISOLATED-AGENT-STAGES.md`.
- **Handoff e estado congelados por SHA, checkpoints, lock e detecção de falta de progresso:** `docs/AUTONOMOUS-PRODUCT-EVOLUTION.md` e `packages/engineering-team/scripts/local_team.py`.
- **Fila determinística, preview e promoção com triagem:** `docs/BACKLOG-CANDIDATE-QUEUE.md`, `docs/AUTONOMOUS-BACKLOG-CONTRACT.md` e `scripts/backlog_candidate_queue.py`.
- **Skills canônicas, avaliação e distribuição controlada:** `packages/kit/skills`, `packages/engineering-team/docs/SKILL-BENCHMARKS.md` e `packages/engineering-team/skills/README.md`.
- **Orçamento agregado do supervisor, métricas de autonomia, teto monetário e retomada reconciliada:** já constam como P1/P2 em `docs/AUTONOMOUS-PRODUCT-EVOLUTION.md`.

Essas capacidades ainda têm aceitação operacional pendente. Sua presença em código ou documentação não comprova um executor contínuo autenticado, limites de custo efetivos ou operação 24/7.

## Decisões de incorporação

### Incorporar como refinamento do trabalho já planejado

No **supervisor local de backlog autorizado (P1)**, aplicar a seguinte sequência:

1. Consultar apenas tarefas elegíveis e autorizadas; congelar issue, repositório, base SHA, escopo, critérios e limite agregado antes de iniciar.
2. Executar inicialmente **uma tarefa por vez**, reaproveitando fila, locks, handoff e estado por tarefa já existentes.
3. Gravar e expor o vínculo de cada execução com issue, run, etapa, tentativa, artefatos, checks e PR; manter o estado original como fonte de verdade, sem tracker paralelo.
4. Ao reiniciar, reconciliar a tarefa e os efeitos externos antes de tentar novamente. Estado ambíguo bloqueia replay automático.
5. Só ampliar concorrência depois do piloto autenticado provar cancelamento, budgets agregados, isolamento por repositório, retomada segura e observabilidade de custo.

Esse refinamento concretiza a intenção do P1 existente; não cria um novo componente nem uma nova issue de execução.

### Manter no roadmap existente

- **P0 – piloto autenticado ponta a ponta:** demonstrar execução real com evidência por issue/run/check/PR, revisão independente e custo medido.
- **P1 – supervisor:** seleção limitada, lock, cancelamento, allowlist e budget agregado.
- **P1 – métricas:** tempo, taxa de aceite, intervenções, custo por tarefa aceita, loops e retrabalho.
- **P2 – budget monetário e retomada reconciliada:** contabilizar falhas e as quatro etapas; tratar uso desconhecido como desconhecido, não como zero; não repetir operações remotas ambíguas.

### Não incorporar agora

- **Fan-out padrão de workers dentro de um mesmo produto ou checkout:** aumenta contenção e custo antes de provar que o supervisor serial é confiável. Concorrência entre repositórios pode ser reavaliada após medição.
- **Memória global adicional, tracker SQLite ou Event Bus novo:** a plataforma já tem issues, estado, eventos e artefatos com donos. Uma nova persistência repetiria responsabilidades.
- **Autoescrita/ativação de skills ou playbooks:** falta evidência de tarefas recorrentes e faltaria uma fronteira de aprovação e benchmark adequada para instruções que passam a afetar produtos.
- **Terminal e MCP permissivos do Hive:** o modelo de autoridade local não substitui os containers, ferramentas restritas, credenciais isoladas e gates de risco da plataforma.
- **Dashboard, browser bridge, personas comerciais e integrações de SaaS:** capacidades específicas da aplicação Hive sem uma lacuna demonstrada nos pacotes atuais.

## Recomendação final

A próxima entrega deve permanecer no fluxo de autonomia já adotado: provar o piloto, materializar o supervisor local serial com estado e limites rastreáveis, concluir métricas/custo/retomada e só então medir se existe caso para concorrência ou playbooks. Hive funciona como referência para execução longa e sistematização, mas sua arquitetura não deve ser copiada para o runtime da Product Platform.

## Fontes primárias

- [Hive README — execução, workers, tracker, limites e estado local](https://github.com/aden-hive/hive/blob/3ee47a3384ea5b3da0bed9a8e9284c7e9ebf987a/README.md)
- [Hive Architecture Overview](https://github.com/aden-hive/hive/blob/3ee47a3384ea5b3da0bed9a8e9284c7e9ebf987a/docs/architecture/README.md)
- [Hive: How a Colony Improves](https://github.com/aden-hive/hive/blob/3ee47a3384ea5b3da0bed9a8e9284c7e9ebf987a/docs/key_concepts/improvement.md)
- [Hive terminal execution](https://github.com/aden-hive/hive/blob/3ee47a3384ea5b3da0bed9a8e9284c7e9ebf987a/tools/src/terminal_tools/exec.py)
- [Product Platform: evolução autônoma](https://github.com/leandroclf/product-platform/blob/7a64095274b6d2b4c947395d7b99b5a3603ffbc1/docs/AUTONOMOUS-PRODUCT-EVOLUTION.md)
- [Product Platform: etapas isoladas](https://github.com/leandroclf/product-platform/blob/7a64095274b6d2b4c947395d7b99b5a3603ffbc1/packages/engineering-team/docs/ISOLATED-AGENT-STAGES.md)
- [Product Platform: contrato de backlog](https://github.com/leandroclf/product-platform/blob/7a64095274b6d2b4c947395d7b99b5a3603ffbc1/docs/AUTONOMOUS-BACKLOG-CONTRACT.md)
- [Product Platform: ownership do Harness](https://github.com/leandroclf/product-platform/blob/7a64095274b6d2b4c947395d7b99b5a3603ffbc1/packages/kit/contracts/product-harness-ownership.yaml)
