# Resultado local do ciclo 1

Data de referência: 2026-10-06 (America/Sao_Paulo).
Tarefa: `product-platform-evolution-01`. Estado: implementação local validada nas
áreas alteradas, com falhas anteriores registradas e promoção ainda pendente.
Risco: R1 para código reversível; R2 para adoção da dependência compartilhada.
Na fase inicial de implementação não houve chamada de modelo, publicação externa,
commit, push, merge ou deploy. A entrega GitHub começou posteriormente: o harness
foi integrado pelo PR #3, no commit `a26110e6ebd967b3867f4e574b39918daebea040`,
com CI aprovado. O piloto foi publicado no PR #52 de vehicle-tracking com CI
aprovado; sua integração e promoção são acompanhadas separadamente.

## Entregas

1. Baseline dos quatro componentes e oito produtos, com SHAs, branch, working
   tree e resultados: [baseline-before.json](baseline-before.json).
2. Catálogo versão 2, domínio/proprietário de cada produto e fronteiras
   permitidas. `ai-docs` permanece apenas como referência histórica fora deste
   ciclo. Capacidades parciais explicitam primitives implementadas e trabalho
   planejado. Catálogo está em [portfolio-products.json](../../contracts/portfolio-products.json).
3. Contratos mínimos e decisões REUSE/EXTEND registrados em
   [phase-1.md](phase-1.md). Um corpus compartilhado com 11 casos verifica
   envelopes válidos, PII extra, metadados ausentes/inválidos e timestamps.
4. Candidato local `product-platform-harness` 0.2.0 com runtime Python de eventos,
   validação runtime de eventos em TypeScript/Python e artefatos compilados.
   Os SDKs antigos do kit ficam congelados para compatibilidade; a substituição
   de consumidores espera uma nova revisão publicada e validada.
5. `vehicle-tracking` consome um artefato distribuído do SHA remoto
   `ffb68c07dfbe491b804e3b59ad1e0ad791872e9e`, versão 0.1.0. Eventos, decisão de
   limite e sinal comercial delegam ao pacote. Autenticação, adapters de sinks,
   outbox e sua persistência mantêm a responsabilidade do produto.

O artefato do piloto não inclui as melhorias locais 0.2.0. O candidato novo
foi publicado como código-fonte no commit acima, sem tag ou release em registry,
e Bússola ainda não migrou seu adaptador Python.

## Verificação executada

| Área | Evidência observada |
| --- | --- |
| Kit | YAML parseável; catálogo/fronteiras e arquitetura aprovados; corpus canônico e snapshot iguais |
| Harness 0.2.0 | build, 4 testes TypeScript e 3 testes Python aprovados; ambas as linguagens usam os mesmos 11 casos |
| Distribuição Python | wheel instalado isoladamente; emissão e corpus aprovados fora do source package |
| Distribuição TypeScript | artefato 0.1.0 instalado em consumidor limpo com scripts desativados; import ESM nativo aprovado |
| Vehicle tracking | `pnpm run validate` completo aprovado: checksum/contrato, typecheck, 27 testes e build Next.js |
| Geofences | três testes novos da rota: bloqueio, filtro por identidade autenticada e falha de analytics/outbox preservando 403 |
| Diff e lint | `git diff --check` aprovado nos três repositórios alterados; ESLint dos arquivos TypeScript alterados aprovado |

Os testes da rota usam doubles para autenticação e banco; comprovam o filtro
solicitado e as respostas do handler, não isolamento real de banco nem reserva
atômica de quota. A decisão atual de entitlement é pura; concorrência exige
um trabalho separado de metering/reservas.

[verification-after.json](verification-after.json) registra a repetição de
checks nas áreas alteradas. Após esse registro, o candidato foi identificado
como 0.2.0 e o corpus ampliado para 11 casos; build/testes e instalação do wheel
foram repetidos com sucesso. O comando completo do consumidor também foi
executado após preservar as resoluções anteriores de peers no lockfile.

## Baseline dos demais repositórios

| Repositório | Resultado inicial |
| --- | --- |
| product-platform-cli | 72 testes e laboratório offline aprovados |
| product-platform-engineering-team | validadores estruturais e 114 testes unitários aprovados |
| lf-worldbank-risk-pricing | 78 testes aprovados; 1 ignorado pela suite existente |
| lf-openalex-enrichment-mvp | 43 testes aprovados |
| lf-wikidata-entity-graph | 43 testes aprovados |
| agentic-travel-engine | 27 testes aprovados |
| fivem-server-monitor-pro | verificador e 12 testes aprovados |
| professional-english-coach | check e 38 testes aprovados |
| bussola-financeira | 7 testes aprovados, 8 falhas de API com SQLite sem tabelas; teste de eventos aprovado separadamente |

## Pendências verificadas

- O validador de nomes aposentados falhava na baseline: havia referências ativas
  antigas e falsos positivos em comandos, configuração e tabela de migração.
  A correção de entrega atualiza referências ativas e adiciona regressões para
  exceções delimitadas. Os JSONs preservam os resultados históricos; o `$id`
  legado do contrato PaymentEvent permanece inalterado por compatibilidade.
- Os testes de API da Bússola instanciam `TestClient(app)` sem context manager,
  enquanto a inicialização do aplicativo ocorre em startup. Essa observação
  orienta a próxima regressão de lifecycle; a correção não foi aplicada neste ciclo.
- Aprovação por provedores independentes, integração com banco real, pagamentos
  reais e deploy não foram executados. Governança declarativa não é evidência
  de execução por agentes.
- Construções npm/Python ainda podem resolver dependências transitivas por ranges.
  Os checksums fixam estes artefatos, não prometem builds bit a bit reproduzíveis.

## Artefatos locais

Gerados em `/tmp/product-platform-harness-wheels/`; candidatos de validação,
não releases publicados. Regerar altera potencialmente hashes por metadados de
build; verificar os bytes antes de distribuição.

| Artefato | SHA-256 |
| --- | --- |
| `product_platform_harness-0.2.0-py3-none-any.whl` | `f882d058df4dd3bd87e211cd7a0fefbae45cdd783ff6d6fcd05464eaf0111663` |
| `leandroclf-product-platform-harness-0.2.0.tgz` | `e63eea6e28c46a304f6110f82f92560cd53d607998fed7abb574d74d4421a517` |
| Artefato 0.1.0 do piloto | `4a61b59c09fb4dfacd5e8297760e669035c1f01c5c315d15b37b4fd2b68bb79a` |

O tarball 0.1.0 está no `vendor/` do consumidor, com manifesto de origem e
checksum, dependência `file:` e integridade no lockfile. É um pacote compilado
do proprietário, não uma cópia editável das primitives no source do produto.

## Próximo marco

Regularizar a baseline isolada da Bússola, publicar uma revisão imutável do
candidato Python após revisão e migrar seu adaptador de eventos. Depois,
exercitar o handoff product-platform-cli → product-platform-engineering-team
com fingerprint do catálogo atualizado.
