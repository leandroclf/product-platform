# Isolated plan

Plan ID: 5f05291ab059ec13936e36d8e7f65cd01f02cfc2ccc20925b3600b785181eb71
Planning HEAD: 9c1a5c429c49406b1d484f54f3926c3531486e15
Risk: R1

## Assumptions

- HEAD confirmado no SHA informado, com árvore limpa. Este estágio realizou apenas inspeção estática; não executou código nem checks do checkout.
- AGENTS.md da raiz, do harness e do kit estão presentes. O catálogo PRODUCT-KPI-CATALOG.md e o roadmap CI-01 fornecem o contexto funcional; o OpenSpec encontrado na raiz trata de outra tarefa.
- /handoff está vazio; capability_decisions deve permanecer vazio. O trabalho corrige capacidades existentes nos donos atuais: semântica no kit e cálculo no harness.
- Não foi localizado um conjunto de dados ou adapter que comprove a primeira baseline operacional CI-01. A baseline histórica de validação da plataforma não comprova esses KPIs; essa lacuna deve ser documentada, sem impedir a revisão local.
- A documentação anuncia o subcaminho TypeScript /observability, mas package.json exporta apenas a raiz, que já disponibiliza calculateKpi.
- Os manifests locais indicam versão 0.2.1; presença de código no checkout não comprova disponibilidade no artefato publicado. Nenhuma versão será alterada.
- Implementação, checks offline e revisão independente serão executados pelas etapas existentes do ai-team, respeitando o teto R1.

## Validation

- Na etapa de execução, reproduzir os casos adicionados contra o código anterior às correções e registrar quais falham; não executar código durante PLAN.
- Em packages/harness: rtk npm run build; depois rtk node --test dist/observability/kpis.test.js e PYTHONPATH=packages/python rtk python3 -m unittest discover -s packages/python/tests -p test_kpis.py -v.
- Verificar importação e chamada pelas APIs públicas documentadas: calculateKpi na raiz de @leandroclf/product-platform-harness e calculate_kpi em product_platform_harness.
- Em packages/harness: PRODUCT_EVENT_CASES="$PWD/../kit/contracts/product-event/fixtures/compatibility-cases.json" rtk npm run validate, no runner offline existente.
- Na raiz: rtk python3 scripts/check-package-boundaries.py e rtk git diff --check.
- Inspecionar o diff e reconciliar README, catálogo e fixtures; confirmar que resultados sintéticos não aparecem como baseline real.
- Vincular checks e pareceres ao SHA final. A revisão independente deve incluir o incremento existente desde o pai de 9c1a5c429c49406b1d484f54f3926c3531486e15, além das correções posteriores ao planejamento, com a implementação TypeScript e o catálogo como contexto.
