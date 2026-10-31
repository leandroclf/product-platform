# Bootstrap da operação autônoma — configuração externa

Esta etapa precisa de permissões administrativas no GitHub. Os workflows não criam secrets, GitHub Apps nem rulesets automaticamente.

## Identidades e permissões
1. Criar GitHub App **executor** com permissões mínimas para branches e PRs nos repositórios selecionados.
2. Criar GitHub App **revisor** com permissão para revisar PRs; instalar somente nos repositórios autorizados. Usar identidade distinta da execução.
3. Criar identidade **integrador** com permissão para habilitar auto-merge, sem bypass de rulesets.
4. Configurar variável de repositório `AGENT_TRUSTED_REVIEWERS` com os logins reais dos revisores permitidos, separados por vírgula. Nunca incluir o executor.
5. Opcionalmente configurar `PORTFOLIO_READ_TOKEN` somente para leitura do inventário autorizado; ele nunca é usado para escrever na issue central. A leitura do inventário público funciona sem esse token e declara cobertura pública/parcial. Escritas na issue usam o `GH_TOKEN` herdado pelo workflow. Para merge, usar o secret `INTEGRATOR_APP_PRIVATE_KEY` e a variável `INTEGRATOR_APP_ID`; o workflow cria um token temporário limitado a `pull_requests:write` e ao repositório atual.

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

## Status operacional
- Executor, revisor e integrador foram criados e instalados somente em `leandroclf/product-platform`.
- A chave privada e o ID do integrador estão configurados no repositório como secret e variável. O workflow usa token temporário e escopado; a revisão de segurança desse workflow ainda precisa entrar na branch padrão.
- O auto-merge nativo está habilitado. O ruleset `main-autonomy-minimum` está ativo, sem bypass, e exige os checks `boundaries`, `offline-safety-tests` e `independent-review-gate`.
- O ruleset ainda permite zero aprovações e não invalida aprovações após novos pushes. O modo continua manual e `AGENT_TRUSTED_REVIEWERS` não está configurado.
- `PORTFOLIO_READ_TOKEN`, execução autenticada do avaliador técnico, piloto ponta a ponta e rollout continuam pendentes.

### Atualização de 2026-10-23

O estado descrito acima é o registro inicial do bootstrap. Desde então, os PRs
#100, #92, #94, #95, #96 e #98 foram analisados independentemente no SHA atual e
integrados com os checks. As allowlists reais, o modo independente e o ruleset
com aprovação obrigatória/descarte após push foram configurados. O App revisor
precisa de instalação com escrita de conteúdo para contar na aprovação nativa,
mas seu token de trabalho continua limitado a conteúdo/checks de leitura e
reviews de escrita. O integrador precisa de `contents:write` para a integração.

As chaves migraram para environments restritos à `main`. O piloto R1, a remoção
das cópias gerais e a execução persistente ainda devem ser verificados pelo
procedimento em [AUTOMERGE-OPERATIONS.md](AUTOMERGE-OPERATIONS.md). A configuração
não demonstra, por si só, operação autônoma ou rollout nos demais produtos.
