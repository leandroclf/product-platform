# Recuperação de merges e autonomia — 2026-10-23

## Evidência inicial

Na inspeção autenticada como `leandroclf`, os PRs #92, #94, #95, #96 e #98
estavam abertos. Todos alteram workflows e o gate R1 os bloqueia antes da
consulta a reviews. O ruleset `main-autonomy-minimum` permanece ativo, sem
bypass, exigindo `boundaries`, `offline-safety-tests` e `independent-review-gate`.

O auto-merge nativo está habilitado e o App integrador está configurado.
`AGENT_REVIEW_MODE`, `AGENT_TRUSTED_REVIEWERS` e a credencial do revisor não
estavam configurados. O ruleset não exigia aprovação nem invalidava reviews
após push. Configuração de App não constitui evidência de análise técnica.

## Correções propostas

- O gate de PR pode avaliar mudanças protegidas somente com
  `ALLOW_SECURITY_REVIEW=true`, fornecido pelo workflow, e aprovação efetiva de
  uma identidade em `AGENT_SECURITY_REVIEWERS`, distinta do autor, no HEAD atual.
  Ausência da allowlist, review obsoleto, autoaprovação e pedidos de mudança
  continuam bloqueando. Renomear um caminho protegido também exige essa rota.
- O integrador não recebe essa permissão nem a allowlist de segurança. R2
  continua fora do automerge e depende de merge manual após revisão e checks.
- O integrador tenta novamente quando `Agent independent review gate` termina
  com sucesso. A resolução consulta o PR atual e exige label `agent-auto-merge`,
  mesma origem, branch padrão, PR aberto, ausência de draft e SHA atual.
  Execução sem associação inequívoca de PR falha; `workflow_dispatch` permite
  nova tentativa explícita com os mesmos controles.
- A solicitação nativa usa `--match-head-commit`; não permite integrar outro SHA
  entre revisão e solicitação. Código do PR e artefatos do executor não são
  executados no job que recebe a credencial do integrador.
- Testes de pinning verificam SHA completo imutável, sem exigir uma revisão
  histórica específica de uma action.
- A auditoria exige a credencial real do App integrador, o modo independente e
  sua allowlist. Reconhece regras efetivamente aplicáveis à `main`, além da
  proteção legada. `PORTFOLIO_READ_TOKEN` é uma dependência do inventário,
  não uma credencial de merge. Evidência operacional ausente segue desconhecida.

## Ativação administrativa e validação

1. Configurar o App `leandroclf-pp-reviewer` com conteúdo/checks somente leitura
   e pull requests com escrita. Guardar a chave em secret, sem inserir em Git,
   prompts, artefatos ou logs. Identidade deve ser distinta do executor/integrador.
2. Executar revisão técnica em sessão isolada e registrar evidência do diff,
   testes, riscos e SHA antes de publicar aprovação pelo App.
3. Configurar `AGENT_SECURITY_REVIEWERS` para os PRs R2 revisados. A integração
   inicial desta política precisa da mesma análise reforçada, checks e merge
   manual; não modificar o ruleset para dispensar checks nem fabricar status.
4. Exigir pelo menos uma aprovação, descarte após push e resolução de discussões
   no ruleset existente, preservando os checks e ausência de bypass.
5. Configurar `AGENT_TRUSTED_REVIEWERS` e `AGENT_REVIEW_MODE=independent` somente
   com revisor efetivo. Criar a label opt-in se ainda não existir.
6. Demonstrar PR R1 bloqueado antes de review, aprovação no SHA atual, checks e
   integração nativa. Demonstrar rejeição de SHA obsoleto, mudanças solicitadas,
   autor igual ao revisor e alterações protegidas na rota do integrador.
7. Só declarar a autonomia operacional após registrar o piloto real e conectar
   o agendamento autenticado do revisor. Um retry automático não executa análise
   técnica por si só.

## Portfólio e legados

Os repositórios `product-platform-harness` e `product-platform-cli` permanecem
arquivados, conforme decisão do proprietário. O conteúdo dos PRs legados já
está presente no monorepo: CI do harness produz tarball/checksum e o CLI já
aceita `rich<16`, `mypy<3` e `pytest-cov<8`. Os PRs legados não são motivo para
reabrir os repositórios nem duplicar manutenção.

No `ai-engineering-control-plane`, os PRs #12 e #13 exigem revisão e CI próprios.
Falhas de scanner devem ser corrigidas ou tratadas pela governança específica;
não são cobertas pela aprovação R1 desta plataforma.

## Rollback

Reverter o commit deste PR e retornar `AGENT_REVIEW_MODE` a `manual` interrompe
novas solicitações do integrador. Solicitações já enfileiradas precisam ser
canceladas explicitamente no GitHub. Não relaxar proteções para executar rollback.
