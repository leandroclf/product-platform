# Preflight do piloto autenticado no Linux

Este procedimento verifica **prontidão do host**, sem iniciar Codex, Claude, sessões autenticadas ou qualquer implementação. Nenhum resultado gerado fora do Linux do operador é prova de aceite operacional.

## Executar no host do operador

```bash
cd ~/projetos/product-platform/packages/engineering-team
.venv/bin/python scripts/pilot_readiness.py \
  --target ~/projetos/product-platform \
  --output ~/ai-team-preflight.json
```

O comando retorna `0` somente com todos os checks de host aprovados; `2` quando houver bloqueios. A saída não contém caminhos locais, tokens, nomes de contas ou prompts. Se usar `--output`, o arquivo novo recebe permissão `0600` e não é sobrescrito. Não publique dados brutos do `ai-team`, imagens de credenciais ou logs.

O preflight confere Linux, Python, Git e Docker; checkout na raiz do alvo, branch nomeada, alterações não commitadas, origin GitHub; configuração v2 congelável do alvo, imagens Docker já existentes, comandos gerais e campos de modelos por estágio; além de uma **prova prática de ACL POSIX** em um arquivo temporário, usando `setfacl` e `getfacl`. O teste ACL é limitado à pasta temporária: **não atesta** o bind mount do volume da tarefa, a identidade efetiva dos provedores ou as políticas do daemon Docker.

## Gates manuais seguintes

Depois de um preflight positivo, no Linux execute explicitamente `ai-team doctor`, `ai-team models` e `python3 scripts/local_stage_isolation_smoke.py` com a imagem já construída. São comandos diferentes: `doctor` consulta a presença das contas autenticadas, mas não prova validade futura do token ou a correção do modelo retornado.

Somente com esses controles aprovados, selecione uma issue **real e ainda aberta** R0/R1, obtenha sua prévia e hash com o launcher do backlog e confirme manualmente a execução. Em seguida siga [LIVE-LINUX-ACCEPTANCE.md](LIVE-LINUX-ACCEPTANCE.md) para verificar HEAD, checks, pareceres e PR draft. Não reutilize uma issue já concluída como se fosse uma tarefa nova.

O relatório **sempre** informa `provider_authenticated=false`, `actual_inference_verified=false` e `production_certified=false`. Nenhuma ausência de bloqueios deve ser interpretada como execução real ou autorização de merge/deploy. A aceitação P0 depende de execução local e inspeção humana.
