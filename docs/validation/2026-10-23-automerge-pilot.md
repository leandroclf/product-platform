# Piloto de revisão independente e automerge — 23/10/2026

Este registro é a sonda R1 do fluxo opt-in da Product Platform, após a integração
do PR #113. Não altera código, dependências, política ou infraestrutura.

## Preparação verificada

- Runtime operacional dedicado no commit `e25f022068eaf5c028c82e921dd85f33ce4b9d21`.
- Serviço local instalado e primeira consulta ao GitHub concluída com sucesso.
- Apps revisor e integrador distintos, sem bypass das regras da branch.
- Chaves no GitHub restritas aos environments da `main`; cópias gerais removidas.
- Timer ainda desativado no momento de criação deste piloto.

## Critérios de aceitação do piloto

1. O PR permanece bloqueado antes de aprovação independente no SHA atual.
2. A CI conclui e o serviço executa uma análise estática real em sessão isolada.
3. O App revisor publica o parecer validado, com SHA e hash da evidência privada.
4. Os gates são executados novamente; o App integrador solicita o merge nativo.
5. O merge só ocorre sob as regras e checks da branch. O resultado pode ser
   conferido no histórico do PR e nos runs associados.

O timer somente será habilitado após observar os cinco resultados. O fluxo
permanece limitado a R1 com label `agent-auto-merge`; alterações protegidas
continuam exigindo revisão e integração manual.
