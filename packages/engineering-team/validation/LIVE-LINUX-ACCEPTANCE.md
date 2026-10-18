# Aceitação operacional do ai-team no Linux — evidências do piloto

O item P0 da [auditoria de engenharia](https://github.com/leandroclf/product-platform/issues/34) exige **uma tarefa real com provedores autenticados**, não somente o CI ou fixtures controladas. Este roteiro mantém a revisão e o merge manuais.

## Pré-requisitos

- No Linux do operador, instalar/revalidar o `ai-team` conforme [fluxo local](../docs/LOCAL-LINUX-WORKFLOW.md), incluindo `setfacl` com suporte a POSIX ACL, Docker e imagem de testes offline.
- Autenticar os quatro estágios separadamente: `ai-team login atlas --stage plan`, `ai-team login argus`, `ai-team login sentinel` e `ai-team login atlas --stage review`. `ai-team doctor` deve retornar sucesso.
- Configurar `ai-team init` com imagem e **checks reais** na raiz do alvo, branch nomeada, checkout limpo e remoto GitHub verificado; executar `ai-team models` para conferir o catálogo da conta. Não enviar credenciais ou conteúdo dos volumes ao GitHub/chat.

## Piloto supervisionado

1. Selecionar uma issue aberta de risco baixo, com aceites verificáveis e `agent-candidate`. A ferramenta `scripts/run_backlog_pilot.py` da raiz do monorepo pode consultar uma candidata e exigir `--execute --confirm-hash` no momento de executar. Alternativamente, executar `ai-team run 'mudança pequena, reversível e verificável'` no alvo.
2. Inspecionar os registros locais do `ai-team`: `ai-team status`, `ai-team report`, `ai-team models`, `ai-team logs --stage validate` e `ai-team logs --stage review`. O CLI deve chegar a `REVIEWED`, com testes offline aprovados, dois pareceres no HEAD e plano exatos, sem exceções.
3. Executar a verificação local **somente leitura**:

```bash
cd ~/projetos/product-platform/packages/engineering-team
python3 scripts/verify_live_pilot.py \
  --task-dir ~/.local/state/ai-team/runs/ID_DE_32_HEX \
  --output ~/ai-team-pilot-summary.json
```

Um resultado `artifact_checks_pass: true` indica apenas que os **artefatos locais** passaram por validações estruturais: plano, HEAD, quatro estágios registrados, testes e dois pareceres. O relatório **sempre** mantém `authenticated_provider_execution_verified: false` e `production_certified: false`. Uma pessoa deve inspecionar os logins, provedores, modelos efetivamente utilizados e resultados no ambiente onde rodaram. `resolved_model: null` **não** deve ser convertido em modelo confirmado.

4. Após conferir diff, evidências e testes, usar `ai-team deliver <task-id> --pr` para publicar um PR draft. Verificar CI e revisar antes de fazer merge **manualmente**. Não realizar deploy neste piloto.

## Proteção das evidências

`state.json`, saídas dos provedores, prompts, paths e relatórios HTML podem conter código interno, dados e informações sensíveis. **Não publicar arquivos brutos nem logs**. O sumário JSON inclui apenas identificador da tarefa, SHA, estado, ciclos, provedores/estágios esperados, modelo solicitado e razões de bloqueio; revisar mesmo assim antes de compartilhá-lo.

## Gate de aceite P0

Um relatório estrutural aprovado sozinho não fecha o P0. É necessário registrar manualmente: conta/CLI real por estágio, nome do modelo efetivo observado, execução das quatro etapas, testes executados sobre o HEAD, evidências do PR, diff inspecionado, resolução de achados, tempo/custo/cotas quando observáveis, ausência de efeitos externos indevidos, e decisão humana de aceitação.

Teste de falhas em etapa separada: simular ausência do provedor, saída inválida e uma tarefa interrompida; confirmar que não houve reexecução, aprovação ou merge silenciosos. Não mudar rulesets nem habilitar auto-merge.
