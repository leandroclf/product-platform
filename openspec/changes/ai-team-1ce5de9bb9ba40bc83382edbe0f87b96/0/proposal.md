# Objective

Revisar e corrigir o incremento local da issue #123, demonstrando paridade TypeScript/Python dos seis KPIs, documentação correta, limites explícitos da baseline real parcial, checks do harness aprovados e revisão independente vinculada ao SHA final.

## Original request

Revise o incremento local da issue #123: confira a paridade TypeScript/Python do catálogo de KPIs, os limites do primeiro baseline real e a documentação. Execute os checks do harness, corrija findings concretos, registre que a baseline real segue parcial e finalize revisão independente no SHA final. Não publique release, não faça push, PR, deploy ou operação externa.

## Out of scope

- Release, publicação, push, PR, merge, deploy ou operação externa.
- Coleta de dados reais, acesso a credenciais e alterações em repositórios consumidores.
- Alterações em dependências, manifests, schemas, ProductEvent, ledger, registry, infraestrutura ou pipelines.
- Novos serviços, coletores ou orquestradores; conclusão integral de CI-01 sem evidência operacional.

## Acceptance

- AC1: TypeScript e Python produzem resultados equivalentes para os seis KPIs do catálogo, incluindo fórmulas, unidades, moeda, contexto e cobertura. Ausência de dados, denominador vazio e zero observado permanecem distintos; margem negativa e média monetária fracionária continuam válidas.
- AC2: Findings de comportamento são reproduzidos e corrigidos com regressões relevantes. Ambos os runtimes rejeitam formatos inválidos, valores não finitos, negativos ou inseguros, overflow da soma, numeradores de taxas acima da coorte, moeda inválida e janelas inválidas. Entradas malformadas não se tornam resultados vazios ou zeros.
- AC3: README e catálogo correspondem às APIs e exports reais, explicam as responsabilidades do consumidor e distinguem disponibilidade local de adoção via release imutável. O import TypeScript documentado funciona pelo export existente; nenhuma publicação é alegada.
- AC4: A documentação registra expressamente que a baseline real segue parcial. Para cada KPI, identifica evidência disponível ou ausência dela e as pendências de fonte, produto/ambiente, janela, coorte, deduplicação e reconciliação. Explicita WIP, acompanhamento de incidentes, decisões pendentes, custos não atribuídos e demanda comprovada quando pertinentes. Não inventa medições, zeros, metas ou conclusão de CI-01.
- AC5: npm run validate conclui build, testes TypeScript, unittest Python e testes PostgreSQL/PGlite com sucesso, usando o fixture canônico de ProductEvent. O check de fronteiras passa. Evidências identificam comandos, resultados e código validado; checks ausentes ou falhos não são apresentados como aprovados.
- AC6: Validação e revisão independente finais referenciam o HEAD final e o plano correto, cobrem todos os critérios e registram evidências e limitações. Não restam findings MEDIUM, HIGH ou CRITICAL abertos; alterações posteriores invalidam o parecer até nova revisão.
- AC7: O diff permanece restrito às correções locais R1 de KPIs, testes e documentação relacionada. Não há alterações em dependências, contratos, pipelines ou artefatos publicados, nem operações externas. O relatório distingue conclusão da revisão local da baseline operacional ainda parcial.
