# Governança agendada do portfólio

## Objetivo
Manter um inventário rastreável dos repositórios da empresa como primeiro passo para a governança contínua. A fonte canônica para engenharia permanece em `packages/engineering-team`; não introduzir novo runtime de agentes.

## Primeira fase (implementada neste PR)
- Workflow de segunda a sexta às 11:20 UTC (08:20 Brasília), além de execução manual.
- Inventário paginado de repositórios visíveis do proprietário, incluindo arquivados.
- Atualização de uma única issue persistente, evitando criar issues repetidas.
- Token `PORTFOLIO_READ_TOKEN`: acesso de leitura a metadados dos repositórios e escrita em issues de `product-platform`. Preferir token fine-grained ou GitHub App com escopo mínimo.
- Sem checkout de outros repositórios, execução de código externo, alterações de arquivos, merge ou exclusões.

## Próximas fases (não implementadas)
1. Catálogo de domínio/produto/capacidade com revisão humana e evidências por repositório.
2. Análise incremental de manifests, contratos, testes e dependências; propostas como issues.
3. Backlog com classificação R0–R3 e seleção de tarefas R1.
4. Invocação controlada do `ai-team` em runner isolado com credenciais próprias, limites de custo e tempo, testes e PRs; não executar CLIs de provedores no runner padrão sem hardening.
5. Gates de aprovação e avaliação do piloto autenticado antes de automatizar mudanças em múltiplos repositórios.

## Limitações
A consulta usa `user/repos?affiliation=owner` e filtra pelo proprietário. A cobertura de repositórios privados depende das permissões concedidas ao token; repositórios não autorizados não aparecerão no inventário.

Não expor credenciais em logs ou conceder acesso de escrita a outros repositórios na fase de descoberta.
