# Auditoria de prontidão da evolução autônoma

Ferramenta local e somente leitura para o momento em que o PC Linux estiver disponível. Não configura, cria nem altera GitHub Apps, tokens, rulesets, PRs ou repositórios.

```bash
gh auth login
python3 scripts/audit_autonomy_readiness.py --repo leandroclf/product-platform
```

A saída JSON relata `pass`, `fail` ou `unknown`. A execução retorna código 2 enquanto houver pendências. O script verifica metadados de secrets (nomes apenas), variável de revisores, autorização de auto-merge, proteções legadas de `main` e disponibilidade da lista de rulesets. Não exibe nem requer valores de segredos no chat.

**Limitações essenciais:** APIs administrativas podem responder 403/404, tratados como `unknown`; a presença de uma credencial não prova sua validade. Rulesets exigem revisão detalhada de aplicabilidade, bypass e enforcement, não inferida de uma listagem. Mesmo com todos os ajustes no GitHub, não é possível certificar identidade distinta de agentes, qualidade técnica da revisão, execução fim a fim ou rollout sem testes reais. Portanto a auditoria **não pode** declarar `ready_for_autonomous_merge=true` apenas a partir dos metadados. Isto é intencional: dados ausentes nunca são sucesso.

Para completar a validação, siga `docs/AUTONOMOUS-BOOTSTRAP.md`, `docs/AUTONOMY-PENDING-PC.md`, execute o piloto real e anexe os links dos workflows, revisões, commits e evidências na issue [#12](https://github.com/leandroclf/product-platform/issues/12).

A rotina pode ser executada repetidamente depois de cada configuração administrativa; cada falha traz o próximo requisito verificável, evitando tentativas de merge às cegas.
