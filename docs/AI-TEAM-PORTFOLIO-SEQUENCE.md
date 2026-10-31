# Sequência de auditoria do portfólio com ai-team

Preparado em 25/10/2026 a partir dos checkouts disponíveis e do catálogo
`packages/kit/contracts/portfolio-products.json`. A análise não executou o
`ai-team`, não inspecionou produção nem alterou código dos produtos.

## Escopo encontrado

O catálogo lista nove produtos: oito estão neste workspace; `ai-docs` não está
presente. O portal institucional `site-lf-solucoes` também é um repositório
separado e não está presente. O monorepo `product-platform` contém o kit, o
harness, o CLI e o próprio `ai-team`; ele também está incluído na sequência.

O checkout de `vehicle-tracking` não tem `AGENTS.md` local. Seu README declara
que o produto ainda não está pronto para produção e registra falhas conhecidas
em typecheck e testes; o agente deve confirmar o estado atual antes de alterar
essa conclusão.

Uma revisão local datada de 23/10/2026 registra itens pendentes para pagamentos
e inventário no harness, correções e aceitação editorial do portal, falha de
build externo do site no Cloudflare, dúvidas de autorização RapidAPI para
Wikidata e limites de evidência de produção. Trate isso como pistas a
revalidar, nunca como estado atual garantido.

## Como executar

Execute um prompt por vez, no diretório Git do repositório indicado. Antes de
cada execução, confirme checkout limpo e branch nomeada; siga o `AGENTS.md`
local, OpenSpec e comandos reais do repositório. Prepare `ai-team init` com
imagem de teste confiável e checks offline reais. Use `ai-team doctor` antes
do primeiro run. Não inicie o próximo run até o atual terminar e seu relatório
ser inspecionado. `ai-team watch` acompanha a tarefa local em andamento/mais
recente; mantenha-o no outro terminal conforme desejado.

Para esta sequência, inicie cada tarefa com `--authorize-r2` e passe o arquivo
[`AI-TEAM-PORTFOLIO-R2-RULES.md`](AI-TEAM-PORTFOLIO-R2-RULES.md) por `--rules`.
O arquivo registra a autorização do operador e seus limites; ele não reduz a
classificação do plano nem autoriza R3.

### Perfil econômico obrigatório para esta sequência

O texto do prompt não escolhe os modelos. A configuração por projeto do
`ai-team` escolhe um modelo para cada uma das quatro etapas; portanto aplique
este perfil em **cada repositório antes de executar seu prompt**:

```text
plan:      gpt-6-luna / low
implement: claude-haiku-5-5 / low
validate:  gpt-6-luna / low
review:    claude-haiku-5-5 / low
```

Esses IDs constavam no catálogo local retornado por `ai-team models` em
25/10/2026. Confirme `ai-team models` novamente em cada ambiente, pois o
catálogo e as contas podem diferir. Na primeira configuração do repositório,
adicione estas opções ao `ai-team init` junto da imagem e dos checks reais:

```bash
--plan-model gpt-6-luna --plan-effort low \
--implement-model claude-haiku-5-5 --implement-effort low \
--validate-model gpt-6-luna --validate-effort low \
--review-model claude-haiku-5-5 --review-effort low
```

Se já houver configuração, encerre qualquer tarefa ativa e use
`ai-team init --upgrade`, repetindo imagem e todos os checks atuais junto das opções acima.
O `--upgrade` substitui a configuração do projeto e grava backup; não o rode
com tarefa ativa. Rode `ai-team models` e `ai-team doctor` antes do primeiro
run. Os modelos baratos também fazem validação e revisão, então podem deixar
escapar problemas que os modelos mais fortes detectariam; mantenha os gates e
inspecione relatório e diff. Somente tarefas R0/R1 que cumpram os gates podem
seguir para `deliver`; tarefas R2 permanecem locais e o fluxo bloqueia sua entrega.

Cada tarefa deve ser exclusivamente de auditoria report-only: não altere código,
configuração, migrations nem documentação de produto; crie somente
`docs/audits/portfolio-audit-2026-10-25.md` no repositório-alvo, com evidências,
severidade, impacto, arquivos/áreas afetados, comandos executados e limitações.
Execute somente verificações locais já existentes e sem efeitos externos. Para
correções, mudanças de produto/comerciais, migrations, custos, credenciais,
publicação, deploy, integrações externas ou operações R2/R3, registre
recomendação e critério de decisão, sem executar. Não faça push, PR, merge,
release ou deploy. Preserve dados e segredos. Ao final, reporte o relatório,
validações e riscos residuais.

Em cada diretório-alvo, depois de conferir `ai-team doctor`, inicialize uma
única vez a configuração de teste econômica com os comandos próprios daquele
projeto e rode o texto do prompt abaixo com `ai-team run --background
'...prompt...'`. O limite report-only reduz o escopo de alteração, mas não
garante classificação R0/R1: o planejador pode concluir que a própria
auditoria exige risco R2/R3, caso em que a política bloqueia a tarefa. Não
reenvie o prompt para contornar o gate.
Se sua instalação expõe o atalho `ai-team-watch`, ele pode ser usado no outro
terminal; a interface documentada neste repositório é `ai-team watch`.

## Prompts sequenciais

### 1. vehicle-tracking

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Faça auditoria técnica de prontidão para produção do vehicle-tracking. Leia README, docs de arquitetura/deploy, configurações Next.js/Cloudflare, APIs, autenticação/autorização, persistência/migrations, WebSocket/tracker-server, testes e CI. Confirme se as falhas já registradas no README (typecheck e testes) ainda existem; não as presuma corrigidas ou atuais. Verifique exposição de dados, validação, isolamento entre usuários, segredos, migrations e comportamento de realtime. O checkout não tem AGENTS.md local: respeite instruções superiores e documente essa ausência. Rode somente checks existentes, sem serviços externos. Registre recomendações para defeitos críticos/altos, sem corrigi-los nesta tarefa. Não altere configuração de deploy, credenciais, dados reais ou contratos públicos. Não publique nem faça deploy. Entregue achados priorizados, evidências, validações e limitações.
```

### 2. bussola-financeira

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Audite o bussola-financeira para segurança, integridade financeira e confiabilidade dos dados exibidos. Leia AGENTS.md e /docs primeiro. Verifique proveniência, timestamp e metodologia das métricas, distinção fato/interpretação/hipótese, disclaimers, fontes/licenças (especialmente B3), segredos, importação/ingestão, APIs, persistência, autenticação, e se falha de analytics afeta requisições. Não crie dados simulados nem recomendações de compra/venda. Execute conformance do ProductEvent, validação do artefato e checks relevantes definidos pelo repositório, sem efeitos externos. Liste recomendações para defeitos sem corrigi-los nesta tarefa. Não processe dados financeiros reais, não altere credenciais, não publique e não faça deploy. Relate evidências, validações e limitações.
```

### 3. lf-worldbank-risk-pricing

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Audite lf-worldbank-risk-pricing como API de scoring e pricing sobre dados do World Bank. Examine contratos e validação dos endpoints, origem/frescor/licença dos dados, fórmula e limites de score/tier, precisão numérica, erros, abuso/rate limit, segredos, CORS, disponibilidade, documentação e workflow de publicação RapidAPI. Revalide comandos e estado atuais; não tome README/badges como prova de produção. Não publique na RapidAPI nem mude Render ou contratos externos. Rode pytest e smoke check se disponíveis, sem efeitos externos. Registre recomendações para defeitos altos/críticos sem corrigi-los nesta tarefa. Não adicione fontes ou dependências. Entregue relatório priorizado com entradas que reproduzem cada achado e limitações.
```

### 4. lf-openalex-enrichment-mvp

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Audite lf-openalex-enrichment-mvp como API de enriquecimento B2B. Inspecione contrato OpenAPI, normalização/validação de entradas, limites e custo de lotes, CORS e exposição de dados, tratamento de erros, resiliência ao OpenAlex, cache/quotas, segurança, logs, licença/proveniência dos dados e consistência entre documentação e implementação. Revalide o estado atual sem inferir prontidão de produção por badges ou texto do README. Rode flake8, pytest e smoke check conforme configurado, sem efeitos externos. Registre recomendações para defeitos altos/críticos sem corrigi-los nesta tarefa. Não altere publicação RapidAPI/Render, não envie listas de leads a serviços externos e não registre payloads pessoais. Reporte evidências, validações e limitações.
```

### 5. lf-wikidata-entity-graph

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Audite lf-wikidata-entity-graph como serviço de resolução de entidades: pipeline e contrato, limiar/confiança dos matches, falsos positivos/negativos cobertos por testes, chamadas/limites da Wikidata, cache, dados pessoais, segurança, métricas, documentação e workflow RapidAPI. Trate qualquer nota anterior sobre HTTP 403, Platform API ou owner ID apenas como hipótese; não tente contornar autorização, não exponha chaves, não faça chamadas administrativas nem publique. Rode testes, smoke e lint configurados, sem efeitos externos. Registre recomendações para defeitos altos/críticos sem corrigi-los nesta tarefa. Entregue relatório priorizado, validações e bloqueios externos sem credenciais.
```

### 6. agentic-travel-engine

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Audite agentic-travel-engine ponta a ponta: API e frontend, validação de pedidos, chamadas LLM e conectores de terceiros, tratamento de preferências/dados pessoais, timeouts/retries/rate limits, circuit breakers/cache, moeda/preços, ranking e explicabilidade, segredos, CORS, logging e custos/abuso. Confirme que resultados e disponibilidade dos provedores são representados sem promessas não verificadas. Rode make lint, make test e checks de frontend disponíveis sem chaves, compras ou chamadas pagas. Registre recomendações para vulnerabilidades ou bugs críticos/altos sem corrigi-los nesta tarefa. Não altere credenciais, integrações externas, contratos ou deploy. Entregue achados com evidência e limitações da validação sem provedores reais.
```

### 7. fivem-server-monitor-pro

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Audite fivem-server-monitor-pro para segurança operacional e prontidão da beta. Leia AGENTS.md, SECURITY.md, BETA_RELEASE.md, SUPPORT_POLICY.md e COMMERCIAL_RELEASE.md. Verifique autorização em eventos/exports/NUI, rate limiting, persistência e recuperação, limites de metadados, privacidade de jogadores, webhooks/menções, compatibilidade de frameworks e diferenças entre evidência standalone e servidor real. Preserve EULA.md e termos comerciais. Execute npm run verify e checks existentes. Registre recomendações para falhas críticas/altas sem corrigi-las nesta tarefa. Não conecte a FXServer real, não envie webhooks, não altere termos, publicação Cfx/Tebex nem faça release. Relate claramente o que requer homologação em servidor real.
```

### 8. professional-english-coach

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Audite professional-english-coach com foco em privacidade local, consentimento e precisão das alegações educacionais. Leia AGENTS.md, README, OpenSpec, acceptance e docs de pesquisa/roadmap. Verifique armazenamento/exportação/exclusão local, envio opt-in de respostas ao provedor no modo local, logs, diferenças da versão hospedada, acessibilidade e limitações de speech/browser. Não afirme fluência falada avaliada, certificação CEFR ou qualidade de aprendizagem não medida. Rode npm run check, npm test e npm run build conforme aplicável. Registre recomendações para defeitos altos/críticos sem corrigi-los nesta tarefa. Não altere conteúdo pessoal, provedor, publicação ou deploy. Entregue achados e limitações de avaliação humana/browser.
```

### 9. ai-docs — executar somente no checkout próprio

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. No repositório ai-docs, faça auditoria técnica do processamento de documentos: tipos/tamanho de entrada, parsing/OCR, arquivos maliciosos, isolamento e retenção, conteúdo sensível, validação, limites de recursos, tarefas longas/retries, dependências, segredos, logs, APIs e evidência real de execução. Primeiro leia as instruções locais e identifique a arquitetura e os comandos reais; não infira detalhes ausentes. Não envie documentos para serviços externos nem use credenciais/dados reais. Rode somente checks locais existentes, sem efeitos externos. Registre recomendações para defeitos críticos/altos sem corrigi-los nesta tarefa e não altere deploy, armazenamento externo ou contratos. Entregue relatório priorizado, evidências e limites que exigem perfil real de CPU/memória.
```

### 10. site-lf-solucoes — site institucional, executar somente no checkout próprio

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Audite o portal institucional site-lf-solucoes e seu catálogo público. Leia instruções locais e documentação editorial; verifique consistência de data/product-catalog.json com o registry do portfólio, links/rotas, metadados/SEO, acessibilidade, segurança de build e limites de orçamento do site. Trate como itens a revalidar a falha do build externo Cloudflare e os ajustes editoriais/catálogo reportados em 23/10/2026; não presuma que persistem nem que foram resolvidos. Não edite ou publique alegações de produto sem evidência dos respectivos donos. Registre recomendações para defeitos técnicos altos/críticos sem corrigi-los nesta tarefa. Não mexa em DNS, Cloudflare, secrets, domínio nem publicação. Preserve revisão editorial para conteúdo. Entregue relatório, checks e qualquer bloqueio que dependa de logs/permissões externas.
```

### 11. product-platform — executar por último

```text
IMPORTANTE: tarefa somente de auditoria report-only. Não modifique código, configuração, migrations, docs de produto, credenciais ou deploy. Crie somente `docs/audits/portfolio-audit-2026-10-25.md` como saída do produto. Os arquivos `openspec/changes/ai-team-<task>/<cycle>/` são gerados automaticamente pelo host e não contam como saída da auditoria. Audite o monorepo product-platform, incluindo packages/kit, harness, cli, engineering-team/ai-team, design-system, contratos do portfólio, CI, segurança do runtime e documentação operacional. Verifique fronteiras de pacotes e consumidores, compatibilidade e checksums do harness, contratos/schema, isolamento das etapas do ai-team, gates, permissões, privacidade de logs, fluxo de entrega e estado atual das pendências registradas em docs/validation/2026-10-23-review-followup/readiness.md. Preserve as distinções entre evidência local, aprovação independente, CI, publicação e produção. Registre recomendações para defeitos críticos/altos sem corrigi-los nesta tarefa; não enfraqueça gates, não contorne aprovações, não altere credenciais ou automações externas e não publique releases. Rode somente checks existentes pertinentes, sem efeitos externos. Entregue relatório priorizado, compatibilidade/consumidores impactados e riscos residuais.
```

## Ordem e limites

Os prompts 1–8 cobrem os produtos que estão neste workspace; 9 e 10 precisam
dos checkouts próprios. O prompt 11 fica por último porque mudanças no kit,
harness ou contratos podem afetar consumidores já auditados. Se uma auditoria
não encontrar defeito crítico/alto verificável, finalize sem criar mudanças.

Esta sequência não autoriza release, publicação, push, merge, deploy, uso de
credenciais ou operação em produção. Revise cada relatório e diff antes de
qualquer entrega R0/R1 permitida; auditorias R2 permanecem nos workspaces locais
e não podem ser entregues pelo `ai-team`.

## Execução autônoma — registro de 26/10/2026, pins atualizados em 31/10/2026

O registro abaixo é um relato operacional do operador baseado em evidências locais não versionadas. Ele documenta o histórico informado, mas não constitui evidência de CI nem pode ser verificado apenas por este repositório.

- `ai-team doctor` passou; todos os quatro logins aparecem autenticados.
- O runtime foi atualizado e testado pelo procedimento oficial: Codex CLI
  0.164.0 e Claude Code 2.1.310. O teste de isolamento passou quando o diretório
  temporário foi colocado sob o workspace compartilhado pelo Docker Desktop.
  Essas versões registram a verificação de 26/10/2026. Na atualização de
  31/10/2026, npm, Dockerfile e preflight confirmaram Codex 0.166.0 e Claude
  Code 2.1.316; veja a baseline atual em `runtimes/Dockerfile` e `scripts/preflight.py`.
- Os 11 prompts desta sequência foram submetidos ao `ai-team`, usando o perfil
  econômico declarado acima e `--authorize-r2 --rules` com as regras locais.
  A tabela registra o resultado terminal de cada prompt. `FAILED` significa que
  o run não passou integralmente pelos gates do `ai-team`; não significa que o
  conteúdo do relatório foi aprovado.

| # | Produto | Resultado / task principal | Evidência e motivo terminal |
|---|---|---|---|
| 1 | vehicle-tracking | `FAILED` — `c949c0865a154a14aef31b416fe97ae5` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; limite de ciclos após divergências no relatório, hashes e evidência dos checks. |
| 2 | bussola-financeira | `FAILED` — `a99c68e6846549ab8cd12965ddf1acc0` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; limite de ciclos com achados de validação/revisão sobre cobertura e evidências. |
| 3 | lf-worldbank-risk-pricing | `FAILED` — `1c54b8b908bd43318bfe4493aa98a0e2` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; limite de ciclos após achados de revisão/validação. |
| 4 | lf-openalex-enrichment-mvp | `FAILED` — `499247b5b73949a2b51e7da8fee3533a` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; limite de ciclos; revisão apontou lacunas funcionais e de segurança. |
| 5 | lf-wikidata-entity-graph | `FAILED` — `1a46237b03b64e029fa27f6366e08e36` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; limite de ciclos; revisão apontou problemas de resolução/matching. |
| 6 | agentic-travel-engine | `FAILED` — `510351c763b4458cbaede24c56eb024f` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; bloqueado no ciclo final, com checks de frontend não configurados e inconsistência de evidências. |
| 7 | fivem-server-monitor-pro | `FAILED` — `2b56759c16734f7eb15a9e11cf16adb5` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; checks configurados falharam: `npm run test:lua` não existe/não encontra testes. |
| 8 | professional-english-coach | `FAILED` — `c5ca0c0cbcc448a0a06beb6219b5306d` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; implementação bloqueada antes do estágio de checks do host. |
| 9 | ai-docs | `FAILED` — `8019c3abc8bc4b61a8e896bbff8022a8` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; limite de ciclos por divergência sobre cobertura e resultados dos checks no relatório. |
| 10 | site-lf-solucoes | `FAILED` — `228677e0209547978c6f5a9be7cc4500` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; avaliação não cobriu o plano exatamente. Relatório isolado em `workspace/docs/audits/portfolio-audit-2026-10-25.md`. |
| 11 | product-platform | `FAILED` — última tentativa `02b7492543294d12adbceeaaf5ab3456` | Evidência local em `~/.local/state/ai-team/runs/<task-id>`; limite de ciclos. Outras tentativas: `c7b7f30e22ef46f895893b06cc3e847f`, `49874bb67d6b439b9e5fe2d4fe4382ba`, `ea1c35dfa9094b1f83a5bd1a96c24357`. Relatório da última tentativa em `workspace/docs/audits/portfolio-audit-2026-10-25.md`. |

Todos os relatórios gerados permanecem dentro dos workspaces isolados listados
nas evidências das tarefas. Nenhum relatório foi entregue ao checkout original;
nenhum `ai-team deliver`, push, PR, merge, publicação ou deploy foi executado.
No `product-platform`, a primeira tentativa com clone compartilhado encontrou
um caminho de Git alternates inválido; as tentativas seguintes usaram clone
completo isolado. A última tentativa confirmou os quatro modelos baratos no
catálogo e avançou por vários ciclos antes de atingir o limite de correção.

Os resultados não equivalem a uma aprovação técnica do portfólio. Para
consumi-los, revise cada relatório e seus `tests.json` no run correspondente;
em especial, não trate achados sugeridos por modelos baratos como confirmados
sem verificar a evidência primária. A sequência está executada até o limite
operacional do `ai-team`; não há tarefas ativas pendentes desta sequência.
