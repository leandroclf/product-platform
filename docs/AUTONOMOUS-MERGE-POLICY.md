# Política de integração autônoma

## Objetivo
Permitir merges sem revisão humana rotineira, usando um revisor especializado independente do executor, sem contornar proteções de branch.

## Separação de funções
- Executor: implementa mudanças em branch e abre PR.
- Revisor: processo e credencial distintos; analisa diff, contratos, segurança, arquitetura, testes e riscos; registra revisão formal no GitHub.
- Gate: verifica aprovação por identidade distinta no SHA atual e bloqueia caminhos críticos.
- Integrador: somente após checks obrigatórios e branch protection, solicita auto-merge pelo GitHub (a configurar).
- Auditor: registra evidências, resultados e rollback.

## Limites desta entrega
O gate de aprovação independente e o workflow opt-in de solicitação de auto-merge estão implementados. A identidade do agente revisor, sua execução autenticada, as credenciais GitHub App, a configuração de branch protection, a habilitação de auto-merge no GitHub e a adoção nos demais repositórios **ainda não estão configuradas**. O workflow só solicita auto-merge em PRs rotulados `agent-auto-merge`, após verificar aprovação independente e caminhos protegidos. O GitHub deve impor os demais checks obrigatórios. A presença de uma aprovação GitHub não demonstra, por si só, qualidade da revisão: é necessário integrar o avaliador especializado e seus testes.

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

## Configuração do integrador (pendente)
- Criar `AGENT_MERGE_TOKEN` com permissões mínimas para solicitar merge e permitir apenas identidades confiáveis aplicarem `agent-auto-merge`.
- Habilitar GitHub auto-merge e branch protection/rulesets exigindo CI, aprovação independente e bloqueio de bypass.
- Configurar agente revisor real com identidade separada; revisar diff e evidências antes de emitir APPROVED.
- O workflow atual não substitui análise semântica do agente e não opera sem essas configurações.
- **Atenção:** mudanças nos próprios workflows, políticas, infraestrutura e arquivos `AGENTS.md` são bloqueadas pelo gate R1; sua adoção inicial requer processo específico de bootstrap.
