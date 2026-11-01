# Roadmap: operação empresarial conduzida por agentes

**Estado:** objetivo estratégico e plano; nenhuma capacidade de administração empresarial está declarada como implementada.
**Fonte de planejamento:** [issue #144](https://github.com/leandroclf/product-platform/issues/144).

## Objetivo

Usar a Product Platform para apoiar uma empresa em que agentes de IA realizem progressivamente a administração e a operação cotidiana, a evolução do portfólio e, quando houver autoridade jurídica e controles demonstrados, atos externos como comunicação, contratação e execução de contratos. A meta é reduzir a necessidade de gestores e funcionários humanos na operação diária.

Esse objetivo não atribui personalidade jurídica aos agentes nem remove automaticamente proprietários, membros, deveres legais, representação ou responsabilidade da entidade. A estrutura societária e as jurisdições precisam ser confirmadas antes de delegar atos externos. A proposta de AIC em Delaware não é lei vigente nem uma forma societária disponível enquanto não aprovada.

## Limite do estado atual

A plataforma hoje tem contratos e políticas no Kit, um executor isolado de engenharia no `ai-team`, runtime compartilhado parcial no harness, e gates de entrega G0–G6. A fila de backlog continua em `PREVIEW_ONLY`; criar issues, documentos ou instruções não mantém um worker ativo nem prova operação 24/7.

O objetivo empresarial amplia o uso esperado da plataforma, mas não expande automaticamente o escopo do executor de engenharia. Operações financeiras, contratuais e comunicações externas exigem domínio, identidade, autoridade e validação próprios.

## Princípios de arquitetura

1. Aplicar `REUSE > EXTEND > CREATE` e atualizar o registry somente com capacidades reais.
2. Não adicionar um segundo orquestrador, uma base de estado central ou um serviço obrigatório para produtos derivados.
3. Manter o `ai-team` como fluxo canônico de engenharia; não dar aos agentes de engenharia credenciais irrestritas de negócio.
4. Reutilizar harness events, commerce, economics/FinOps, outbox/inbox e observabilidade quando o domínio coincidir, preservando dados e adapters por consumidor.
5. Enforçar autoridade e limites na fronteira da ação, fora do prompt: identidade do agente, entidade, ferramenta, escopo, valor, vigência, delegação, política e estado.
6. Usar credenciais de privilégio mínimo, orçamento, idempotência, reconciliação, auditoria, revogação e kill switch.
7. Classificar ações por risco e efeito. A leitura e preparação de rascunhos podem ter autonomia maior; pagamentos, assinatura, obrigações legais, comunicação externa e produção requerem controles reforçados.
8. Não inventar métricas ou custos. Estabelecer baseline e cobertura antes de definir metas de eficiência.
9. Tratar modelos, runtimes e provedores como componentes substituíveis; a autoridade pertence à política da empresa e à entidade, não ao modelo.

## Fases e critérios de saída

| Fase | Prioridade / risco | Evolução | Critério de saída |
|---|---|---|---|
| 0. Charter e inventário | P0 / R0 | Confirmar entidade, jurisdições, sistemas, obrigações, contratos e processos; classificar fluxos por impacto, dados, efeito externo, valor e reversibilidade; obter pareceres jurídicos necessários. | Charter aprovado pelo proprietário, matriz de processos, perguntas legais e mapa REUSE/EXTEND/CREATE; custo e metas marcados como desconhecidos até medição. |
| 1. Autoridade e governança | P0 / provavelmente R2 | Contratos versionados de agente, identidade, papéis, escopos, ferramentas, limites monetários, delegação, expiração e revogação; decisões e escalonamentos rastreáveis. | Testes provam que política fora do prompt permite e bloqueia ações por entidade, agente, valor, escopo e estado; mudanças de política ficam auditáveis. |
| 2. Segurança operacional | P0 / R2 | Auditoria correlacionada, budgets por empresa/agente, timeout, cancelamento, proteção contra prompt injection, detecção de repetição, reconciliação de efeitos incertos e kill switch. | Cenários de falha e abuso testados; credenciais não aparecem em prompts/logs; revogação e pausa impedem novas ações. |
| 3. Estado da empresa e métricas | P1 / varia por integração | Relacionar objetivos, decisões, tarefas e eventos a fontes financeiras e operacionais verificáveis; aproveitar #123 e #102–#106 sem duplicar ledger ou declarar contabilidade oficial. | Um piloto tem fonte reconciliada, janela, cobertura, denominadores e owner; dados faltantes permanecem indisponíveis, não zero. |
| 4. Workflows internos | P1 / R1 | Piloto serial de leitura, análise, preparação de propostas e rascunhos em um processo e um produto/empresa. | Evidência real de qualidade, custo e intervenções; rollback/opt-out disponíveis; nenhuma ação externa não autorizada. |
| 5. Integrações empresariais | P1 / R2–R3 | Avaliar e integrar, por domínio, CRM, contabilidade, compras, assinatura eletrônica, pagamentos e comunicações. Não selecionar fornecedor antes de confirmar necessidade, entidade, cobertura e limites. | Cada adapter tem contrato, identidade, escopo mínimo, idempotência, reconciliação, auditoria, sandbox e rollback testados. |
| 6. Contratos e atos externos | Condicional / R2–R3 | Após validação jurídica, operar contratos com autoridade da entidade, contraparte e disclosure corretos, limites de valor/prazo/escopo, template aprovado e comprovante de aceitação. | Parecer aplicável, cenários sandbox e de falha aprovados; assinatura demonstrada por identidade autorizada; contestação e revogação operacionalizadas. |
| 7. Operação contínua | P2 / R2–R3 | Instalar executor disponível fora do notebook, autenticação, observabilidade, alertas, recuperação, orçamento e resposta a incidentes. Expandir por workflow medido. | SLOs e custo observados, incidente simulado com pausa/reconciliação, e histórico sustentando expansão. |

## Métricas de autonomia

Definir metas somente depois da baseline. No mínimo, medir:

- taxa de conclusão sem intervenção por workflow e severidade;
- intervenções, escalonamentos, reversões e ações incorretas;
- divergências de reconciliação financeira/contratual;
- tempo até conclusão e retrabalho;
- custo total por workflow concluído, incluindo falhas, modelos, ferramentas e infraestrutura;
- disponibilidade do executor, idade da fila e tempo de recuperação.

Uma taxa alta de execução automática não é sucesso se aumentar erros, disputas, custos ocultos ou exposição jurídica.

## Dependências já no backlog

- [#34 — auditoria e aceitação real do ai-team](https://github.com/leandroclf/product-platform/issues/34): evidência de execução de engenharia autenticada.
- [#58 — entrega, health checks e rollback](https://github.com/leandroclf/product-platform/issues/58): operação de runtimes e implantação.
- [#102–#106 — pagamentos, finanças e monetização](https://github.com/leandroclf/product-platform/issues/106): infraestrutura econômica/financeira compartilhada.
- [#123 — KPIs e baseline auditável](https://github.com/leandroclf/product-platform/issues/123): definição e primeira medição de indicadores.

Esses itens são dependências ou capacidades reutilizáveis, não tarefas substitutas para a operação empresarial. A criação deste roadmap ou de uma issue não inicia execução. Cada fase precisa de triagem própria, risco real, handoff, orçamento e gates G0–G6.

## Situação jurídica a acompanhar

A proposta AIC de Delaware é um possível caminho futuro, não uma licença atual para operar sem representação ou responsabilidade humana. A lei de Delaware atualmente reconhece contratos formados por agentes eletrônicos em transações automatizadas; isso não torna o agente pessoa jurídica. Uma corporation tradicional permanece sujeita a requisitos próprios de governança. Qualquer decisão de constituição, representação, assinatura, tributação, consumidor, privacidade ou trabalho deve ser validada por counsel nas jurisdições envolvidas.

Fontes e análises atuais devem ser registradas na issue #144; atualizar este roadmap quando houver texto legislativo promulgado ou parecer jurídico aplicável.
