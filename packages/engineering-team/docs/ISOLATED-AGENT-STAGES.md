# Três agentes, quatro etapas isoladas

Contrato do CLI local 0.2.0. Substitui a distribuição local anterior, sem reescrever a evidência histórica do harness ou instanciar Dots. Sem gateway, roteador aprendido, banco ou novo serviço.

| Etapa | Agente | CLI | Modelo padrão | Esforço |
| --- | --- | --- | --- | --- |
| plan | Atlas | Codex | `gpt-6-astra` | `xhigh` |
| implement | Argus | Claude Code | `claude-opus-5-5` | `high` |
| validate | Sentinel | Codex | `gpt-6-astra` | `xhigh` |
| review | Atlas em nova sessão | Claude Code | `claude-opus-5-5` | `high` |

Escolhas baseadas nos guias oficiais de 2026-10-03: Astra para raciocínio exigente e Opus 5.5 para programação com agentes. Não são superioridade comprovada no projeto. Acesso depende da conta/cliente/políticas nativas. `init` permite IDs explícitos do mesmo provedor e esforços suportados usando `--plan-model`, `--implement-model`, `--validate-model`, `--review-model` e os respectivos `--*-effort`. Não há troca automática se um modelo falhar.

Com `model_routing` habilitado (padrão em novas configurações), o host aplica o perfil medido `plan=gpt-6.1-sol/medium`, `implement=claude-sonnet-5-5/medium`, `validate=gpt-6-astra/medium`, `review=claude-opus-5-5/medium` apenas para pedidos curtos, explicitamente documentais e sem sinais de risco. O plano precisa confirmar R0/R1, até duas tarefas e três critérios; caso contrário, as etapas restantes usam os modelos configurados. O pedido R2, sinais de segurança/produção/código, escopo ambíguo, catálogo ausente ou perfil econômico indisponível mantêm o perfil configurado. O modelo econômico é validado contra os catálogos das quatro etapas antes de iniciar. A decisão, o motivo e os modelos são congelados em `state.json`; não há chamada adicional de classificador nem fallback depois de erro do provedor. Configurações existentes permanecem fixas até `init --upgrade`; `--no-model-routing` desativa o roteamento.

## Isolamento

Cada chamada tem container, sessão, staging e handoff próprios. Volumes: `ai-team-atlas-plan-home`, `ai-team-argus-implement-home`, `ai-team-sentinel-validate-home`, `ai-team-atlas-review-home`. Codex é ephemeral; Claude não persiste sessão, usa modo restrito, hooks desabilitados e MCP vazio. Não há resume/continue de conversas. Volumes separados não provam identidades distintas.

Atlas planeja com checkout somente leitura: objetivo, escopo, premissas, risco, tarefas, critérios e validação. O host valida JSON, SHA e cobertura; calcula identidade SHA256 e escreve `openspec/changes/ai-team-<task>/<cycle>/`, com commit anterior à implementação. Plano R3 ou BLOCKED impede execução. O plano canônico fica fora do checkout e é montado somente leitura.

Argus implementa com Read/Grep/Glob/Edit/Write; Bash, Agent e MCP são removidos. Apenas implementação recebe checkout gravável; Git metadata permanece somente leitura para todos. O host executa checks offline sem contas. Argus devolve COMPLETE, BLOCKED ou REPLAN_REQUIRED; COMPLETE não substitui verificação.

Sentinel valida pedido/aceite/evidências. Atlas/Claude revisa correção, segurança, manutenção e regressões em nova sessão. Ambos recebem pedido original, plano, código e checks; o revisor não recebe o parecer nem a conversa do validador. Os dois resultados exigem HEAD, plano e evidência para cada critério, além de qualidade/segurança obrigatórias. JSON válido não prova veracidade.

Falhas verificáveis retornam ao Argus; plano inadequado retorna ao Atlas/OpenAI. Replanejamento consome o mesmo limite de ciclos/prazo. Erro de provedor, saída inválida ou estado incerto bloqueiam. Não há publicação, merge ou deploy automático.

## Evidência, atualização e retomada

### Escolha de modelos por etapa

`ai-team models` compara a configuração com o catálogo real que cada CLI guarda no volume do estágio e lista o que a conta oferece (com esforços suportados). `init` e `run` recusam, antes de gastar cota, IDs inexistentes (com sugestão, por exemplo `gpt-6-Luna` → `gpt-6-luna`), esforços não suportados e modelos cobrados à parte por créditos de uso (o ai-team nunca altera cobrança). O formato do ID sozinho não basta: um ID inexistente só falharia na própria etapa, depois das anteriores terem gasto cota.

Critério usado para reduzir tokens sem enfraquecer os gates, com os números medidos em tarefas reais:
- **Economizar no produtor.** O Argus responde por ~75% do gasto Claude; o Sonnet 5.5 custa cerca de metade do Opus 5.5 por token (US$ 0,0038 contra US$ 0,0078 no mesmo prompt com cache) e o esforço médio reduz o raciocínio, que era ~53% da saída com esforço alto. Planos e revisões seguem protegendo o resultado.
- **Verificadores fortes e diferentes do produtor.** O Sentinel pegou um defeito real que o produtor deixou passar; um modelo "rápido e barato para tarefas fáceis" (`gpt-6-luna`) ou o mesmo modelo do Argus no revisor reduz a diversidade dos gates. Por isso a revisão do Atlas usa um modelo diferente do Argus.
- **O esforço dos estágios Codex pesa pouco em tokens aqui:** o raciocínio foi de 2 a 4 mil tokens contra 400 a 760 mil de entrada; reduzir o esforço ajuda no tempo e no consumo do limite, não no volume lido.

Perfil adotado no projeto de validação (editável com `init --upgrade --<etapa>-model/--<etapa>-effort`): plan `gpt-6.1-sol` médio, implement `claude-sonnet-5-5` médio, validate `gpt-6-astra` médio, review `claude-opus-5-5` médio. Os padrões do framework não mudam sem um A/B real que mostre qualidade igual.

state.json registra etapa, agente, provedor, modelo solicitado, esforço e plano. `resolved_model: null` significa modelo efetivo não confirmado, sem inferência. Artefatos por ciclo: plan, implement, tests, validate e review. Entrega revalida os dois pareceres e checks no HEAD atual.

Config/tarefas usam versão 2. Repita `init --upgrade` com imagem/checks explícitos para atualizar configuração; preserva backup privado. Não migra tarefas: versões antigas não retomam nem entregam sob contrato novo. Retomada mantém plano/modelos/prazo; estágio interrompido ou staging parcial não é repetido automaticamente.

## Aceitação operacional

Testes controlados comprovam contratos, ordem, falhas e comandos, não acesso aos modelos ou ferramentas reais. Rebuild, quatro logins, doctor e tarefa pequena no Linux do operador com diff inspecionado são necessários. Sandbox Codex depende do kernel/cliente; não contornar incompatibilidade com bypass por padrão. Onde o bwrap não inicia no container, o operador pode optar explicitamente por projeto com `init --codex-sandbox danger-full-access`, que fica registrado na configuração congelada da tarefa e mantém o container como fronteira. O isolamento não é DLP completo nem garantia de independência cognitiva.

Fontes: [modelos OpenAI](https://learn.chatgpt.com/docs/models), [raciocínio/configuração](https://learn.chatgpt.com/docs/config-file/config-reference), [modelos Claude](https://platform.claude.com/docs/en/models/overview), [CLI Claude](https://code.claude.com/docs/en/cli-reference). [OpenSpec e aceitação](../openspec/changes/isolated-agent-stages/tasks.md).
