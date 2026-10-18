# Pendência administrativa — executar no PC Linux

**Estado:** bloqueado por configuração administrativa e autenticação interativa; não tratar como concluído.

## Ações para o operador com Codex
- Autenticar `gh auth login` localmente e verificar escopo e repositórios.
- Criar/instalar identidades independentes para executor, revisor e integrador, com menor privilégio.
- Configurar `PORTFOLIO_READ_TOKEN`, `AGENT_MERGE_TOKEN` e `AGENT_TRUSTED_REVIEWERS` com logins reais.
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
