# Política de integração autônoma

## Objetivo
Permitir merges sem revisão humana rotineira, usando um revisor especializado independente do executor, sem contornar proteções de branch.

## Separação de funções
- Executor: implementa mudanças em branch e abre PR.
- Revisor: processo e credencial distintos; analisa diff, contratos, segurança, arquitetura, testes e riscos; registra revisão formal no GitHub.
- Gate: verifica aprovação por identidade distinta no SHA atual e bloqueia caminhos críticos.
- Integrador: somente após checks obrigatórios e branch protection, solicita auto-merge pelo GitHub (a configurar).
- Auditor: registra evidências, resultados e rollback.

## Estado e limites
Executor, revisor e integrador estão instalados somente em `leandroclf/product-platform`. A credencial do integrador foi configurada como secret/variável do repositório, e o auto-merge nativo está habilitado. O ruleset `main-autonomy-minimum` está ativo sem bypass e exige os checks `boundaries`, `offline-safety-tests` e `independent-review-gate`.

O ruleset ainda exige zero aprovações e não descarta aprovações antigas após um push. O modo permanece manual, sem allowlist confiável e sem avaliador especializado autenticado. O App revisor, por si só, apenas fornece uma identidade: não analisa código. O workflow atualizado para usar o token do integrador e executar código confiável da branch padrão ainda precisa ser revisado e integrado. A aprovação GitHub isolada não comprova qualidade técnica.

## Política de risco
- R0: documentação e análise; podem ser automatizadas.
- R1: código reversível, com testes e revisão independente; elegível para auto-merge depois de configurar o integrador.
- R2: infraestrutura, permissões, dependências críticas e segurança; exige política reforçada.
- R3: produção, exclusão de repositórios, dados e operações irreversíveis; não elegível para auto-merge nesta fase.

## Pré-requisitos antes de ativar merges
1. Identidades separadas para executor e revisor (GitHub Apps ou contas autorizadas), sem autoaprovação.
2. Branch protection com checks obrigatórios e revisão exigida; impedir bypass.
3. Testes e revisão obrigatórios no SHA atual; cancelar aprovação quando o PR mudar.
4. GitHub auto-merge habilitado no repositório; nunca usar merge forçado.
5. Runner isolado e credenciais de escopo mínimo para o executor.
6. Piloto validado com PR reversível e rollback, antes da expansão progressiva.
7. Adotar workflows por repositório após inspecionar os checks e as políticas de cada produto.

A autorização operacional do proprietário não substitui as proteções de segurança nem comprova que os pré-requisitos foram satisfeitos.

## Próximos passos para ativação
- Integrar o workflow revisado sem contornar checks; confirmar a criação de token temporário com escopo apenas `pull_requests:write`.
- Conectar um avaliador real e independente ao App revisor; ele deve analisar diff, testes, riscos e HEAD antes de enviar APPROVED.
- Configurar os logins efetivos em `AGENT_TRUSTED_REVIEWERS` e definir revisão obrigatória com descarte de aprovações antigas após push.
- Executar piloto reversível, demonstrando bloqueio antes da revisão, checks, auto-merge nativo e trilha de auditoria.
- **Atenção:** workflows, políticas, infraestrutura e `AGENTS.md` são mudanças R2. O gate atual bloqueia esses caminhos; o bootstrap precisa passar por revisão e checks explícitos, sem bypass.
