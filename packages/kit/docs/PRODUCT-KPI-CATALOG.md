# Catálogo de KPIs — CI-01 v1

Incremento de #123. O catálogo define a semântica; `calculateKpi` no harness calcula agregados fornecidos pelo produto. Não coleta dados, não publica telemetria e não comprova baseline operacional. Sem novos eventos, serviços, dependências ou banco central.

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

Para concluir CI-01, selecionar um produto com fontes reais, registrar baseline e limitações, testar o adapter de agregação e obter revisão independente/checks. Nenhuma meta numérica é definida antes dessa baseline. Este incremento não altera ProductEvent, registry de capacidades, ledger ou o estado planejado do roadmap. Publicação e adoção exigem novo release imutável; não sobrescrever harness-v0.2.1.
