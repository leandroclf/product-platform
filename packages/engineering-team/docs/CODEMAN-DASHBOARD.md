# Codeman: painel opcional de sessões (Linux)

## Escopo

[Codeman](https://github.com/Ark0N/Codeman) (antigo Claudeman) é um painel externo para sessões persistentes de CLIs de programação. **Não** substitui o `ai-team`, seu estado de tarefas, isolamento, papéis ou os gates G0–G6. Seu uso é **opt-in** e requer instalação e autenticação no host do operador.

O Codeman oferece dashboard, sessões tmux e acesso à interface via navegador. O `ai-team` continua sendo invocado pelos comandos documentados em [LOCAL-LINUX-WORKFLOW.md](LOCAL-LINUX-WORKFLOW.md); iniciar uma sessão de Claude/Codex pelo painel **não** equivale a executar a pipeline de validação do `ai-team`.

## Ativação local

1. Faça a revisão de segurança e licenciamento da versão de Codeman que pretende instalar. Não execute instaladores remotos cegamente, especialmente sob privilégios administrativos.
2. Instale Codeman conforme a [documentação oficial](https://github.com/Ark0N/Codeman#quick-start---installation), verificando os pré-requisitos do host (Node.js, tmux, compilador e pelo menos uma CLI de agente). Mantenha a instalação fora do checkout da Product Platform.
3. Com Codeman instalado e no `PATH`, execute:

```bash
bash packages/engineering-team/scripts/codeman-dashboard.sh --check
bash packages/engineering-team/scripts/codeman-dashboard.sh
```

4. Acesse `http://127.0.0.1:3000` **somente no próprio host**, salvo configuração de porta diferente. Para acesso remoto, prefira túnel SSH ou rede privada autenticada e siga as recomendações oficiais de autenticação.

O script não baixa software, não instala pacotes, não altera o serviço do sistema, não grava credenciais e não cria uma sessão de agente automaticamente. Por padrão, solicita que o Codeman use seu comportamento oficial de bind loopback; confirme o bind efetivo no host antes de liberar acesso à rede.

## Fronteiras e segurança

- **Não** monte o socket Docker do host no Codeman sem revisão explícita de isolamento e privilégios. O modo Docker sibling-container descrito no upstream amplia muito o acesso ao host.
- Use um workspace não privilegiado e evite compartilhar tokens, arquivos `~/.ssh`, `~/.aws` ou credenciais entre sessões ou projetos.
- Não configure comandos de execução autônoma, auto-respawn ou agendamentos com permissões de merge, deploy, alterações de infraestrutura ou produção sem autorização específica e gates nativos.
- Sessões Codeman iniciadas diretamente **não** herdam as restrições de ferramentas, isolamento por etapa, checks offline e controles R2/R3 do `ai-team`. Não as classifique como execução governada.
- Codeman está fora do grafo de dependências e do runtime do harness; pinagem de versão, atualização e rollback do Codeman são responsabilidade operacional separada.
- Se a CLI `codeman` não existir, o diagnóstico falha de forma explícita e a Product Platform permanece intacta.

## Aceite

- `--check` retorna diagnóstico sem mutações quando a CLI está instalada e falha quando ausente.
- `--help` funciona sem ferramentas adicionais.
- A execução normal delega exclusivamente a `codeman web`; não habilita abertura de rede nem auto-start.
- O `ai-team` original e os checks do repositório continuam funcionando sem Codeman.

## Evolução opcional (não implementada)

Um adapter supervisionado pode correlacionar `task_id`, `repo`, `base_sha` e `head_sha` com sessões Codeman **após** auditar a API/MCP do upstream, políticas de credenciais e lifecycle. Não confundir a presença do dashboard com integração bidirecional de estado.
