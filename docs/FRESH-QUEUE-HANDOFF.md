# Fila do backlog → handoff atualizado do ai-team

O script `scripts/fresh_queue_handoff.py` liga a fila priorizada às entradas do executor local sem iniciar agentes e sem conceder permissões. Ele seleciona uma issue explícita do artefato, consulta o estado **atual** do GitHub e compara o SHA256 da tarefa com o snapshot da fila.

## Procedimento no Linux

1. Baixar o artefato `backlog-candidate-queue` de **Actions → Backlog candidate queue**; inspecionar previamente a issue, sua fonte e o risco real.
2. Selecionar uma issue presente no JSON e gerar a prévia:

```bash
GH_TOKEN="$(gh auth token)" python3 scripts/fresh_queue_handoff.py \
  --queue candidate-queue.json --issue 28 --output candidate-preview.json
```

3. Gerar o pedido verificado:

```bash
python3 scripts/verified_ai_team_handoff.py \
  --preview candidate-preview.json --output ai-team-request.json
```

4. Usar a prévia **sem executar** o `ai-team`:

```bash
python3 scripts/local_ai_team_launcher.py \
  --preview candidate-preview.json --target /caminho/do/repositorio
```

A execução posterior exige `--execute` e `--confirm-hash`, com `ai-team doctor`, CLI autenticado e preflight local. O operador continua responsável por autorizar essa execução e revisar o PR final.

## Restrições e prevenção de tarefas obsoletas

- Consulta novamente a issue no GitHub; rejeita item fechado, sem `agent-candidate`, alterado desde a fila ou com destino e classificação de risco divergentes.
- Não usa `gh issue edit`, não atualiza labels e não abre PR.
- O checksum SHA256 verifica **consistência**, não procedência ou confiabilidade: confirme artefato/execução de origem no GitHub.
- Mesmo com validação recente, a issue pode mudar antes da execução no Linux; para tarefas sensíveis, reconsultar a origem e refazer a prévia imediatamente antes do `--execute`.
- A coleta de fila é somente leitura; a issue #28 demonstra o contrato, e este PR implementa seu critério de aceite.
- A execução autenticada dos modelos segue pendente até validação operacional do Linux. Revisão e merge dos PRs continuam manuais.

## Proteção adicional antes de `ai-team run`

Ao usar `scripts/local_ai_team_launcher.py --execute --confirm-hash ...`, o launcher agora consulta **novamente a issue original no GitHub** duas vezes: antes de executar `ai-team doctor` e logo antes de `ai-team run`. Exige issue aberta, label `agent-candidate`, URL canônica e SHA256 da tarefa idêntico ao preview. Se a consulta falhar, a issue for encerrada ou a tarefa mudar, nenhuma etapa de implementação será iniciada.

O modo padrão sem `--execute` continua offline e somente informativo. Essa verificação reduz o intervalo entre validação e uso; não torna o artefato confiável por si só e não protege contra alterações posteriores ao último GET. Não requer token de escrita e **não aciona merge nem revisão automática**.
