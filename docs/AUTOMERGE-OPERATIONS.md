# Operação local de revisão independente e automerge

## Fronteiras

O worker `scripts/independent_pr_reviewer.py` consulta somente
`leandroclf/product-platform`. Por execução, avalia no máximo um PR R1 aberto,
sem draft, destinado à `main`, com label `agent-auto-merge` e os checks
`boundaries` e `offline-safety-tests` aprovados no HEAD atual pelo GitHub Actions.
PRs protegidos, renames desses caminhos, manifests de dependências classificados
como R2 e mais de 50 arquivos ficam para revisão manual. O diff tem limite de
100 KB, com margem sob o limite de argumentos do Linux. Esses limites são deliberados para o piloto, não uma classificação
automática de segurança de todo código.

O Claude roda numa nova sessão, com o comando e schema canônicos do
`packages/engineering-team`, no volume `ai-team-atlas-review-home`, imagem local
fixada pelo ID imutável da imagem local verificada e checkout somente leitura. O modo seguro desativa
customizações do checkout. Só Read/Grep/Glob estão disponíveis: nenhum código
do PR, teste, comando shell, MCP ou subagente executa no container autenticado.
A análise é estática; os testes são responsabilidade do CI, e essa limitação
aparece no review. O container reaproveita `docker_base` do ai-team: usuário
1001, root filesystem somente leitura, capabilities removidas, sem novos
privilégios, pull desabilitado e limites de memória/CPU/processos. ACLs dão
acesso somente ao clone descartável, com `.git` fora da concessão. O worker
reaproveita `review_pass` do ai-team: achados médios
ou superiores não resolvidos, gates negativos, schema ou SHA inválidos bloqueiam.

A chave do App e o transporte GitHub ficam no host. O App revisor tem instalação
com escrita de conteúdo para que a aprovação conte na regra nativa do GitHub,
mas cada token de trabalho solicita apenas leitura de conteúdo/checks e escrita
de reviews. O App integrador é distinto e não recebe bypass de rulesets.
Seus tokens precisam de escrita de conteúdo para a integração nativa e de PRs,
limitadas ao repositório. Chaves no GitHub pertencem aos environments
`agent-review` e `agent-integration`, restritos à branch `main`; não deixá-las
como secrets gerais do repositório após concluir a migração.

## Configuração no Linux do proprietário

1. Confirmar Python com `yaml` e `jsonschema` já usados pelo ai-team, `setfacl`,
   login do `gh` como `leandroclf`, autenticação do Claude no volume
   revisor e existência da imagem local de providers. Não copiar credenciais de
   um projeto ou conta diferente automaticamente.
2. Instalar a chave em `~/.config/product-platform-reviewer/reviewer.pem` com
   proprietário correto e modo `0600`, dentro de pasta `0700`.
3. Criar `~/.config/product-platform-reviewer/reviewer.env` sem inserir o valor
   da chave no arquivo:

```text
REVIEWER_APP_ID=5389770
REVIEWER_RUNTIME_SHA=SHA_DO_COMMIT_INTEGRADO_E_REVISADO
REVIEWER_PROVIDER_IMAGE=sha256:ID_IMUTAVEL_DA_IMAGEM_LOCAL_VERIFICADA
REVIEWER_APP_PRIVATE_KEY_FILE=/home/leandro/.config/product-platform-reviewer/reviewer.pem
REVIEWER_STATE_DIR=/home/leandro/.local/state/product-platform-reviewer
```

4. Criar a pasta de estado com modo `0700`. Ela contém snapshots e evidências de
   código; não é montada no container exceto pelo checkout de cada avaliação.
5. Criar clone operacional dedicado em `~/.local/share/product-platform-reviewer/runtime`,
   em HEAD destacado no commit integrado e revisado. Conferir que está limpo,
   registrar esse SHA no environment e nunca usar a pasta de desenvolvimento
   como runtime. O serviço valida HEAD e árvore limpa antes de ler a chave.
   Instalar as duas units de `ops/systemd/` no systemd do usuário, validar com
   `systemd-analyze --user verify`, recarregar e executar o serviço uma vez.
6. Habilitar o timer somente após o piloto: bloqueio antes de review, análise
   real, aprovação no SHA atual, gates, solicitação do integrador e merge nativo.

## Reexecução e auditoria

A aprovação é publicada somente depois de reconsultar HEAD, estado e opt-in.
Reviews do App no mesmo SHA impedem nova avaliação e submissão duplicada.
Após aprovação real, o worker pode reexecutar uma única vez cada run falho do
workflow exato `agent-review-gate.yml` no mesmo SHA. Isso resolve a coexistência
de checks de `pull_request` e `pull_request_review`: a reexecução executa a
política novamente, sem fabricar status e sem repetir testes verdes.

Evidências ficam em `REVIEWER_STATE_DIR/pr-N-SHA/`: identidade da revisão,
resultado estruturado, saída sanitizada do provider e erros. A revisão GitHub
publica apenas decisão/gates controlados pelo schema, contagens por severidade,
SHA e hash SHA256 da evidência. Texto livre do modelo e achados detalhados
permanecem privados, evitando usá-los como canal de exportação de credenciais.
O journal do serviço registra PR, SHA e decisão, sem prompts nem corpo de erros.
Falhas de autenticação, CI pendente, saída inválida e mudanças no HEAD não
habilitam merge. Uma falha fica marcada por PR+SHA para revisão manual, sem
repetir consumo do provider; a fila segue no próximo ciclo. O operador pode
remover a marca `manual-review-N-SHA.json` após corrigir a causa e autorizar nova
tentativa. O processo usa lock local e não altera código nem integra PRs.

O fluxo depende de Linux, Docker Desktop, imagem e logins locais disponíveis.
Não é um executor hospedado no GitHub nem prova de isolamento completo de
credenciais do provider. A integração final continua sob os controles nativos.

## Interrupção e rollback

Parar/desabilitar `product-platform-reviewer.timer` interrompe novas revisões;
parar o serviço interrompe a execução atual. Retornar `AGENT_REVIEW_MODE` a
`manual` interrompe novas solicitações do integrador. Auto-merges já habilitados
precisam ser cancelados por PR; desabilitar o timer não cancela a fila nativa.
