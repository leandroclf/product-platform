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
