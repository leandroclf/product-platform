# Fila verificável do backlog para o ai-team

O script `scripts/backlog_candidate_queue.py` prepara, sem mutações, uma fila determinística de issues abertas com a label `agent-candidate`. Reutiliza o contrato `autonomy-task` e valida apenas candidatos R0/R1 com ciclos limitados.

## Prioridade e seleção

A ordem de prioridade é `priority-p0`, `priority-p1`, `priority-p2` e sem prioridade. Dentro de cada grupo, R0 aparece antes de R1, seguido do número da issue crescente. Mais de uma label de prioridade causa rejeição. Issues fechadas, PRs e itens sem `agent-candidate` ficam fora da fila; corpos inválidos aparecem em `rejected`.

Exemplo para o Linux com `gh` autenticado:

```bash
python3 scripts/backlog_candidate_queue.py --repo leandroclf/product-platform --limit 10 --output candidate-queue.json
python3 -m unittest discover -s tests -p 'test_backlog_candidate_queue.py' -v
```

A saída registra SHA256 da tarefa, URL, repositório-alvo, prioridade e ciclos máximos. São explicitamente `PREVIEW_ONLY`, `execution_allowed: false`; não fornecem credencial, comando executável nem autorização para merge.

## Continuidade do fluxo

Para cada issue elegível, a rotina `Agent candidate preview` já existente pode gerar o artefato próprio; depois, `verified_ai_team_handoff.py` e `local_ai_team_launcher.py` preparam e, somente com autorização explícita no Linux, iniciam o `ai-team`. Este seletor **não** promove issues a `ready` nem inicia os modelos. Deve-se revalidar o estado e o conteúdo da issue no momento de usá-la, pois o snapshot pode ficar obsoleto.

Não existe conexão automática dos agendamentos ChatGPT a este script, nem execução autenticada dos CLIs nesta sessão. Sua revisão humana dos PRs continua obrigatória. Consulte `docs/MANUAL-REVIEW-TRANSITION.md` e a issue central #12.
