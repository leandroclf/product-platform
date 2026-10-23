# Pendência administrativa — executar no PC Linux

**Estado em 2026-10-23:** autenticação Linux e configuração de Apps/allowlists/ruleset realizadas. Recuperação dos PRs protegidos demonstrada. Piloto R1 e ativação persistente do worker ainda exigem evidência; não tratar a operação autônoma como concluída por configuração apenas. Procedimento atual: [AUTOMERGE-OPERATIONS.md](AUTOMERGE-OPERATIONS.md).

## Ações para o operador com Codex
- Autenticar `gh auth login` localmente e verificar escopo e repositórios.
- Criar/instalar identidades independentes para executor, revisor e integrador, com menor privilégio.
- Para merge, usar `INTEGRATOR_APP_ID` e `INTEGRATOR_APP_PRIVATE_KEY`; `AGENT_MERGE_TOKEN` é legado. `PORTFOLIO_READ_TOKEN` atende o inventário do portfólio. As allowlists de revisores devem conter logins reais.
- Ativar auto-merge, rulesets, checks obrigatórios e revisão independente no GitHub.
- Conectar CLIs autenticados ao `packages/engineering-team` e implementar o agente revisor real; a aprovação GitHub isolada não comprova revisão técnica.
- Executar piloto de PR R1, demonstrando bloqueio antes da revisão, revisão independente, CI, auto-merge, rollback e evidências.
- Expandir aos demais repositórios em lotes após o piloto, sem contornar regras.

## Trabalho possível antes do PC
- Testes unitários offline para o gate de revisão, executados em CI.
- Inventário agendado já preparado, porém exige token para execução.
- Documentação e contratos de risco; nenhum token ou identidade fictícia será inserido.
- Sem deploy, merge automático de mudanças críticas ou configuração simulada.

## Critério de desbloqueio
Configuração administrativa real + demonstração ponta a ponta registrada no repositório.
