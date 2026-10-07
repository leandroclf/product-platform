# Gate de virada: repositórios por pacote para o repositório da plataforma

Estende `docs/LEGACY-CUTOVER-GATE.md` para os quatro repositórios que viraram pacotes: `product-platform-kit`, `product-platform-harness`, `product-platform-cli` e `product-platform-engineering-team`. Arquivar é uma operação separada e reversível; apagar é outra operação, nunca coberta por este gate.

Um repositório antigo só pode ser arquivado quando todas as condições abaixo forem verdadeiras e verificadas.

| # | Condição | Estado em 2026-10-07 |
|---|---|---|
| 1 | `main` do repositório da plataforma contém o conjunto completo de fontes de cada pacote | Montado localmente com histórico preservado (1229 arquivos); **não enviado** ao GitHub |
| 2 | CI do repositório da plataforma verde em `main` (um workflow por pacote e `platform`) | **Pendente**: depende do envio; o equivalente local passou (fronteiras, kit, harness contra o corpus do kit, engineering-team 122 testes, cli 84 testes) |
| 3 | PRs abertos migrados ou rejeitados de forma explícita | Feito: harness PR 2 (artefato com checksum) migrado para `harness.yml`; cli PR 1 (bump de dependências) rejeitado, o dependabot do repositório novo o recriará se ainda se aplicar |
| 4 | Branches remotas relevantes migradas | Os 20 branches remotos do kit são históricos de trabalho já integrado em `main`; permanecem no repositório arquivado. Confirmar antes de arquivar |
| 5 | Nenhuma referência ativa ao repositório antigo | Links de issue e segurança do cli corrigidos; READMEs e guias usam nomes canônicos. Referências em documentos históricos datados foram preservadas de propósito |
| 6 | Instruções de instalação apontam só para o repositório novo | Pendente de revisão após o envio (URLs de clone) |
| 7 | Registry, ownership e boundaries usam nomes canônicos | Feito: `portfolio-products.json` mapeia os pacotes; `platform-packages.json` define o grafo |
| 8 | Nenhum deploy, release ou automação aponta para o repositório antigo | Pendente: nenhum release foi feito; o `vehicle-tracking` ainda fixa um artefato antigo do harness e deve migrar para uma release `harness-v*` |
| 9 | Segredos e dados pessoais fora do histórico importado | Feito: varredura em todas as revisões sem segredos reais; 105 arquivos `events.jsonl` (e-mail corporativo, caminhos locais) removidos do histórico importado |

## Antes de arquivar

- Conferir as condições 1, 2, 4, 6 e 8 após o envio.
- Os históricos antigos não são alterados nem apagados.
- Reverter: desarquivar o repositório antigo e descartar o repositório da plataforma ou parte dele, pois nenhum dado do original é removido.
