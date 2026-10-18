# Pacote automatizado para revisão manual de PR

No modo transitório de revisão manual, o workflow `Manual PR review packet` produz um **resumo informativo** na página da execução em GitHub Actions para cada novo PR ou atualização. Não altera PRs, não adiciona aprovação, não modifica labels e não executa merge.

Informações apresentadas:
- SHA da revisão, autor, quantidade de arquivos e resumo de alterações.
- Classificação **heurística por caminho**: R2 para workflows/infra/segurança/migrações/políticas; R2-review para manifests/lockfiles; R1-candidate para demais caminhos.
- Checklist para sua análise efetiva: diff, testes, impacto, reuso, rollback, aprovações e proteção da branch.

## Segurança
Usa `pull_request_target` somente para consultar metadados de PR via token com permissões de leitura. O checkout é da **branch padrão confiável**, nunca do código vindo do PR. Nenhuma credencial externa é fornecida; não executa testes nem scripts do PR. PRs vindos de forks e informações fornecidas por colaboradores continuam não confiáveis.

O relatório não consulta automaticamente o resultado dos testes nem comprova ausência de vulnerabilidades. A classificação é apenas um alerta e **não substitui revisão manual**. O SHA é consultado de novo ao final, para detectar mudanças durante a coleta.

## Como usar
Abra **Actions → Manual PR review packet → execução do PR → Summary**, verifique o SHA, siga o checklist e confira os checks reais no PR. Depois, faça o merge manualmente conforme a política vigente.

Também é possível executar manualmente o workflow informando um número de PR; o relatório continua somente leitura. Para reproduzir o resumo localmente:

```bash
GH_TOKEN="$(gh auth token)" python3 scripts/manual_pr_review_packet.py --repo leandroclf/product-platform --number 20
```

O pipeline de revisão independente e GitHub Apps continua pendente; consulte `docs/MANUAL-REVIEW-TRANSITION.md`.
