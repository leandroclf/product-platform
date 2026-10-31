# Política de risco independente e matriz mínima de qualidade

O `ai-team` é um executor local supervisionado. R0/R1 seguem o fluxo padrão; um operador pode autorizar explicitamente um plano até R2 com `ai-team run --authorize-r2`. R3 continua bloqueado. O risco declarado por issue ou pelo modelo nunca concede poder extra.

## Gates determinísticos

1. O plano `READY` com risco R2 só continua se a execução foi iniciada com `--authorize-r2`; planos R3 são sempre bloqueados. A autorização é vinculada ao repositório, HEAD base e hash da solicitação no estado privado da tarefa.
2. Após o commit do implementador e **antes dos testes**, o host compara os nomes de arquivos alterados com o `base_sha`; arquivos de autenticação, permissões, workflow GitHub, infraestrutura, migrações, dependências, lockfiles, credenciais e configurações sensíveis elevam a classificação para R2 e interrompem o fluxo.
3. O host reexecuta esse controle antes dos testes e antes de `deliver` (incluindo PR draft), para impedir entrega de um diff que deixou de cumprir a autorização. Todos os caminhos alterados, inclusive OpenSpec gerado pelo coordenador, entram na classificação e nos patches entregues a validate/review; apenas o detector de ciclos ignora a pasta de registros da tarefa corrente.
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

O classificador `change_policy.required_quality_surfaces` agora também atua como **gate obrigatório**: para cada família detectada no diff real, é necessário existir um comando correspondente em `quality_checks`. Se faltar, o host bloqueia antes de testar ou entregar. Os comandos são executados junto dos checks gerais, no container de testes offline sem contas dos provedores. A presença do comando não garante sua adequação: o operador deve fornecer testes reais da stack, e o resultado integra `tests.json`.

Exemplo de configuração inicial ou atualização deliberada (substitua os comandos pelos testes do projeto):

```bash
ai-team init --upgrade --test-image python:3.12-slim \
  --check 'python -m unittest discover -v' \
  --quality-check 'api_contract=python -m unittest tests.test_api_contracts' \
  --quality-check 'integration=python -m unittest tests.test_integrations'
```

`--upgrade` exige configuração existente e preserva um backup; na primeira configuração, omita-o. As famílias suportadas são `api_contract`, `database_migration`, `frontend`, `integration`, `infrastructure` e `security_and_approval`. Mudanças R2 em caminhos sensíveis continuam exigindo os checks especializados correspondentes; a autorização não cria checks nem os marca como executados. A classificação de caminhos permanece independente do plano.

A classificação por nomes de arquivo é heurística: testes e revisão humana continuam necessários para detectar mudanças semânticas fora das pastas esperadas.

## Limites importantes

R2/R3 não são rebaixados por alegação do agente ou por um `PASS` do CI. `--authorize-r2` é uma decisão explícita do operador para o plano, não um passe para caminhos R2: esses caminhos ainda passam pelo classificador, exigem checks especializados e revisão independente. A entrega de planos R2/R3 permanece bloqueada; execução R2 fica isolada no clone da tarefa. Execução real dos CLIs, revisão humana, validação da main pós-merge e proveniência de release continuam gates separados. Interromper por risco excessivo não altera o checkout original, publica ou faz merge.
