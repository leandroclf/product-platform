# Ingestão das rotinas de inteligência no backlog central

O script `scripts/portfolio_backlog_intake.py` recebe uma lista JSON de achados **curados** dos radares de arquitetura, governança, segurança, inteligência de negócios ou revisão executiva e prepara issues `candidate` no `product-platform`.

Os achados usam os campos de `docs/AUTONOMOUS-TASK-HANDOFF.md`: `source`, `target_repository`, `problem`, `evidence_url`, `acceptance_criteria`, `risk`, `rollback`, `max_cycles`. Só são aceitos R0/R1, 1–3 ciclos e evidência HTTPS. O lote inteiro é validado antes de qualquer escrita.

## Executar

Salvar os achados em um arquivo JSON com uma lista de tarefas nesse esquema. Usar `gh auth login` quando disponível. Antes de escrever, fazer prévia:

```bash
python3 scripts/portfolio_backlog_intake.py --findings findings.json
```

Para criar apenas issues ainda não identificadas:

```bash
python3 scripts/portfolio_backlog_intake.py --findings findings.json --apply
```

A deduplicação utiliza SHA256 de fonte, repositório destino e URL da evidência. Repetições da mesma evidência no mesmo domínio são ignoradas, mesmo com pequenas alterações de descrição. A consulta contempla issues abertas e encerradas para evitar recriar pendências antigas. Revisar manualmente possíveis casos em que a mesma evidência represente problemas distintos. **Não existe escrita em modo padrão.**

## Limites e continuidade

- O script usa `gh api` com credenciais GitHub já presentes no ambiente e cria apenas **issues novas**, nunca atualiza ou apaga issues, não atribui `ready`, não adiciona `agent-candidate`, não executa modelos, não abre PRs e não faz merge.
- Issues criadas continuam dependentes de triagem e da cadeia existente `agent-candidate` → `candidate-preview` → `verified_ai_team_handoff` → `local_ai_team_launcher`, com os controles próprios de cada etapa.
- Os radares agendados do ChatGPT **não escrevem automaticamente** arquivos neste repositório; a exportação dos achados estruturados é uma fronteira ainda não automatizada.
- Esta implementação não substitui planejamento OpenAI, execução Claude, validação OpenAI ou revisão humana dos PRs. O fluxo de revisão manual permanece em `docs/MANUAL-REVIEW-TRANSITION.md`.

**Atenção:** GitHub não fornece transação atômica entre vários POSTs: uma interrupção pode deixar um lote parcialmente criado. Repetir após consultar o GitHub deduplica issues já registradas. Não iniciar lotes simultâneos com as mesmas evidências.
