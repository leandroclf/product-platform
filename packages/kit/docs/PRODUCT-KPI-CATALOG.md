# Catálogo de KPIs — CI-01 v1

Incremento de #123. O catálogo define a semântica; o harness calcula agregados fornecidos pelo produto com `calculateKpi` (TypeScript, export da raiz `@leandroclf/product-platform-harness`) e `calculate_kpi` (Python, `product_platform_harness`), com resultados equivalentes verificados pelos casos compartilhados `fixtures/kpi-cases.json`. Não coleta dados, não publica telemetria e não comprova baseline operacional. Sem novos eventos, serviços, dependências ou banco central.

## Contexto obrigatório

Cada cálculo identifica fonte auditável, janela `[windowStart, windowEnd)` com timezone e cobertura `complete` ou `partial`. O consumidor seleciona uma única coorte de produto/ambiente, deduplica registros e reconcilia as fontes antes de agregar. A função valida números e contexto, mas não verifica a veracidade da fonte nem filtra registros. IDs pessoais e credenciais não pertencem ao contexto. Retenha evidências detalhadas no sistema de origem com acesso apropriado.

`null/missing_data` significa fonte ausente; `null/empty_denominator`, nenhuma observação elegível. Zero só representa resultado observado. Cobertura parcial acompanha todo resultado, inclusive zero; não extrapolar para o portfólio. Valores monetários pertencem a uma única moeda explícita; converter/reconciliar antes, nunca somar moedas. Médias em unidades mínimas podem ser fracionárias e não servem para liquidação financeira.

## Definições

| ID no harness | Fórmula e unidade | Fonte e coorte | Limites |
| --- | --- | --- | --- |
| `lead_time_ms` | Média de `acceptedAt - executionStartedAt`, milissegundos | Histórico de execução e aceite; entregas aceitas na janela | Incluir início anterior à janela; rejeitar duração negativa; relatar WIP separadamente para evitar viés de sobrevivência |
| `change_failure_rate` | Deploys com incidente/rollback/remediação ÷ deploys | Receipts G6 + vínculo com incidentes; deploys realizados na janela | Cada deploy conta uma vez; falha de CI não é incidente de deploy; definir horizonte de acompanhamento e marcar parcial enquanto aberto |
| `cost_per_delivery_minor` | Custo atribuível de IA/CI/infra ÷ entregas aceitas | Custos reconciliados atribuídos à mesma coorte de entregas aceitas | Incluir custo da coorte fora da janela; declarar custos não atribuídos e cobertura; não confundir custo parcial com TCO |
| `acceptance_rate` | Entregas aceitas ÷ entregas submetidas | Critérios de aceite versionados e histórico; submissões na janela | Deduplicar reenvios por entrega; pendências ficam no denominador e cobertura parcial até decisão final |
| `contribution_margin_minor` | Receita líquida − custos variáveis atribuíveis | Ledger reconciliado e custos por produto na janela | Receita líquida já desconta taxas/impostos definidos pelo ledger; não descontar duas vezes; negativo é válido; não equivale a lucro/TCO |
| `validated_demand_rate` | Hipóteses confirmadas ÷ hipóteses avaliadas | Registro de experimentos/clientes com critério prévio e evidência; avaliações concluídas na janela | Inconclusivas contam no denominador; não inferir PMF, TAM, CAC ou LTV; não contar entrega técnica como demanda |

## Adoção e saída deste incremento

Os contadores devem ser inteiros seguros não negativos; numeradores de taxas não excedem a coorte. O harness rejeita inconsistências em vez de ajustar silenciosamente. `durationsMs` contém durações inteiras de entregas aceitas. O consumidor calcula esses deltas a partir de timestamps auditáveis.

Para concluir CI-01, selecionar um produto com fontes reais, registrar baseline e limitações, testar o adapter de agregação e obter revisão independente/checks. Nenhuma meta numérica é definida antes dessa baseline. Este incremento não altera ProductEvent, registry de capacidades, ledger ou o estado planejado do roadmap. Publicação e adoção exigem novo release imutável; não sobrescrever harness-v0.2.1. As funções existem no checkout local; não se afirma que integrem o artefato `harness-v0.2.1` publicado.

## Estado da baseline real: parcial

A primeira baseline real de CI-01 **segue parcial**: nenhum KPI tem medição operacional registrada. As evidências disponíveis são técnicas — fórmulas deste catálogo, `calculateKpi`/`calculate_kpi`, casos sintéticos em `fixtures/kpi-cases.json` e os checks do harness. Esses casos (`source: fixture-only`) não são observações de produto e não devem ser citados como baseline, zero observado ou meta. A baseline histórica de validação da plataforma não mede estes KPIs. Até haver evidência, cada KPI é “não disponível”; não registrar zero nem inferir valores.

Pendências comuns a todos os KPIs: escolher um produto e um ambiente; fixar janela `[windowStart, windowEnd)` com timezone; definir a coorte e a deduplicação; reconciliar as fontes; declarar a cobertura; implementar e testar o adapter de agregação do consumidor; obter revisão independente da primeira medição.

### Auditoria do primeiro candidato: Bússola Financeira (2026-10-31)

A Bússola é um candidato da primeira onda e já consome o harness, mas as fontes
inspecionadas não sustentam ainda uma medição CI-01. O checkout `main` estava no
SHA `f2bd971f907362d494596f47c5fb3f29c7444626` (commit de 2026-10-15). O CI
`38725202794` concluiu em 2026-10-15T11:08:43Z; essa execução valida código e
artefato, não é entrega de produto nem fonte de custo reconciliado. A API GitHub
de deployments retornou zero receipts para o repositório na consulta de
2026-10-31; isso não cobre deployments feitos por outros provedores.

No código, `/metrics` expõe `http_requests_total` e
`http_request_duration_seconds`; esses contadores não registram início/aceite
de entregas nem estão vinculados a uma coorte CI-01. O evento
`feedback_submitted` registra envio de feedback, não hipótese validada com
critério prévio. Nenhuma consulta a dados de runtime, financeiros ou de clientes
foi feita.

| KPI | Resultado neste snapshot | Evidência que falta |
| --- | --- | --- |
| `lead_time_ms` | Não disponível | Registro auditável de início de execução e aceite por entrega, com WIP da mesma janela |
| `change_failure_rate` | Não disponível | Receipts de deployments por provedor, vínculo com incidentes/rollback e horizonte de acompanhamento |
| `cost_per_delivery_minor` | Não disponível | Custos reconciliados de IA, CI e infraestrutura, atribuídos às mesmas entregas e em uma moeda |
| `acceptance_rate` | Não disponível | Histórico versionado de submissões e decisões de aceite, incluindo pendências e deduplicação |
| `contribution_margin_minor` | Não disponível | Ledger financeiro reconciliado e custos variáveis atribuíveis ao produto |
| `validated_demand_rate` | Não disponível | Registro de experimento com hipótese, critério definido antes da avaliação e resultado evidenciado |

O snapshot não define janela de medição nem escolhe oficialmente o produto para
a baseline; portanto não cria observações, zeros ou cobertura para qualquer
KPI. A próxima execução exige selecionar produto/ambiente e obter acesso às
fontes operacionais correspondentes. A issue #123 permanece aberta.

| KPI | Evidência real disponível | Pendências específicas |
| --- | --- | --- |
| `lead_time_ms` | Não disponível | Fonte auditável de `executionStartedAt` e `acceptedAt` por entrega; incluir inícios anteriores à janela; relatar o WIP (entregas não aceitas) separadamente |
| `change_failure_rate` | Não disponível | Receipts G6 vinculados a incidentes, rollbacks e remediações; horizonte de acompanhamento de incidentes; marcar parcial enquanto houver deploys em observação; não contar falhas de CI |
| `cost_per_delivery_minor` | Não disponível | Custos de IA/CI/infra reconciliados e atribuídos à coorte, em uma única moeda; declarar custos não atribuídos e a cobertura; não apresentar como TCO |
| `acceptance_rate` | Não disponível | Critérios de aceite versionados e histórico de submissões; deduplicar reenvios; manter decisões pendentes no denominador com cobertura parcial |
| `contribution_margin_minor` | Não disponível | Ledger reconciliado por produto, com receita líquida e custos variáveis atribuíveis na mesma moeda; evitar dupla dedução de taxas/impostos |
| `validated_demand_rate` | Não disponível | Registro de hipóteses com critério prévio e evidência de demanda comprovada; avaliações inconclusivas no denominador; entrega técnica não conta como demanda |

A revisão local de paridade, documentação e checks não conclui CI-01. A conclusão exige a primeira medição real com as pendências acima resolvidas e a adoção via release imutável.
