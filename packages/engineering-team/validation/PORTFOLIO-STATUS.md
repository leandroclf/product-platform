# Portfólio: diagnóstico e execução pelo ai-team

Observado em 2026-10-14, horário de São Paulo. Escopo: os nove produtos ativos de
`packages/kit/contracts/portfolio-products.json`. Plataforma de referência:
`37184551a1440b26fc5f117334f3ba3298332779`; fingerprint do registry:
`b476209eb1a2fcef3f7dd99a53393e9846ccb674bb1ba26c0337819c55a4d3d9`.

## Método e limites

Conferidos instruções locais, HEAD, estado dos checkouts, manifests, workflows,
testes relevantes, código dos fluxos selecionados e main/CI/PRs no GitHub.
O AI Docs foi inspecionado no GitHub porque não há checkout local localizado.
Não houve alteração de código dos produtos, chamada a API de produção, acesso a
credenciais ou reexecução de deploy. Os checkouts locais estavam limpos.

Esta é uma triagem técnica para selecionar trabalhos delimitados, não uma auditoria
integral de cada produto. CI histórico aprovado não comprova aceitação funcional,
qualidade do dado, disponibilidade do serviço nem segurança em produção.
Não foram encontrados PRs abertos nos nove repositórios na consulta.

A skill local `tech-lead` orientou a análise. O AAS foi consultado; a orientação
local foi mantida para esta tarefa, sem importar outra stack de skills. Na etapa
de contratos HTTP foi aplicada `postman:api-engineer`, reutilizando contratos locais
e evidência offline; nenhum workspace ou recurso externo do Postman foi modificado.

## Situação dos nove produtos

| Produto | main no GitHub | Evidência e lacuna atual | Próxima tarefa delimitada | Risco da tarefa |
|---|---|---|---|---|
| bussola-financeira | `51f4092` | CI só executa ProductEvent; seis testes do piloto e artefato já passaram offline. O último run encontrado de CI é de outro SHA (`1a0f1ce`), portanto não certifica este HEAD. | Incluir os dois testes existentes de ingestão no CI, preservando eventos e artefato. Depois, tarefa separada para isolamento dos testes de API. | R1 |
| ai-docs | `87f2748` | CI desse SHA passou. `CallbackService` usa `settings.api_key` como header de saída por padrão; headers explícitos podem substituí-lo. Alguns caminhos de falha do chamador omitem a credencial específica do callback. O teste atual cobre somente construção sem event loop. | Eliminar fallback para a credencial de entrada; preservar a credencial de callback explícita e testar headers em sucesso e falha. Depois, ciclo de vida e retries determinísticos em tarefa própria. | R2 |
| lf-wikidata-entity-graph | `a53a285` | CI desse SHA passou, mas o linker gera pseudo-QID por hash e confiança por comprimento do nome, sem consultar Wikidata, marcando `linked=true`. Reprodução local confirmou o comportamento. | Impedir que identificador sintético seja exposto como vínculo verificado; retornar não resolvido quando não houver evidência. Atualizar contrato/exemplos/testes sem inventar integração externa. | R2 |
| vehicle-tracking | `43cd73e` | CI e job validate do deploy falham em `pnpm install --frozen-lockfile`; validate da aplicação, migração e deploy foram pulados. Comparação no SHA remoto encontrou seis dependências OTEL ausentes do importer do lockfile. | Sincronizar deterministicamente o lockfile com dependências já declaradas e refazer instalação/validação. Não alterar versões ou implantar junto. | R2 |
| lf-openalex-enrichment-mvp | `c4c412b` | CI, CI Pipeline e GitFlow Guard passaram nesse SHA. `build_value_signal_summary` aceita NaN e retorna score não finito com banda low, reproduzido sem rede. O enriquecimento lido normaliza e mede os campos recebidos; essa função não consulta OpenAlex. | Rejeitar scores não finitos na fronteira apropriada, preservando o comportamento dos números finitos e cobrindo contrato HTTP. Avaliar conexão real e origem dos dados em outra tarefa. | R1/R2 conforme contrato |
| lf-worldbank-risk-pricing | `98dfb26` | CI e GitFlow Guard passaram nesse SHA. Há testes com mocks para fonte indisponível e fallback de ano, além de governança. Não há lint no CI. | Exercitar respostas de origem malformadas/não finitas e a rastreabilidade do ano efetivamente usado, com mocks e sem alterar fórmula financeira por suposição. Nenhum defeito adicional foi reproduzido nesta triagem. | R1; R2 se contrato mudar |
| agentic-travel-engine | `e65fe48` | CI desse SHA passou; já executa ruff, black e pytest. Existem testes de conectores e de falha parcial. Conversão monetária não tem uma suíte dedicada identificada. | Cobrir conversão com cache, taxa inválida/ausente e falha do provedor; preservar moeda/valor quando a conversão falhar, usando mocks e sem chamar LLM ou fonte real. | R1 |
| fivem-server-monitor-pro | `658dbfb` | CI desse SHA passou. `npm run verify` passou agora: validador de 90 arquivos/14 referências e 12 testes. Aceitação interativa, frameworks e retenção prolongada seguem pendentes no OpenSpec. | Exercitar retenção/recuperação Lua em ambiente controlado; separar dos testes com cliente/FXServer, que exigem ambiente real. Não declarar compatibilidade QBCore/Qbox/ESX apenas pelos testes estáticos. | R1 para testes; ambiente real separado |
| professional-english-coach | `ade1d81` | CI desse SHA passou. `npm run check` passou agora com 38 testes. Helpers de restore validados existem no código; a inspeção posterior confirmou ausência de controles de import/restore em src/app.js. | Reconciliar roadmap/OpenSpec distinguindo helpers testados de interface de restauração ausente; deixar perfis familiares e hospedagem de IA para requisitos próprios. | R0/R1 |

## Evidências principais

- [Vehicle: CI e etapa que falhou](https://github.com/leandroclf/vehicle-tracking/actions/runs/37806392328).
  [Deploy bloqueado no validate](https://github.com/leandroclf/vehicle-tracking/actions/runs/37806392239).
  Comparação estática de `package.json` e `pnpm-lock.yaml` no mesmo SHA encontrou:
  `@opentelemetry/api`, `@opentelemetry/auto-instrumentations-node`,
  `@opentelemetry/exporter-trace-otlp-http`, `@opentelemetry/resources`,
  `@opentelemetry/sdk-node` e `@opentelemetry/semantic-conventions` sem specifier no
  importer raiz. Os logs falhos não retornaram conteúdo; a etapa que falhou e a
  divergência foram verificadas separadamente. Não se afirma que essa é a única
  causa possível da instalação.
- [AI Docs: serviço de callback](https://github.com/leandroclf/ai-docs/blob/87f27488df154261b547bb5c5264b8945aa3e536/app/services/callback_service.py),
  [chamadores de sucesso/falha](https://github.com/leandroclf/ai-docs/blob/87f27488df154261b547bb5c5264b8945aa3e536/app/services/async_document_service.py)
  e [CI observado](https://github.com/leandroclf/ai-docs/actions/runs/37616171883).
  Confirmado no código: há fallback para a chave de entrada quando headers de
  callback não a substituem. Não foi investigado se houve exposição em produção.
- [Wikidata: linker inspecionado](https://github.com/leandroclf/lf-wikidata-entity-graph/blob/a53a2857391426c66736308abde8b0f3b04af282/backend/src/api.py).
  A reprodução local, sem rede, com nome de teste retornou `linked=true`, confiança
  0.9 e um QID calculado por hash. Trata-se de resultado sintético, não de identidade
  confirmada pela fonte. [CI observado](https://github.com/leandroclf/lf-wikidata-entity-graph/actions/runs/37617880849).
- OpenAlex: reprodução direta de `build_value_signal_summary("test", float("nan"))`
  retornou score NaN e banda low. Não foi executado um ataque ao endpoint remoto.
  [CI observado](https://github.com/leandroclf/lf-openalex-enrichment-mvp/actions/runs/37619473348).
- [Bússola: evidência offline e bloqueio do executor](../../cli/artifacts/pilots/bussola-ci-20261014/delivery-evidence.json).
- [World Bank: CI](https://github.com/leandroclf/lf-worldbank-risk-pricing/actions/runs/37617866257),
  [Travel: CI](https://github.com/leandroclf/agentic-travel-engine/actions/runs/37627015385),
  [FiveM: CI](https://github.com/leandroclf/fivem-server-monitor-pro/actions/runs/37626873165),
  [English Coach: CI](https://github.com/leandroclf/professional-english-coach/actions/runs/37626851983).

## Frescor dos checkouts

| Produto | HEAD local | Situação frente ao main remoto observado |
|---|---|---|
| vehicle-tracking | `3a336e0` em main | SHA diferente; não usar este checkout como baseline atual sem fetch e reconciliação |
| bussola-financeira | `51f4092` em main | Mesmo SHA |
| lf-worldbank-risk-pricing | `40b504e` em chore/plataforma-agents-md | Branch anterior à integração; usar checkout isolado no main remoto, preservando esta branch |
| lf-openalex-enrichment-mvp | `c4c412b` em main | Mesmo SHA |
| lf-wikidata-entity-graph | `dddf774` em chore/plataforma-agents-md | Branch anterior à integração; usar checkout isolado no main remoto, preservando esta branch |
| agentic-travel-engine | `e65fe48` em main | Mesmo SHA |
| fivem-server-monitor-pro | `658dbfb` em main | Mesmo SHA |
| professional-english-coach | `ade1d81` em main | Mesmo SHA |
| ai-docs | Não localizado | Inspeção remota no SHA `87f2748`; preparar checkout isolado antes de execução |

## Ordem proposta

1. Resolver a aceitação do executor. A tarefa anterior da Bússola falhou em PLAN
   porque `bwrap` não conseguiu criar namespace. Não repetir a mesma execução nem
   mudar sandbox sem a escolha explícita do operador. Um host onde o sandbox padrão
   funcione também é válido. Nenhuma credencial deve ser copiada para resolver isso.
2. Fechar o piloto de CI da Bússola: escopo de uma linha, imagem e baseline offline
   prontas. Ele comprova a jornada de entrega em produto; não encerra as pendências
   funcionais ou de produção. Essa validação curta não deve virar pretexto para
   adiar as correções de integridade e credenciais abaixo.
3. AI Docs: separação de credenciais de entrada e callback. Antes de executar,
   congelar contrato, chamadores, critérios e imagem offline no seu próprio envelope.
4. Wikidata: impedir vínculos externos sintéticos. Exigir contrato/exemplos coerentes
   e regressão do pipeline, sem implementar um conector real nessa mesma tarefa.
5. Vehicle: reparar reprodutibilidade da instalação. O Argus não tem Bash: não pedir
   ao modelo que escreva milhares de linhas de lockfile manualmente. A regeneração
   determinística pelo pnpm e o preparo da imagem precisam ser feitos pelo host,
   em checkout isolado, antes de congelar uma nova tarefa ou por uma extensão
   explicitamente projetada do runner. Atualizar a baseline e a imagem após isso.
6. OpenAlex: números não finitos e contrato de erro; depois avaliar enriquecimento real.
7. World Bank, Travel e FiveM: workloads determinísticos específicos da tabela,
   um repositório por tarefa, após preparar os respectivos checks offline.
8. English Coach: reconciliar documentação e aceitação do restore já implementado;
   não reimplementar a mesma capacidade por causa de um checkbox antigo.
9. Só após evidência de repetição entre produtos, evoluir G3 ou o harness no dono
   canônico. Não adicionar telemetria, pagamentos, novos serviços ou dependências
   aos produtos apenas para uniformizar o portfólio.

Prioridade de risco e prontidão de execução são critérios distintos: o piloto é o
primeiro pronto; AI Docs e Wikidata são as primeiras remediações de produto.

## Prompt pronto para a primeira execução

Prompt: [prompt.txt](portfolio-2026-10-14/prompt.txt).
Envelope: [handoff-bussola-ci.json](portfolio-2026-10-14/handoff-bussola-ci.json).
O envelope reduz o escopo à `.github/workflows/ci.yml`, porque a leitura e a baseline
já demonstraram que não é preciso alterar testes. Ele foi montado pelo coordenador
com base na proposta original; não é uma nova concepção autenticada do CLI.

Antes do comando: checkout da Bússola limpo em `51f4092dc8ad7f7439ca74b524f05286a46bff20`,
registry e regras nos SHAs registrados, imagem de teste preparada e problema do sandbox
resolvido com autorização aplicável. A configuração era `read-only` na preparação. Na rodada seguinte o operador autorizou explicitamente `danger-full-access` nos nove projetos, mantendo Docker como fronteira; veja campaign.json.

Na raiz da Bússola, com `PLATFORM_ROOT` apontando para este checkout da plataforma:

```bash
PLATFORM_ROOT=/home/leandro/IdeaProjects/lfsolucoes/product-platform/product-platform
PILOT_DIR="$PLATFORM_ROOT/packages/engineering-team/validation/portfolio-2026-10-14"
rtk ai-team run \
  --handoff "$PILOT_DIR/handoff-bussola-ci.json" \
  --registry "$PLATFORM_ROOT/packages/kit/contracts/capability-registry.yaml" \
  --rules "$PLATFORM_ROOT/packages/kit/docs/PLATFORM-DELIVERY-FLOW.md" \
  --rules "$PLATFORM_ROOT/packages/harness/AGENTS.md" \
  "$(rtk proxy cat "$PILOT_DIR/prompt.txt")"
```

O `ai-team` opera um alvo por execução. O prompt não dá autoridade para navegar
pelo host nem alterar os outros oito produtos. O host registra o OpenSpec fora do
escopo do agente, roda checks e cria commits. REVIEWED exige validação e revisão
no mesmo SHA; entrega em branch/PR é etapa seguinte, e produção permanece separada.

## Execução da rodada autorizada

O operador pediu execução dos nove produtos e autorizou explicitamente a configuração
do sandbox para esta rodada. O acompanhamento persistente está em
[estado da rodada](portfolio-2026-10-14/campaign.json), com envelopes, prompts,
configurações congeladas, baselines e evidências por produto. A conclusão de uma
tarefa delimitada não certifica o produto inteiro para produção.

A verificação do English Coach em Chrome headless com sandbox habilitado confirmou
exportação de JSON v1 e helpers de restore com rejeição de conflito/substituição
explícita. Não há controle de import/restore na interface; essa funcionalidade
continua parcial. Nenhum conteúdo real de aprendiz foi utilizado.


## Resultado da rodada pelo ai-team — 15/10/2026

As nove tarefas delimitadas passaram por planejamento, implementação, checks offline,
Sentinel e revisão no SHA final, foram entregues em PR, e os nove CIs remotos passaram.
A coluna “testes” resume apenas os checks declarados e seus resultados nesta tarefa;
não representa uma certificação completa do produto. O estado detalhado, hashes,
configurações congeladas, checks e tentativas anteriores estão em
[campaign.json](portfolio-2026-10-14/campaign.json).

| Produto | Resultado desta tarefa | Checks offline registrados | Entrega |
|---|---|---|---|
| Bússola | Incluídos os testes determinísticos de ingestão no CI; 6 testes | artefato do harness + 6 testes | [PR 8](https://github.com/leandroclf/bussola-financeira/pull/8), CI passou |
| AI Docs | Callback usa credencial de saída própria; 20 testes | suíte pytest com POST/PUT, ausência/override de chave, falhas e retries | [PR 27](https://github.com/leandroclf/ai-docs/pull/27), CI passou |
| Wikidata Entity Graph | Remove pseudo-QIDs sem fonte verificada; 45 testes e smoke 6/6 | pytest + smoke | [PR 6](https://github.com/leandroclf/lf-wikidata-entity-graph/pull/6), CI passou |
| Vehicle Tracking | Lockfile reproduzível e instrução de instalação; 37 testes | conformance, typecheck, instalação congelada offline, testes e build Next (62 páginas) | [PR 54](https://github.com/leandroclf/vehicle-tracking/pull/54), CI passou; mantido aberto porque merge em main aciona migração e deploy |
| OpenAlex | Rejeita scores não finitos/inválidos; 84 testes | pytest + flake8 + smoke | [PR 7](https://github.com/leandroclf/lf-openalex-enrichment-mvp/pull/7), CI passou |
| World Bank | Valida indicadores finitos e fallback de ano; 125 testes, 1 skip externo preexistente | pytest + smoke | [PR 5](https://github.com/leandroclf/lf-worldbank-risk-pricing/pull/5), CI passou |
| Agentic Travel | Preserva montante/moeda/confiança quando não há taxa válida; 51 testes | pytest + ruff + black | [PR 7](https://github.com/leandroclf/agentic-travel-engine/pull/7), CI passou |
| FiveM Monitor | Preserva backup e retry; 12 testes Lua + 12 JavaScript | `npm run verify`, `npm run test:lua`, sintaxe Lua | [PR 3](https://github.com/leandroclf/fivem-server-monitor-pro/pull/3), CI passou |
| English Coach | Corrige o estado documental: helpers de restore existem, UI de import/restore continua pendente; 38 testes | check + build + evidência headless sem rede | [PR 3](https://github.com/leandroclf/professional-english-coach/pull/3), mesclado em `main` no commit `59c5b90`; checkout local sincronizado |

O FiveM teve uma tentativa encerrada sem alteração porque a nota genérica já existia;
a tentativa nova executou a suíte Lua contra a produção original e reproduziu três
falhas de preservação de backup/estado dirty. A tarefa seguinte documentou o contrato
preciso, corrigiu o parecer e passou todas as verificações. Vehicle e Travel também
precisaram de novas tentativas após bloqueios de cota ou evidência. As tentativas estão
preservadas no registro; nenhuma aprovação foi atribuída a elas.

Os PRs permanecem em rascunho para integração pelo responsável, exceto English Coach,
cuja instrução local manda levar a entrega a `main` e cujo PR foi mesclado após o CI.
Vehicle permanece como PR aberto. Não foi feito deploy ou migração em produção.

A rodada fecha tarefas específicas, não a prontidão integral dos produtos. Permanecem
fora do que foi provado: integrações com provedores reais em Travel, execução longa e
frameworks/cliente/ACE em FXServer, perfis e disponibilidade de fontes externas, além
da interface de import/restore e avaliação de aprendizagem do English Coach. Em
Vehicle, a atualização de dependências foi validada com instalação e build, mas a
integração que aciona migração/deploy requer a janela e o processo próprios.
