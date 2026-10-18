# Fase transitória: PRs com revisão manual do proprietário

**Objetivo:** continuar desenvolvendo a plataforma e abrindo PRs enquanto GitHub Apps, credenciais e a revisão técnica independente autenticada não foram instalados no PC Linux.

## Modo operacional atual — manual
- Variável opcional GitHub Actions `AGENT_REVIEW_MODE=manual` (ou ausente). A verificação `independent-review-gate` funciona, **nesta fase, somente como um check estrutural**: confere SHA atual e bloqueia alterações nos caminhos críticos definidos pelo gate. Não atesta que houve review humano ou aprovação independente.
- O workflow `Agent auto-merge (opt-in)` não executa no modo manual, inclusive se o PR possuir a label `agent-auto-merge`. **Não habilitar auto-merge por fora da política.**
- Toda integração depende de revisão manual efetiva do diff, dos testes, impacto/custo e do merge feito pelo proprietário no GitHub.
- Manter CI obrigatório, impedir force push e preservar branch protections/rulesets existentes. A existência de um check estrutural verde **não** garante que o merge esteja protegido contra pessoas que tenham permissão de escrita — validar a configuração no GitHub.
- Mudanças em workflows, `AGENTS.md`, segurança, infraestrutura, migrações ou credenciais seguem R2 e não passam pelo gate R1, mesmo com intervenção manual. Essas mudanças demandam verificação reforçada conforme a política de proteção.
- A entrega via agentes locais, quando disponível, pode abrir PR draft; **não configurar etapa de merge automatizado**.

## Quando concluir configuração do PC
1. Configurar GitHub Apps executor, revisor e integrador e tokens temporários apropriados; identidade revisora distinta e autorizada.
2. Validar o revisor técnico efetivo com os quatro estágios do `ai-team`.
3. Instalar proteção nativa GitHub de CI/reviews, stale approvals, sem bypass e confirmar o fluxo em piloto.
4. Configurar variável `AGENT_TRUSTED_REVIEWERS` com identidades reais, e **somente então** mudar `AGENT_REVIEW_MODE` para `independent`.
5. Demonstrar ponta a ponta e auditar a trilha. O gate independent exige revisão do HEAD corrente e a rota de auto-merge volta a ser elegível apenas em modo `independent`.

## Limite
A política manual é transitória e **não constitui aprovação automática, revisão independente nem certificação de produção**. Não tratar o indicador `independent-review-gate` como evidência de revisão técnica enquanto o modo for manual. Trabalhos já planejados permanecem rastreados na issue [#12](https://github.com/leandroclf/product-platform/issues/12).
