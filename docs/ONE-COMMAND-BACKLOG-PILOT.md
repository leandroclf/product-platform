# Piloto de uma issue do backlog em um comando

A ferramenta `scripts/run_backlog_pilot.py` reduz o caminho de uma issue `agent-candidate` para a entrada do executor existente. **Não introduz novo runtime, gateway ou agente.** Reutiliza os módulos de seleção, leitura atualizada da issue e `local_ai_team_launcher`.

## Pré-requisitos operacionais

É necessário ter um checkout Linux limpo do repositório de destino, `gh` autenticado para **ler** a issue e `ai-team` instalado e configurado no alvo, conforme `packages/engineering-team/docs/LOCAL-LINUX-WORKFLOW.md`.

### 1. Consultar a tarefa sem executar modelos

```bash
cd ~/projetos/product-platform
python3 scripts/run_backlog_pilot.py --issue 32 --target ~/projetos/product-platform
```

O programa lê a issue diretamente no GitHub, exige `open`, label `agent-candidate`, contrato estruturado válido e risco declarado R0/R1. Lê uma segunda vez para detectar alterações durante o preflight e mostra `task_sha256`, repositório e checks necessários.

### 2. Executar deliberadamente apenas após revisar o escopo

```bash
python3 scripts/run_backlog_pilot.py --issue 32 \
  --target ~/projetos/product-platform \
  --execute --confirm-hash SHA256_EXATO_DA_PREVIA
```

O comando delega ao launcher existente, que confere SHA, remote Git, checkout limpo, `ai-team doctor` e verifica o estado da issue novamente antes de chamar `ai-team run`. **Sem `--execute`, nenhum modelo roda.** Se os CLIs autenticados não estiverem disponíveis, o modo de execução é bloqueado.

### 3. Revisar e entregar

Depois que o `ai-team` completar uma tarefa na máquina local, inspecione `ai-team status`, `ai-team report` e os checks. Para produzir PR draft, use o comando oficial `ai-team deliver <task-id> --pr` somente após conferir os artefatos. **Não há entrega automática, revisão independente ativa, merge ou deploy.** O proprietário revisa e faz o merge no GitHub.

## Limitações

O `task_sha256` confirma identidade do conteúdo, não a autoridade ou veracidade da fonte. A classificação de risco do autor precisa ser revisada. Entre a última consulta GitHub e a execução ainda existe uma janela de alteração possível. O resultado impresso do executor deve ser tratado como texto não confiável, não como comprovação de sucesso: use o estado, diff, testes e evidências do próprio `ai-team`.

A issue #32 é a primeira tarefa do backlog para validar essa integração. A implementação deste PR usa GitHub connector e testes offline, **não comprova uma execução real com modelos OpenAI/Claude**. A configuração autenticada do Linux continua pendente.
