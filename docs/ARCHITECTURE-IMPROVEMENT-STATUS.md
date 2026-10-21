# Aplicação da revisão arquitetural de 20/10/2026

Base: `e4330be0f295877dd55ed74dbdccd04f2b9398d8`. Este registro separa
implementação, evidência local e aceitação operacional. Nenhum status equivale
a autorização de produção ou prova de ganho comercial.

## Mudanças implementadas neste lote

- Fronteiras reconhecem nomes reais de distribuição e módulos, imports literais,
  manifests aninhados/optional-dependencies/requirements e ciclos. Aliases ficam
  no grafo; nomes adicionais são descobertos nos manifests. Regressões incluem
  dependência proibida do harness em `omnicli` (#89), nomes normalizados,
  subpaths JS e casos permitidos. Não é um sandbox ou análise de imports gerados.
- Mapeamento físico do portfólio inclui o Design System; teste mantém paridade
  entre os cinco caminhos e o grafo, preservando os quatro IDs históricos de
  papéis usados pelo contrato de handoff. Nenhum novo produto foi incluído por inferência.
- Readiness da Bússola reconhece que o CI já inclui ingestão; o histórico do
  bloqueio bwrap foi preservado, sem atribuir sucesso a uma jornada não executada.
- ADR 004 deixa de congelar visibilidade e contagem antiga do catálogo.
- Kit e Design System têm build/install local por versão, checksum e manifest
  com origem e hashes por arquivo. Instalação rejeita adulteração, traversal,
  symlink e destino existente. Não publica nem troca políticas de consumidores.
- Piloto determinístico de consumo compara cada arquivo instalado à origem.
  Snapshots do engineering-team permanecem até a adoção real com precedência e
  rollback. Não se confunde paridade de bytes com comportamento seguro de LLM.
- Comparação dos workspaces e dos serviços de entrega foi aprofundada em código
  e decisões registradas em `REPOSITORY-CONSOLIDATION.md`.

## Lote protegido de release (separado)

A correção de #88 precisa executar `scripts.test_build_release_manifest` a partir
da raiz, congelar a instalação Node com `npm ci` e o build Python sem isolamento
que reinstale dependências flutuantes. O workflow deve registrar toolchain no
manifest e testar sua própria invocação offline antes de publicar.

Mudanças em `.github/workflows/**` são bloqueadas pelo `independent-review-gate`
atual, inclusive no modo manual. Este lote deve passar pela política específica
sem bypass e sem tornar o check opcional. A aprovação de implementação não pode
ser apresentada como resultado verde de um check que rejeitou o diff.

## Evidência administrativa observada

Ruleset `main-autonomy-minimum`, ID 25445834: ativo para main, sem bypass; exige
`boundaries`, `offline-safety-tests`, `independent-review-gate`; proíbe deletion e
non-fast-forward. Exige zero aprovações, sem dismiss de reviews antigas e sem
last-push approval. Portanto checks são exigidos, mas revisão humana independente
não é imposta por esse ruleset. Leitura é evidência de configuração, não teste de
que todo merge é bloqueado corretamente. #75 continua dependente dessa prova.

Fonte: https://github.com/leandroclf/product-platform/rules/25445834

## Recomendações mantidas e gates concretos

| Tema | Aplicação / decisão | Conclusão ainda necessária |
|---|---|---|
| Núcleo | Monorepo e produtos separados, sem gateway novo | Manter enforcement e releases por pacote |
| AICP/ClawTeam | Experimentos sem dependência de execução do ai-team | Workload e benchmark que justifiquem qualquer integração |
| Workspaces | Comparação de arquivos e classificação explícita | Inventário de usos locais antes de arquivar/remover |
| ai-hub/protokit | Fronteiras e invariantes comparadas; sem copiar fonte | Contrato e migração de consumidores antes de descontinuar serviço |
| Agentes de domínio | Permanecem nos produtos | Nenhuma substituição pelo ai-team |
| OpenClaw | Imagem e estado operacional separados conceitualmente | Inventário do host, retenção e consumidores reais |
| Skills | Bundle local e roundtrip | Consumo no runtime autenticado antes de remover snapshots |
| Design | Bundle local, opt-in | Aceite visual nos produtos e licença antes de publicação externa |
| Release | Correção/testes no lote protegido | Política de segurança e CI verde antes do merge/publicação |
| Entrega | Preservados adapters/contratos existentes | Staging segregado, health e rollback reais por família (#58) |
| Portal | Preservado como publicação editorial | Credencial mínima, revisão e fluxo cross-repo efetivo (#60) |
| Runtime compartilhado | Registry continua parcial | Inbox/outbox/metering somente quando workload exigir |
| Outros produtos | Sem adesão automática ao catálogo | Definir dono e motivo de adoção antes de integração |

## Bloqueios externos à edição de código

Este ambiente não oferece Docker, Codex CLI nem Claude Code CLI autenticados.
Não pode executar a aceitação real de quatro etapas (#34), provar sessões,
expiração/retomada e custos reais, operar o host OpenClaw ou testar staging com
segregação de credenciais. Também não há credencial administrativa exposta para
alterar rulesets; nenhuma configuração foi relaxada para possibilitar merge.

Não declarar esses itens concluídos por adicionar documentação ou mocks. Não
implementar inbox, outbox, billing, CRM ou roteamento antecipadamente: a revisão
recomenda explicitamente evolução sob demanda, não criar todas as capacidades
planejadas. Não arquivar, excluir, forçar push ou fazer migração de dados por
semelhança de nomes.

## Evidência de integração desta execução

- PR [#90](https://github.com/leandroclf/product-platform/pull/90) mergeado em `7d2cc5ffe26e884df72fe2cec2b116853aa7571c`: correção de #89, bundles, catálogo e decisões. Os seis workflows do PR passaram.
- PR [#91](https://github.com/leandroclf/product-platform/pull/91) mergeado em `3be88e09200fcc3e53a2f4a602e60e4780edf817`: restauração de trecho documental truncado na transferência. Comparação dos 14 blobs identificou somente aquele arquivo divergente; os demais correspondiam à cópia testada.
- Main integrada passou no [Post-merge main integrity](https://github.com/leandroclf/product-platform/actions/runs/39522362153), platform, kit e offline-safety-tests.
- PR [#92](https://github.com/leandroclf/product-platform/pull/92), head `73c2fdea455577d61f11c0ed3c8fda31d32fad38`, implementa a correção de release #88 e toolchain. Passaram seis regressões locais de release, build, quatro testes TS, três Python, geração de tarball/wheel e manifest com versões. O [harness CI remoto](https://github.com/leandroclf/product-platform/actions/runs/39522297406) passou. O [gate obrigatório](https://github.com/leandroclf/product-platform/actions/runs/39522297497) rejeitou o workflow protegido; a API do PR informou `mergeable_state=blocked`. Não houve bypass nem tentativa de declarar o gate aprovado. #88 permanece aberta.
- Ajustes documentais também foram mergeados em [agentesautonomos #6](https://github.com/leandroclf/agentesautonomos/pull/6), [claude-workspace #1](https://github.com/leandroclf/claude-workspace/pull/1), [agentic-travel-engine #8](https://github.com/leandroclf/agentic-travel-engine/pull/8), [lf-openalex #8](https://github.com/leandroclf/lf-openalex-enrichment-mvp/pull/8), [lf-worldbank #6](https://github.com/leandroclf/lf-worldbank-risk-pricing/pull/6), [ai-hub #4](https://github.com/leandroclf/ai-hub/pull/4) e [pshhospitalar #2](https://github.com/leandroclf/pshhospitalar/pull/2). Os três produtos com CI de PR ativo concluíram com sucesso; nos quatro demais não houve run de PR retornado. Não afirmar testes executados onde não houve execução.

Validação local do lote #90: 11 testes de fronteiras; 108 testes de segurança/contratos/bundles; 28 de handoff integrado; 46 do validador de handoff; paridade de 13 skills; cinco testes de tokens/ativos; arquitetura e conformance ProductEvent. Testes controlados não encerram os gates externos descritos acima.

**Estado global: parcial, com bloqueios reais.** A autorização do operador para aplicar e mergear está registrada na solicitação; não falta uma confirmação genérica. Faltam política válida para workflows protegidos, acesso administrativo correspondente e ambiente autenticado/segregado para os pilotos. Não transformar esses requisitos em check opcional, aprovação própria ou evidência fictícia.
