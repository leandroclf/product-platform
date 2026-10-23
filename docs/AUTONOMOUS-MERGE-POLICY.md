# Política de integração autônoma

## Objetivo
Permitir merges sem revisão humana rotineira, usando um revisor especializado independente do executor, sem contornar proteções de branch.

## Separação de funções
- Executor: implementa mudanças em branch e abre PR.
- Revisor: processo e credencial distintos; analisa diff, contratos, segurança, arquitetura, testes e riscos; registra revisão formal no GitHub.
- Gate: verifica aprovação por identidade distinta no SHA atual e bloqueia caminhos críticos.
- Integrador: após revisão independente, solicita integração nativa pelo GitHub; checks e ruleset continuam obrigatórios.
- Auditor: registra evidências, resultados e rollback.

## Estado e limites
Executor e integrador estão instalados em `leandroclf/product-platform`; o revisor também atende revisão manual do laboratório `ai-engineering-control-plane`. O auto-merge nativo está habilitado. O ruleset `main-autonomy-minimum` está ativo sem bypass, exige os checks `boundaries`, `offline-safety-tests` e `independent-review-gate`, uma aprovação, descarte após push, aprovação do último push por outra identidade e resolução de discussões.

Em 2026-10-23, `AGENT_REVIEW_MODE=independent`, `AGENT_TRUSTED_REVIEWERS` e `AGENT_SECURITY_REVIEWERS` foram configurados para o App revisor real. O PR #100 e os PRs #92, #94, #95, #96 e #98 receberam análise técnica independente no SHA atual e foram integrados com checks. Isso demonstra recuperação dos merges R2, mas não substitui o piloto autônomo R1 nem comprova rollout em todos os produtos.

O worker e o procedimento de ativação estão em [AUTOMERGE-OPERATIONS.md](AUTOMERGE-OPERATIONS.md). Ele usa revisão estática isolada e a política canônica do ai-team; a identidade do App isoladamente não comprova análise. As chaves devem ficar nos environments restritos à `main`, e a chave local em arquivo privado fora do Git.

## Política de risco
- R0: documentação e análise; podem ser automatizadas.
- R1: código reversível, com testes e revisão independente; elegível ao fluxo opt-in depois do piloto operacional.
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
- Validar o token temporário do integrador com `contents:write` e `pull_requests:write`, limitado ao repositório e criado somente após o gate.
- Instalar e validar o worker local, demonstrando bloqueio antes da revisão, análise real, checks, integração nativa e trilha de auditoria.
- Remover as cópias gerais das chaves do repositório após verificar os environments restritos à `main`.
- **Atenção:** workflows, políticas, infraestrutura e `AGENTS.md` seguem R2: a rota de segurança exige aprovação distinta no HEAD atual e merge manual; o integrador R1 continua rejeitando esses caminhos.
