# Gate de virada: repositórios por pacote para o repositório da plataforma

Estende `docs/LEGACY-CUTOVER-GATE.md` para os quatro repositórios que viraram pacotes: `product-platform-kit`, `product-platform-harness`, `product-platform-cli` e `product-platform-engineering-team`. Arquivar é uma operação separada e reversível; apagar é outra operação, nunca coberta por este gate.

Um repositório antigo só pode ser arquivado quando todas as condições abaixo forem verdadeiras e verificadas.

| # | Condição | Estado em 2026-10-07 |
|---|---|---|
| 1 | `main` do repositório da plataforma contém o conjunto completo de fontes de cada pacote | Cumprida: `leandroclf/product-platform` (privado) com histórico preservado, 4 pacotes em `packages/` |
| 2 | CI do repositório da plataforma verde em `main` | Cumprida: `kit`, `platform`, `harness`, `cli` e `engineering-team` verdes na `main`, no push e na execução manual (`workflow_dispatch`); o release `harness-v0.2.0` também passou. A validação local anterior achou 5 erros de ruff no cli e um tarball com testes compilados, ambos corrigidos |
| 3 | PRs abertos migrados ou rejeitados de forma explícita | Cumprida: harness PR 2 (artefato com checksum) migrado para `harness.yml`; cli PR 1 (bump de dependências) rejeitado, o dependabot do repositório novo cuida das atualizações |
| 4 | Branches remotas relevantes migradas ou descartadas de forma explícita | Cumprida: 26 branches com trabalho não integrado importadas como `legacy/<pacote>/<branch>` (kit 21, harness 3, cli 2), reescritas para `packages/<pacote>/` e sem segredos, e-mail corporativo ou `events.jsonl`. Branches do Dependabot não foram importadas de propósito |
| 5 | Nenhuma referência ativa ao repositório antigo | Cumprida para instruções, badges, metadados do pacote cli e `CONSUMING.md` do harness. Permanecem apenas documentos históricos datados e evidência de execução, preservados de propósito |
| 6 | Instruções de instalação apontam só para o repositório novo | Cumprida: clone de `leandroclf/product-platform` e `cd product-platform/packages/<pacote>` |
| 7 | Registry, ownership e boundaries usam nomes canônicos | Cumprida: `portfolio-products.json` mapeia os pacotes; `platform-packages.json` define o grafo |
| 8 | Nenhum deploy, release ou automação aponta para o repositório antigo | Cumprida: o único consumidor do harness, `vehicle-tracking`, adotou o release `harness-v0.2.0` (PR 53 mesclado, CI verde); os repositórios antigos não têm secrets, variáveis nem releases |
| 9 | Segredos e dados pessoais fora do histórico importado | Cumprida: varredura em todas as revisões do repositório e das branches `legacy/*`; 105 arquivos `events.jsonl` (e-mail corporativo, caminhos locais) ficaram fora do histórico importado |

## Ressalvas conhecidas

- O pacote Python do harness não é publicado como ativo do release; `docs/CONSUMING.md` do harness descreve o procedimento até isso existir.
- Os `events.jsonl` brutos só existem nos repositórios antigos. Arquivar os preserva; excluir os perde.
- PRs e issues dos repositórios antigos permanecem apenas lá.
- O PR 4 do Dependabot no repositório novo (dependências Python do cli) segue aberto.

## Exclusão

Não faz parte deste gate. Excluir apaga os PRs, os `events.jsonl` brutos e o histórico original dos repositórios antigos. O token do `gh` não tem o escopo `delete_repo`. Só excluir depois de arquivar, com um período de uso sem problemas e com confirmação explícita por repositório.

## Reverter o arquivamento

Desarquivar o repositório antigo (`gh repo unarchive`). Nenhum dado do original é removido por arquivar.
