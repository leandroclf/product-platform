# Proposta verificável → handoff inerte para ai-team

O próximo estágio da integração dos cinco radares é aceitar **propostas estruturadas** antes da execução. O script `scripts/autonomy_backlog.py` transforma um corpo de issue em JSON com SHA256, porém **não executa agentes, não aprova PRs e não faz merge**.

Exemplo de bloco a incluir no corpo da issue:

```autonomy-task
{
  "source": "architecture",
  "target_repository": "leandroclf/product-platform",
  "problem": "Link legado aponta para repositório arquivado",
  "evidence_url": "https://github.com/leandroclf/agents-workspace",
  "acceptance_criteria": ["Referência aponta para packages/engineering-team", "Nenhuma nova dependência foi criada"],
  "risk": "R1",
  "rollback": "Reverter o commit",
  "max_cycles": 2
}
```

Execute somente para prévia offline:

```bash
python3 scripts/autonomy_backlog.py --body-file issue.md --issue-url https://github.com/leandroclf/product-platform/issues/12 --output handoff-preview.json
python3 -m unittest discover -s tests -p 'test_autonomy_backlog.py' -v
```

## Escopo atual
- Valida presença de evidência HTTPS, repositório explícito, critérios de aceite, risco R0/R1, rollback e ciclos limitados.
- Rejeita campos extras para impedir transporte acidental de comandos. A entrada continua **não confiável** mesmo quando válida.
- Produz `PREVIEW_ONLY`, `execution_allowed: false`, estado `awaiting_independent_triage` e hash estável.
- Não resolve automaticamente evidências, contexto do código, permissões, reuso, segurança ou risco real: a triagem e o `ai-team` continuam gates distintos.
- Antes da execução real, integrar classificação de risco, autenticação dos CLIs, sandbox, orçamento, revisão especializada, GitHub Apps e provas de ponta a ponta.

Uma issue marcada `ready` sem validação não basta para conceder permissão de execução ou merge.
