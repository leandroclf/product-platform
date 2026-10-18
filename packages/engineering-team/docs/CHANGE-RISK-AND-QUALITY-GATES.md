# Política de risco independente e matriz mínima de qualidade

O `ai-team` é atualmente um executor local supervisionado para alterações R0/R1; **não possui canal seguro implementado para autorizar R2/R3**. O risco declarado por issue ou pelo modelo nunca concede poder extra.

## Gates determinísticos

1. O plano `READY` com risco R2/R3 é bloqueado antes da implementação.
2. Após o commit do implementador e **antes dos testes**, o host compara os nomes de arquivos alterados com o `base_sha`; arquivos de autenticação, permissões, workflow GitHub, infraestrutura, migrações, dependências, lockfiles, credenciais e configurações sensíveis elevam a classificação para R2 e interrompem o fluxo.
3. O host reexecuta esse controle antes dos testes e antes de `deliver` (incluindo PR draft), para impedir entrega de um diff que deixou de cumprir a autorização. O OpenSpec gerado pelo próprio coordenador é excluído da análise de *risco por caminho*.
4. Arquivos desconhecidos tratados como R1 **não provam** que o conteúdo é seguro. Essa heurística é um piso conservador, não substitui análise semântica, políticas nativas ou revisão humana.

## Matriz de qualidade por mudança

| Superfície | Checks mínimos a configurar e verificar |
|---|---|
| API/backend | contratos de API, casos de erro, concorrência, idempotência |
| Banco/migração | integridade, compatibilidade expand/contract, rollback |
| Frontend | acessibilidade, comportamento, testes de navegação |
| Integração externa | erros, timeout, retries, idempotência |
| Infraestrutura/IAM/segurança | revisão especializada, autorização R2/R3, validação de políticas |
| Mudança geral | teste focado, regressão, verificação de diff, checks reais da stack |

O classificador `change_policy.required_quality_surfaces` fornece **alertas** das famílias especializadas detectadas. Ainda não comprova execução dessas suítes; elas devem ser configuradas como checks efetivos do alvo e comprovadas na aceitação. Ausência de check não é sucesso.

## Limites importantes

R2/R3 **não** são rebaixados por `--confirm-hash`, por alegação do agente ou por um `PASS` do CI. Execução real dos CLIs, autorização, revisão humana, validação da main pós-merge e proveniência de release continuam gates separados. Interromper por risco excessivo pode deixar commits no clone isolado; não implica alteração do projeto original, publicação ou merge.
