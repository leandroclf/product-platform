# Isolated plan

Plan ID: 71b4d36fc7e4f7bfb7094edeac2c583a3a4e9f5a0b094e289bb71e07f68abc50
Planning HEAD: d40fa032e490ad6eb5192482b949d978af122056
Risk: R2

## Assumptions

- O HEAD confirmado corresponde ao SHA de planejamento; seu pai é dc8762aa696ad15587458f734d0f40ad1e8f30a3. A revisão final deve abranger a correção original e quaisquer ajustes posteriores.
- O operador autorizou este trabalho R2. Não é necessária nova aprovação para o escopo local solicitado.
- /work/AGENTS.md está presente. Não foram encontrados AGENTS.md específicos em scripts/ ou tests/; aplicam-se as instruções da raiz.
- /handoff está vazio; capability_decisions deve permanecer vazio.
- O OpenSpec da raiz trata de outra tarefa documental; os requisitos desta revisão vêm do pedido atual, da issue #120, do código e da documentação de governança.
- A issue #120 exige também evidência operacional agendada e pós-merge. Esses critérios permanecem pendentes por estarem fora da autorização atual.
- A inspeção foi estática; nenhum teste foi executado nesta etapa. A documentação do catálogo ainda descreve autenticação incompatível com a nova consulta anônima.

## Validation

- Somente nas etapas posteriores ao planejamento, executar os comandos nativos abaixo com saída condensada via rtk, isolamento e credenciais removidas.
- python3 -m unittest discover -s tests -p test_portfolio_governance.py -v
- python3 -m unittest discover -s tests -p 'test_*.py' -v
- python3 scripts/test_check_package_boundaries.py
- python3 scripts/check-package-boundaries.py
- python3 scripts/test_handoff_contract.py — inclui testes de catálogo, pacote editorial e intake; preparar previamente as dependências de requirements-validation.txt.
- Inspecionar o diff e executar git diff --check; confirmar escopo, SHA final e correspondência entre código validado e código revisado.
- Se houver checks remotos existentes, consultar somente seus resultados e SHAs; ausência de status não significa sucesso e não autoriza disparar workflows.
- Preservar evidência local da revisão independente final e registrar separadamente a prova operacional ainda não realizada.
