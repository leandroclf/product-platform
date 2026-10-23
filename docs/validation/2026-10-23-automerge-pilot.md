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

## Resultado observado do primeiro piloto

O [PR #114](https://github.com/leandroclf/product-platform/pull/114) recebeu
[aprovação do App revisor no SHA atual](https://github.com/leandroclf/product-platform/pull/114#pullrequestreview-5624127112).
O serviço instalado produziu uma avaliação estática real, com schema, SHA e hash
da evidência privada. Os dois runs do gate terminaram com sucesso.

O [run de integração 39903920442](https://github.com/leandroclf/product-platform/actions/runs/39903920442)
concluiu todos os passos; o merge foi realizado por
`leandroclf-pp-integrator[bot]` no commit
`49b68e11ddb8d22f0b9aedc4a9b775bded4ed19d`. O operador não executou o merge desse PR.

O primeiro piloto revelou solicitações automáticas simultâneas para o mesmo SHA.
O [PR #115](https://github.com/leandroclf/product-platform/pull/115) serializou
esses eventos sem cancelar uma integração em andamento. Dispatch manual de
recuperação deve ser usado sem uma integração automática simultânea, pois usa
um grupo distinto.

Esta atualização documenta somente resultados já observados. Sua própria
revisão será iniciada pelo timer periódico instalado, sem iniciar manualmente o
serviço. O resultado pode ser auditado no PR desta atualização e nos runs
associados; não constitui evidência de deploy ou de login dos candidatos do
laboratório.
