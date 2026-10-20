# Isolated plan

Plan ID: 468996f64d814e4fda6a728650ffbb72c90b5297272c740ba2e2c5c8774b3c57
Planning HEAD: 12d1886f4609eeb89fbe3c6da46859b0adc1d35a
Risk: R0

## Assumptions

- O escopo documental informado pelo pedido original prevalece sobre o procedimento geral do AGENTS.md: a edição ficará restrita à seção indicada.
- Não há /handoff/proposal.json nem /handoff/rules.json; os arquivos não estavam presentes no handoff.

## Validation

- Comparar o diff para confirmar que somente o trecho documental autorizado mudou.
- Conferir a coerência do texto com packages/engineering-team/AGENTS.md e packages/engineering-team/docs/CAPABILITY-RESOLUTION-GATE.md.
- Revisar o exemplo de chamada local para confirmar que omite --handoff e é sintaticamente coerente com a interface documentada.
