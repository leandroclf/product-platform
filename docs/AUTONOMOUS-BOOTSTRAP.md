# Bootstrap da operação autônoma — configuração externa

Esta etapa precisa de permissões administrativas no GitHub. Os workflows não criam secrets, GitHub Apps nem rulesets automaticamente.

## Identidades e permissões
1. Criar GitHub App **executor** com permissões mínimas para branches e PRs nos repositórios selecionados.
2. Criar GitHub App **revisor** com permissão para revisar PRs; instalar somente nos repositórios autorizados. Usar identidade distinta da execução.
3. Criar identidade **integrador** com permissão para habilitar auto-merge, sem bypass de rulesets.
4. Configurar variável de repositório `AGENT_TRUSTED_REVIEWERS` com os logins reais dos revisores permitidos, separados por vírgula. Nunca incluir o executor.
5. Configurar secrets `PORTFOLIO_READ_TOKEN` (leitura do portfólio e escrita na issue central) e `AGENT_MERGE_TOKEN` (permissões mínimas de PR/merge). Preferir credenciais temporárias de GitHub App a tokens pessoais de longa duração.

## Rulesets e gates
- Exigir CI e o status `independent-review-gate` na branch principal.
- Exigir aprovação independente, invalidar aprovações após push e bloquear force push.
- Habilitar auto-merge nativo; não permitir bypass do agente integrador.
- O gate R1 bloqueia alterações em workflows, segurança, infra, migrações e AGENTS.md; estas exigem trilha reforçada.

## Teste de aceitação
1. Abrir PR de documentação não crítica criado pela identidade executora.
2. Confirmar falha do gate antes de aprovação.
3. Executar revisão especializada real (diff, testes, segurança, arquitetura) sob identidade revisora e registrar APPROVED no SHA exato.
4. Aplicar `agent-auto-merge` apenas ao PR elegível.
5. Confirmar que o GitHub integra somente depois de todos os checks e registra trilha de auditoria.
6. Alterar o SHA, pedir mudanças ou tocar caminho crítico e confirmar bloqueio.
7. Repetir o piloto em um segundo repositório somente após sucesso completo.

## Status
Implementado: inventário, gate, workflow opt-in de auto-merge e allowlist de revisores.
Não implementado: instalação de Apps, configuração de secrets/rulesets, invocação autenticada do agente revisor, validação de PR piloto, execução autônoma de mudanças e rollout para todos os repositórios.
