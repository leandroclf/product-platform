# Fase transitória: PRs com revisão manual do proprietário

> Registro histórico da transição. Em 2026-10-23, o modo independente e as allowlists reais foram configurados, o ruleset passou a exigir aprovação e descarte após push, e os PRs R2 bloqueados foram revisados e integrados. O piloto R1 e a ativação do worker são acompanhados em [AUTOMERGE-OPERATIONS.md](AUTOMERGE-OPERATIONS.md). Os itens abaixo descrevem a fase anterior, não a configuração atual. R2 continua com revisão e merge manual.

**Objetivo:** continuar desenvolvendo a plataforma e abrindo PRs enquanto GitHub Apps, credenciais e a revisão técnica independente autenticada não foram instalados no PC Linux.

## Modo operacional atual — manual
- Variável opcional GitHub Actions `AGENT_REVIEW_MODE=manual` (ou ausente). A verificação `independent-review-gate` funciona, **nesta fase, somente como um check estrutural**: confere SHA atual e bloqueia alterações nos caminhos críticos definidos pelo gate. Não atesta que houve review humano ou aprovação independente.
- O workflow `Agent auto-merge (opt-in)` não executa no modo manual, inclusive se o PR possuir a label `agent-auto-merge`. **Não habilitar auto-merge por fora da política.**
- Toda integração depende de revisão manual efetiva do diff, dos testes, impacto/custo e do merge feito pelo proprietário no GitHub.
- Manter CI obrigatório, impedir force push e preservar branch protections/rulesets existentes. O ruleset atual não tem bypass e exige três checks, mas permite zero aprovações e não invalida aprovações após push; portanto, ele não impõe revisão humana efetiva.
- Mudanças em workflows, `AGENTS.md`, segurança, infraestrutura, migrações ou credenciais seguem R2 e não passam pelo gate R1, mesmo com intervenção manual. Essas mudanças demandam verificação reforçada conforme a política de proteção.
- A entrega via agentes locais, quando disponível, pode abrir PR draft; **não configurar etapa de merge automatizado**.

## Quando concluir configuração do PC
1. Apps executor, revisor e integrador estão instalados no repositório. O ID e a chave privada do integrador estão configurados, e o workflow revisado precisa ser integrado sem bypass.
2. Validar o revisor técnico efetivo com os quatro estágios do `ai-team`; a identidade do App não substitui essa análise.
3. Ajustar o ruleset para exigir aprovação independente e invalidá-la após push, mantendo os checks e sem bypass.
4. Configurar `AGENT_TRUSTED_REVIEWERS` com logins reais e distintos do executor; **somente então** mudar `AGENT_REVIEW_MODE` para `independent`.
5. Demonstrar ponta a ponta e auditar a trilha. O gate independent exige revisão do HEAD corrente e a rota de auto-merge só se torna elegível em modo `independent`.

## Limite
A política manual é transitória e **não constitui aprovação automática, revisão independente nem certificação de produção**. Não tratar o indicador `independent-review-gate` como evidência de revisão técnica enquanto o modo for manual. Trabalhos já planejados permanecem rastreados na issue [#12](https://github.com/leandroclf/product-platform/issues/12).
