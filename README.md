# Product Platform

Repositório único da plataforma de produtos: contratos e políticas, runtime reutilizável, geração de propostas e time de agentes de engenharia. Os produtos vivem em repositórios próprios e consomem o harness como artefato de release imutável. Decisão: [ADR 004](packages/kit/docs/adr/004-platform-monorepo.md).

| Pacote | Papel | Depende de | Release |
| --- | --- | --- | --- |
| [`packages/kit`](packages/kit) | Contratos, registry de capacidades, políticas, skills e conformance | nenhum | `kit-v*` (quando houver) |
| [`packages/harness`](packages/harness) | Runtime embutido nos produtos: identidade, planos, entitlements, eventos, pagamentos, economics, observabilidade | kit | `harness-v*` (artefato com `SHA256SUMS`) |
| [`packages/cli`](packages/cli) | Transforma uma ideia em proposta revisável e gera o handoff de capacidades | kit | `cli-v*` |
| [`packages/engineering-team`](packages/engineering-team) | `ai-team`: plan, implement, validate e review isolados no repositório alvo | kit | `engineering-team-v*` (quando houver) |
| [`packages/design-system`](packages/design-system) | Tokens e ativos visuais institucionais, adotados opt-in pelos produtos | nenhum | Distribuição versionada pendente |

## Regras

- O grafo de dependências está em [`platform-packages.json`](platform-packages.json) e é verificado por `scripts/check-package-boundaries.py` em todo PR. O kit é folha.
- Cada pacote tem CI próprio, filtrado por caminho (`.github/workflows/<pacote>.yml`). Uma mudança em `packages/kit/contracts/product-event/` também executa o CI do harness contra o fixture canônico.
- Produtos nunca dependem do código-fonte deste repositório: fixam um release do harness pelo checksum do artefato.
- A esteira de entrega (gates G0 a G6) está em [`packages/kit/docs/PLATFORM-DELIVERY-FLOW.md`](packages/kit/docs/PLATFORM-DELIVERY-FLOW.md).
- A baseline verificada e as próximas etapas estão em [`packages/kit/docs/PLATFORM-READINESS.md`](packages/kit/docs/PLATFORM-READINESS.md).

## Verificação local

```bash
python3 scripts/check-package-boundaries.py
(cd packages/kit && node scripts/validate-architecture.cjs && python3 scripts/validate-platform-handoff.test.py)
(cd packages/harness && PRODUCT_EVENT_CASES=$PWD/../kit/contracts/product-event/fixtures/compatibility-cases.json npm run validate)
(cd packages/engineering-team && python3 -m unittest discover -s tests/unit)
(cd packages/cli && pip install -e '.[dev]' && pytest)
```
