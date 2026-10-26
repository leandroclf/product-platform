# Roadmap: decisão, eficiência e melhoria contínua de produtos

**Estado:** planejamento; nenhuma funcionalidade desta evolução está declarada como implementada. **Data:** 2026-10-25.

## Objetivo
Ampliar o ciclo atual da Product Platform para **oportunidade → qualificação → priorização → implementação → validação → operação → aprendizado**, guiado por evidências e resultados econômicos. Reutilizar exclusivamente os donos canônicos (`kit`, `cli`, `engineering-team`, `harness`) e o fluxo G0–G6. Não criar serviços, gateways, orquestradores ou dashboards extras sem benefício demonstrado.

## Conceitos e aplicação

- **Estratégia:** GUT para urgência e risco, combinada com impacto/esforço/custo; KPIs auditáveis; SWOT/TAM e ROI como hipóteses; OKRs quando houver metas definidas.
- **Pessoas e cultura:** 1:1, CNV, feedback 360°, PDI e EX aplicados a colaboradores, operadores e experiência do desenvolvedor conforme pertinência; evitar antropomorfizar agentes.
- **Crescimento:** Kaizen e PMF como hipóteses e ciclos de experimentação; CAC e LTV somente com dados reais de aquisição, retenção e coortes.
- **Execução:** Kanban, limites de WIP, 5W2H, PDCA e RACI, sem sobrepor o fluxo de agentes existente.
- **Finanças:** margem de contribuição e TCO por produto como primeiros resultados; EBITDA/ROA/ROE somente com dados contábeis e maturidade necessários.

## Backlog priorizado

| ID | Fase | Prioridade | Entrega / dono | Aceite |
| --- | --- | --- | --- | --- |
| CI-01 | Fundação | P0 | Catálogo de KPIs no `kit`, instrumentação no `harness` | Fórmulas, fontes, janelas, denominadores, ausência de dados, testes; lead time, change failure rate, custo por entrega, taxa de aceitação, margem e validação de demanda |
| CI-02 | Fundação | P0 | Priorização auditável no `kit`/`engineering-team` | GUT + impacto, esforço, custo, dependências e risco; pesos explícitos, justificativa, override e testes determinísticos; GUT não é decisão isolada |
| CI-03 | Fundação | P0 | WIP e budget no `engineering-team` | Limites por produto/execução, concorrência, custo e retries; cancelamento, idempotência, bloqueios e retomada testados |
| CI-04 | Economics | P1 | TCO e margem no `harness` | Separar receita líquida, taxas, custo variável, custo fixo/compartilhado, IA/CI/cloud; regras de rateio e reconciliação; sem CAC/LTV especulativos |
| CI-05 | Descoberta | P1 | Qualificação de proposta no `cli` e contrato no `kit` | Problema, segmento, hipóteses, riscos, evidências, 5W2H, SWOT/TAM/ROI opcionais, handoff validado e versionado; PMF não presumido |
| CI-06 | Aprendizado | P1 | PDCA/Kaizen no `engineering-team` via eventos existentes | Comparação com baseline, sugestões de melhoria deduplicáveis com evidências, revisão independente e gates antes de merge/deploy |
| CI-07 | Governança | P2 | OKRs, responsabilidades RACI e EX no `kit` | Objetivos ligados a métricas e decisões; responsabilidades claras: Atlas planeja, Claude implementa, OpenAI valida, Claude revisa isoladamente; operador aprova conforme políticas |

## Definições operacionais iniciais

1. **Lead time:** diferença entre entrada em execução e entrega aceita; registrar timestamps.
2. **Change failure rate:** deploys que geraram incidentes/rollback/remediação ÷ deploys da janela; não confundir com falhas de CI.
3. **Custo por entrega:** gasto atribuível em IA, CI e infraestrutura; explicitar custos não atribuídos e cobertura.
4. **Taxa de aceitação:** entregas aceitas nos critérios previamente definidos ÷ entregas submetidas.
5. **Margem de contribuição:** receita líquida menos custos variáveis atribuíveis; diferente de lucro e TCO.
6. **Demanda validada:** hipóteses comerciais confirmadas por evidências de experimentos ou clientes; não afirmar PMF com entrega técnica.

Registrar métricas ausentes como “não disponível”; não inventar zeros nem metas antes da baseline.

## Fases e critérios de saída

1. **P0:** instrumentar baseline, política de priorização e limites operacionais; passar conformance, testes de contrato/handoff e cenários de falha.
2. **P1:** validar custos por produto e propostas comerciais em piloto único, com rollback e compatibilidade com ProductEvent.
3. **P1:** gerar propostas de melhoria verificáveis a partir de resultados, sem autoaprovação e sem duplicar issues.
4. **P2:** ligar resultados a objetivos somente após benefício operacional comprovado.

Cada incremento exige deduplicação do backlog, issue rastreável, testes automatizados, PR, checks e evidências de aceitação. Seguir [PLATFORM-DELIVERY-FLOW.md](PLATFORM-DELIVERY-FLOW.md) e [PLATFORM-READINESS.md](PLATFORM-READINESS.md); os gates de revisão, merge, deploy e segurança existentes permanecem.

**Fora de escopo:** 25 módulos separados, gateway adicional, reescrita do harness, avaliação humana simulada para agentes, novo orquestrador, auto-merge baseado em score e métricas financeiras sem contabilidade confiável.
