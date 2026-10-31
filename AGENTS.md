# Instruções para agentes

## Fluxo de pull requests

- Neste repositório, enquanto não houver branch de desenvolvimento no remoto, crie a branch de trabalho a partir de `main` e abra o PR para `main`. Esta exceção ao Gitflow global foi solicitada para o fluxo deste projeto; não presume promoção ou deploy em outros ambientes.
- Para desbloquear PRs, investigue os checks, conflitos, revisões e regras de proteção efetivamente aplicáveis; preserve a identidade e o SHA exato de cada revisão.
- Delegue a um subagente revisor independente a análise de PRs com código ou alterações em segurança, pagamentos, dependências, permissões ou pipelines. Use `backend_code_reviewer` para backend e `code_reviewer` para mudanças gerais, quando disponíveis; delimite base, HEAD e escopo e peça achados com evidências e limitações.
- O subagente atua em somente leitura e não aprova, publica reviews nem faz merge. Avalie e corrija os achados antes de solicitar a revisão necessária no GitHub; um parecer local não substitui a aprovação da identidade exigida pelo gate.
- Verifique o parecer independente, os checks e o HEAD atual; registre a aprovação pela identidade revisora permitida no GitHub somente quando houver análise real favorável. Um parecer obsoleto ou achado bloqueante exige correção e nova revisão.
- Mantenha os controles de CI, revisão e proteção de branches. Siga a política de risco e o procedimento em `docs/AUTOMERGE-OPERATIONS.md`; PRs sensíveis não entram automaticamente no fluxo R1. Merge depende de solicitação explícita e dos controles aplicáveis; depois confira o estado do PR e os checks da `main`.
- Instruções específicas dos pacotes complementam estas regras. Os comandos e limites do monorepositório estão no `README.md`.
