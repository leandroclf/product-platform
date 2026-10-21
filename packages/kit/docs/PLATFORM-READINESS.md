# Baseline e próximas etapas da plataforma

Verificação iniciada em 2026-10-14, sobre `main` em `3a49cc1d38c985cd16b8067faa2f63cb37521ecb`.
Os resultados abaixo são verificações locais, salvo a consulta explícita da release no GitHub.
O fluxo normativo permanece em [PLATFORM-DELIVERY-FLOW.md](PLATFORM-DELIVERY-FLOW.md).

## Atualização da revisão arquitetural (2026-10-20)

O workflow atual de `bussola-financeira/.github/workflows/ci.yml` já executa
`tests/test_ingestion_integrity.py`, além dos eventos e verificação do artefato.
Isso substitui a pendência de edição do workflow descrita na evidência histórica abaixo.
Não comprova, por si só, o último CI remoto nem aceitação de uma execução autenticada
de quatro etapas. O bloqueio `bwrap` registra aquela tentativa histórica, não o estado
de todas as execuções futuras. Ver `docs/ARCHITECTURE-IMPROVEMENT-STATUS.md` na raiz
para resultados, limitações e itens dependentes de ambiente.

## Sequência de execução

| Etapa | Estado | Critério de conclusão |
| --- | --- | --- |
| 1. Consolidar a baseline | Concluída | Checks dos quatro pacotes executados, divergências documentais corrigidas e limitações registradas |
| 2. Validar a jornada completa | Escopo autorizado pelo operador; execução bloqueada no sandbox do planejamento | Proposta autenticada, revisão humana, envelope validado, execução isolada e entrega com evidências |
| 3. Piloto na Bússola Financeira | CI de ingestão implementado; aceitação autenticada da jornada ainda pendente | CI passa a executar os testes determinísticos de ingestão existentes, preservando os checks de eventos e artefato |
| 4. Padronizar G3 | Pendente | Checks de conformidade padronizados e validação de contratos por schema, incluindo pagamentos |
| 5. Evoluir o harness | Sob demanda do produto | Implementar somente a capacidade comprovadamente necessária, no dono canônico |
| 6. Operação e releases | Parcial | Artefatos publicados; instalação, atualização, rollback e cenários de falha ainda exigem aceitação |
| 7. Expandir adoção | Após o piloto | Workloads delimitados de três famílias de produtos, conforme o roadmap do time de engenharia |

## Evidência já obtida

| Área | Comando ou fonte | Resultado |
| --- | --- | --- |
| Fronteiras | `python3 scripts/test_check_package_boundaries.py` e `python3 scripts/check-package-boundaries.py` | 6 testes; grafo válido |
| Handoff entre pacotes | `python3 scripts/test_handoff_contract.py` | 4 testes; envelope do CLI validado pelo kit e aceito pelo `ai-team`, com rejeição de registry/base defasados |
| Kit | `node scripts/validate-architecture.cjs`, `python3 scripts/conformance-product-event.py`, `python3 scripts/validate-platform-handoff.test.py` | Passaram; 4 testes de nomes aposentados e 5 de handoff |
| Harness | `npm run validate` | Build, 4 testes TypeScript e 3 testes Python passaram contra o corpus canônico |
| CLI, após os ajustes | `pytest --cov=omnicli --cov-report=term`, `ruff check .`, `mypy` | 104 testes passaram; cobertura de 82%; lint e tipos passaram |
| CLI, operação offline | `pip check`, `omnicli lab verify --json`, `omnicli conceive ... --dry-run --json`, `omnicli doctor --offline --json` | Passaram; laboratório sintético não certifica compatibilidade autenticada |
| CLI, distribuição e dependências | `python -m build --outdir /tmp/product-platform-cli-build-20261014` e `pip-audit` na venv | Wheel e sdist gerados; auditoria sem vulnerabilidades conhecidas após atualizar o pip da venv; o pacote local `omnicli` não é auditável pelo índice |
| Time de engenharia | `python3 -m unittest discover -s tests/unit` e `python3 -m unittest discover -s tests -p 'test_*.py'` | 128 + 23 testes passaram |
| Governança do time | Validadores de framework, hardening, operações nativas, documentação, skills, avaliações e benchmarks definidos no CI | Passaram; também passou `docs/anexos/build/verificar_docs.py` |
| Canários Docker | `local_isolation_smoke.py` e `local_stage_isolation_smoke.py`, imagem `ai-eng-provider-cli:local` | Passaram após ajuste do canário de etapas; rede/credenciais ausentes nos checks, origem preservada e mounts protegidos nas quatro etapas; verificado também sem RTK |
| Baseline do piloto | `PYTHONPATH=src DATABASE_URL=sqlite+pysqlite:///:memory: python -m pytest -p no:cacheprovider tests/test_ingestion_integrity.py tests/test_product_events.py -q` e `python scripts/validate_harness_artifact.py`, na venv do produto | 6 testes passaram (2 de ingestão + 4 de eventos), 26 avisos de depreciação de `utcnow`; artefato verificado; checkout permaneceu limpo |
| Piloto no runner real de checks | `local_team.test_command` com `bussola-tests:pilot-20261014`, sem rede, contas ou socket Docker, origem somente leitura | Artefato verificado e os mesmos 6 testes passaram; o canário de isolamento também passou com essa imagem |
| Release | `gh release view harness-v0.2.1 --repo leandroclf/product-platform --json tagName,isDraft,isPrerelease,publishedAt,assets` | Publicada em 2026-10-07, sem draft/prerelease; tarball, wheel e `SHA256SUMS` presentes |

Os ambientes iniciais não tinham `tsc` nem `pytest`. Foram instaladas apenas as dependências
já declaradas: `npm ci` no harness e extras de desenvolvimento do CLI em uma venv temporária.
Nenhum manifest de dependências foi alterado.

## Correções descobertas na execução

- O modo `--project` do CLI executa os provedores em diretório temporário. A configuração do
  Codex não permitia execução fora de Git, causando falha em `critical-review`. As configurações
  padrão e de exemplo agora usam `--skip-git-repo-check`; o sandbox não foi alterado.
- O canário de etapas exigia home vazio, mas o executor já monta `.codex/AGENTS.md` somente
  leitura quando RTK está disponível. O canário aceita apenas esse arquivo e também testa sua
  proteção contra escrita; arquivos de conta continuam proibidos.
- A documentação misturava estados anteriores com o envelope completo já implementado e a
  release já publicada. Esses trechos foram reconciliados com código, tags e manifestos dos consumidores.

## Ambiente e limites

- Docker Desktop recusou mounts de `/tmp`. Os canários passaram com `TMPDIR` apontando para
  `.venv/validation-tmp` neste checkout, já ignorada pelo Git. Nenhuma configuração do daemon foi alterada.
  A execução real precisa manter estado/workspaces em um caminho compartilhado com Docker.
- `ai-team doctor` encontrou imagem, ferramentas e quatro logins salvos, mas retornou a aceitação
  dos provedores como `INCONCLUSIVE`. Isso não comprova validade da sessão ou acesso ao modelo.
- No host, `omnicli doctor --capabilities --json` reconheceu Claude `2.1.281` e Codex `0.162.1`.
  A imagem do `ai-team` declara Claude `2.1.287` e Codex `0.159.3`; são ambientes distintos.
- Ainda faltam benchmark humano, matriz completa autenticada e cenários reais de interrupção,
  retomada, sessão expirada e falha do provedor. A baseline não certifica produção autônoma.

## Piloto delimitado

Artefatos para revisão: [proposta gerada](../../cli/artifacts/pilots/bussola-ci-20261014/proposta.md),
[envelope validado](../../cli/artifacts/pilots/bussola-ci-20261014/handoff.json) e
[evidência resumida](../../cli/artifacts/pilots/bussola-ci-20261014/evidence.json).

A execução autenticada `run-20261015-012157-7487aabbd0c4` concluiu as cinco etapas em
213.018 ms, com cinco chamadas, sem falhas nem retries. O prefixo de data do ID está em UTC;
a data local foi 2026-10-14. O kit validou o envelope e `ai-team platform_inputs` o aceitou
contra o HEAD real do produto, com os caminhos de escopo conferidos. O score determinístico
foi 100/100; ele não substitui revisão humana ou execução de implementação.

A proposta gerada manteve como pendente o isolamento dos testes porque o contexto estático
selecionado não incluía o arquivo de teste completo. Essa ressalva foi resolvida pela leitura
direta e pela execução dos seis testes no runner offline. A baseline passou sem alterações;
assim, a implementação esperada limita-se ao workflow de CI. Não há necessidade demonstrada
de editar os testes nem adicionar dependências para este piloto.

Produto: `bussola-financeira`, checkout limpo em `main`, base
`51f4092dc8ad7f7439ca74b524f05286a46bff20`. A consulta local confirmou o CI restrito aos testes
de eventos e a presença de dois testes de integridade de ingestão fora dele.

- Objetivo: incluir `tests/test_ingestion_integrity.py` no CI, preservando os testes de ProductEvent
  e a validação do wheel `harness-v0.2.1` já vendorizado.
- Caminhos permitidos: `.github/workflows/ci.yml` e, somente mediante falha demonstrada,
  `tests/test_ingestion_integrity.py`.
- Critérios: os dois testes de ingestão passam sem rede ou banco externo, os testes de eventos
  continuam passando e o validador de artefato permanece obrigatório.
- Capacidades: reutilizar `engineering_delivery`, `financial_insights` e `product_events`,
  respeitando os donos do registry. Nenhuma capacidade nova é necessária.
- Fora do escopo: produção, APIs, fontes reais, dependências, migrações e correção dos testes de API.
  A pendência histórica do banco de testes será reavaliada em tarefa separada, sem migrar o banco do operador.

A proposta gerada pelo CLI precisa passar pela revisão humana da etapa 2 da esteira antes do
`ai-team run`. Merge, deploy e mudanças de produção têm autorização própria.

### Continuação autorizada e primeiro bloqueio do executor

O operador autorizou prosseguir com a consolidação e o piloto delimitado nesta sessão.
A revisão técnica confirmou o isolamento dos testes e o HEAD da proposta; não há necessidade
de editar testes. A baseline foi reexecutada por `local_team.test_command`: artefato verificado
e seis testes aprovados, com seus identificadores, sem rede ou credenciais.

As correções do CLI e do canário foram consolidadas no commit
`542f480fa30bf5663082a8be855eba5e2e6ab3df`. Nesta continuação passaram novamente 104 testes do CLI,
lint e tipos, 128 testes unitários e 23 testes adicionais do executor, checks de fronteiras,
handoff, arquitetura, conformance de eventos e o canário Docker das quatro etapas.

A tarefa `13c9fed321c04d8b94dccfa424e62aa4` terminou em `FAILED` durante `PLAN`: o sandbox
`read-only` do Codex não conseguiu iniciar comandos por `bwrap: No permissions to create a new namespace`.
Não houve implementação, entrega ou alteração no checkout original do produto. A configuração
permanece no sandbox padrão; a opção documentada `--codex-sandbox danger-full-access` exige escolha
explícita do operador para este projeto. Após resolver a causa, iniciar nova tarefa: uma tarefa
`FAILED` não pode ser retomada. Evidência: [continuação do piloto](../../cli/artifacts/pilots/bussola-ci-20261014/delivery-evidence.json).

### Preparo dos checks offline

A imagem local `bussola-tests:pilot-20261014` foi construída e testada, com identidade
`sha256:81e71a8a0c0e0a316fd35744d001564cfce1aa4e41bc28a23a2cc988d21aa064`.
O contexto de build contém somente os dois arquivos de requisitos e o wheel vendorizado;
nenhuma conta ou dado do produto foi incluído. A base é a imagem de provedores já instalada,
com dependências de teste em uma venv separada. Ela foi usada apenas no runner offline.

Os checks preparados para `ai-team init --test-image bussola-tests:pilot-20261014` são, nesta ordem:

```bash
python3 scripts/validate_harness_artifact.py
PYTHONPATH=src DATABASE_URL=sqlite+pysqlite:///:memory: python3 -m pytest -p no:cacheprovider tests/test_ingestion_integrity.py tests/test_product_events.py -q
```

O runner de checks já os executou com sucesso. O projeto foi configurado com esses checks
(`-v` no pytest para registrar os identificadores); a implementação aguarda a resolução do bloqueio acima.
A imagem é preparo local, não uma release
do produto; mudanças nos requisitos exigem reconstrução e nova validação antes de outra tarefa.
