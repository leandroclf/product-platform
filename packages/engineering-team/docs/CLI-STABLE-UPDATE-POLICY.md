# Atualização dos CLIs — última versão estável, com promoção testada

**Regra:** antes de uma nova tarefa, o `ai-team run` consulta o registro oficial npm por HTTPS e verifica se a imagem de provedores do projeto contém as últimas versões **estáveis** de `@openai/codex` e `@anthropic-ai/claude-code`. Se houver versão diferente, falta de rede/registro ou incompatibilidade, o início da tarefa é bloqueado **sem fallback silencioso**. Versões são fixadas pelo digest da imagem durante a tarefa, sem substituições em execução.

## 1. Consultar versões sem modificar nada

No Linux, após instalar o AI Team:

```bash
cd ~/projetos/product-platform/packages/engineering-team
.venv/bin/python scripts/update_provider_clis.py
```

O resultado informa `installed`, `available`, necessidade de atualização e `approval_fingerprint`. Usa o endpoint estável `https://registry.npmjs.org/@openai%2fcodex/latest` e o equivalente de Claude Code; rejeita pré-releases e respostas inválidas. A consulta **não** atualiza o CLI nem consome inferência dos provedores.

## 2. Atualizar somente após confirmação explícita

```bash
.venv/bin/python scripts/update_provider_clis.py \
  --promote --confirm-hash HASH_EXATO_DO_CHECK
```

A atualização constrói uma imagem candidata com **versões exatas**, verifica em containers sem login os binários, as flags exigidas e os limites dos quatro estágios, incluindo canários adversariais de Docker. Reconsulta o registro antes de promover. A imagem é publicada na tag local `ai-eng-provider-cli:local` apenas após todas as verificações. Se houver tarefa `RUNNING`, `INTERRUPTED` ou `DELIVERY_PENDING`, a promoção é bloqueada antes e depois do build. Todas as tarefas antigas usam seus IDs de imagem já congelados.

A instalação inicial via `scripts/install-local.sh` permanece baseada em versões revisadas/pinadas para bootstrap reproduzível. Em seguida, realize explicitamente a atualização controlada antes da primeira tarefa. Não usar `npm install ...@latest` em volumes ou containers de um estágio ativo.

## Garantia de imagem por tarefa

No início de `ai-team run`, o coordenador converte a tag configurada da imagem de provedores em seu **ID imutável antes de verificar as versões oficiais**. Tanto a inspeção das versões quanto o `state.json` da nova tarefa utilizam esse mesmo ID. Assim, uma promoção concorrente da tag local não pode causar o uso de uma imagem diferente daquela cuja versão foi conferida. A imagem de testes também é congelada pelo ID antes de criar a tarefa.

## Limites de garantia

A consulta identifica a última publicação estável disponível no registro npm; **não garante que uma atualização seja compatível**. Os testes de CLI e Docker podem rejeitar releases que alterem flags e sandbox. Esse processo não autentica contas, valida todos os comportamentos dos modelos nem atesta a cadeia de suprimentos do registro. Se a nova versão falhar, a imagem ativa permanece preservada e a tarefa não inicia até resolução deliberada. Nenhuma alteração em GitHub branch rules, merge, deploy ou credenciais é executada por esse script.

Também não substitui `ai-team doctor`, `ai-team models`, os testes offline reais da aplicação nem a revisão humana.

## Atualização fail-closed diante de estado desconhecido

Antes da promoção, o atualizador inspeciona **todas** as pastas de tarefa locais. Diretórios ou arquivos de estado ausentes, ilegíveis, ligados por symlink ou malformados bloqueiam a operação; estados desconhecidos são tratados como execução potencialmente ativa. Somente `REVIEWED`, `DELIVERED`, `FAILED` e `STOPPED` são considerados terminais para a checagem. Indisponibilidade do registro npm gera erro legível e impede iniciar ou atualizar, nunca inferindo a versão atual por cache ou valor fixo.

Esses controles não substituem sincronização transacional entre múltiplos processos do host. A seleção por ID imutável de imagem (PR #48) protege o runtime de uma tarefa contra alterações concorrentes da tag.
