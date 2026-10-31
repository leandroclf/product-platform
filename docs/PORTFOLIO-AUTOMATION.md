# Governança agendada do portfólio

## Objetivo
Manter um inventário rastreável dos repositórios da empresa como primeiro passo para a governança contínua. A fonte canônica para engenharia permanece em `packages/engineering-team`; não introduzir novo runtime de agentes.

## Primeira fase (implementada neste PR)
- Workflow de segunda a sexta às 11:20 UTC (08:20 Brasília), além de execução manual.
- Inventário paginado dos repositórios do proprietário, incluindo arquivados. **A issue publicada contém somente repositórios explicitamente públicos** (`private: false` e, quando informado, `visibility: public`); nome, URL, descrição, data e contagem de repositórios privados ou de visibilidade desconhecida nunca entram no corpo nem nos totais.
- Atualização de uma única issue persistente, evitando criar issues repetidas. A issue canônica é a issue aberta com o marcador do inventário criada por `github-actions[bot]`, pelo proprietário ou por membro/colaborador; marcadores em issues de terceiros são ignorados. Mais de uma issue canônica, resposta inválida ou paginação incompleta interrompem a execução sem criar nem atualizar issues.
- Token opcional `PORTFOLIO_READ_TOKEN`: somente leitura, usado apenas para listar repositórios. A escrita da issue usa o `GITHUB_TOKEN` do workflow, restrito ao repositório canônico. Sem o token de portfólio, o inventário é gerado em modo `public-only (privados não verificados)`; com ele, `public-only (dados privados omitidos)`. Em ambos os casos privados não são publicados nem declarados ausentes. Um token configurado mas inválido causa falha, sem downgrade silencioso.
- Sem checkout de outros repositórios, execução de código externo, alterações de arquivos, merge ou exclusões.

## Próximas fases (não implementadas)
1. Catálogo de domínio/produto/capacidade com revisão humana e evidências por repositório.
2. Análise incremental de manifests, contratos, testes e dependências; propostas como issues.
3. Backlog com classificação R0–R3 e seleção de tarefas R1.
4. Invocação controlada do `ai-team` em runner isolado com credenciais próprias, limites de custo e tempo, testes e PRs; não executar CLIs de provedores no runner padrão sem hardening.
5. Gates de aprovação e avaliação do piloto autenticado antes de automatizar mudanças em múltiplos repositórios.

## Limitações
Com token, a consulta usa `user/repos?affiliation=owner`; sem token, `users/<owner>/repos?type=owner`. Ambas filtram pelo proprietário. O inventário publicado cobre apenas repositórios públicos: a ausência de um repositório na issue não prova sua inexistência, e o token opcional não amplia o que é publicado.

Não expor credenciais em logs ou conceder acesso de escrita a outros repositórios na fase de descoberta.
