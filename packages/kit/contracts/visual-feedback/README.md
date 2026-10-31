# Visual feedback contracts

| Versão | Uso | Compatibilidade |
| --- | --- | --- |
| v1 | Registro de tarefa/captura e integridade, inclusive execução bloqueada | Preservada sem alteração de schema |
| v2 | Evolução iterativa com UX, impacto, regressões, estados, árvore do código e medições opcionais | Adoção explícita; não converter v1 em aceite automaticamente |

O kit define contratos; o engineering-team implementa sua validação. Fonte canônica de execução e limites: [runbook de feedback visual](../../../engineering-team/docs/VISUAL-FEEDBACK-PILOT.md). O vínculo documental não é uma dependência de runtime do kit.

Na v2, `source_tree_sha` é o resultado de `git rev-parse HEAD^{tree}` do produto renderizado. O gate recebe `--expected-head` de fonte confiável, confere o checkout atual e bloqueia mudanças posteriores à captura, inclusive arquivos não rastreados e flags assume-unchanged/skip-worktree. SHA/hash não comprovam por si mesmos que uma captura foi produzida por determinado código ou que um avaliador a inspecionou.

`performance_budgets` vazio significa que não há pré-requisito de performance neste registro; não significa performance aprovada. Orçamentos presentes exigem resultados correspondentes, baseline igual à congelada e `after <= max_after`. `unit` precisa representar a mesma grandeza antes/depois; a ferramenta não converte unidades. Não definir metas especulativas.

Resultados bloqueados/reprovados podem ter integridade válida. Para verificar pré-requisitos de aceite use o modo `--require-acceptance` do runbook, sem substituir testes nativos, revisão independente e gates de merge/deploy.
