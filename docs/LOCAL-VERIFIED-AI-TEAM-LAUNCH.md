# Executar localmente uma proposta verificada com ai-team

Essa integração reutiliza `packages/engineering-team` e não cria novo runtime. O script `scripts/local_ai_team_launcher.py` importa o artefato `candidate-preview.json`, verifica esquema e SHA, valida que a pasta de destino é a raiz do Git correto e que o checkout está limpo. Por padrão **apenas mostra a proposta**.

## No Linux, depois da configuração administrativa
1. Instalar, autenticar e configurar `ai-team` no repositório alvo conforme `packages/engineering-team/docs/LOCAL-LINUX-WORKFLOW.md`; `ai-team doctor` precisa passar. GitHub Apps, rulesets, secrets e revisor real continuam pendentes.
2. Verificar a issue original, autoria, evidências, risco verdadeiro, permissões, orçamento e reuso de capacidades. O SHA não autentica a origem da issue.
3. Baixar `candidate-preview.json` da execução oficial GitHub Actions e verificar a procedência.
4. Executar a prévia:

```bash
python3 scripts/local_ai_team_launcher.py --preview candidate-preview.json --target /caminho/repo
```

5. Somente após conferir a prévia, iniciar explicitamente:

```bash
python3 scripts/local_ai_team_launcher.py --preview candidate-preview.json --target /caminho/repo --execute --confirm-hash SHA256_DA_PREVIA
```

O modo `--execute` chama apenas `ai-team doctor` e `ai-team run '<texto de tarefa>'` por lista de argumentos, **sem shell**. Ele **não** faz `deliver`, push, PR, merge ou deploy, não instala credenciais e não muda configuração de projeto. O `ai-team` aplica seus próprios gates e pode bloquear etapas.

## Limites de segurança
- O repositório Git de destino deve coincidir com `target_repository`, com URL GitHub SSH/HTTPS padrão, branch nomeada e checkout limpo.
- O hash exato é uma confirmação local explícita, não uma aprovação técnica da tarefa. A classificação R1 declarada pelo autor não prova risco R1 real.
- O script não verifica se a evidência é verdadeira, nem se há injecção no texto da issue. A revisão pelo operador/política independente permanece necessária antes da execução.
- Não executar automaticamente artefatos produzidos por issues não confiáveis. Nenhum workflow remoto chama este launcher.
- A execução com contas reais, QA e entrega via PR continuam pendentes de validação ponta a ponta.
