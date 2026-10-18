# Contrato de backlog para evolução autônoma

## Decisão
As cinco rotinas ChatGPT continuam **analíticas**; não são o executor. Suas descobertas devem resultar em issues verificáveis no `product-platform`. O executor oficial continua `packages/engineering-team` (`ai-team`), sem novo framework, gateway ou GitHub App fictício.

## Contrato por proposta (issue)
- **Origem**: governança / arquitetura / segurança / negócios / revisão executiva; link e data da evidência.
- **Repositório de destino**: `owner/repo` explícito.
- **Problema verificável**: fato observado, hipótese e referência para reproduzir.
- **Resultado esperado**: comportamento mensurável e critérios de aceite.
- **Risco**: R0 (análise), R1 (reversível), R2 (segurança, infra, pagamentos, migrations), R3 (irreversível/prod).
- **Custo**: limite financeiro e de execução estimado; não inventar valores.
- **Capacidades**: checar `packages/kit` e `packages/harness` antes de criar código; indicar dono do domínio.
- **Checks**: testes específicos do repositório, validação de contratos, regressão, segurança e evidências.
- **Dependências**: issues/PRs bloqueadores, disponibilidade de credenciais e aceitação externa.
- **Status**: `candidate` → `triaged` → `ready` → `in_progress` → `in_review` → `merged` → `validated` (ou `blocked`).
- **Rastreabilidade**: links issue → handoff do plano → PR → checks → revisão → merge SHA → evidência de operação.

## Critérios para promover a 'ready'
- Problema tem evidência rastreável e está no escopo comercial/técnico do produto.
- Destino/reuso definidos; não duplica outro runtime ou produto.
- Teste de aceite reproduzível sem segredos embutidos.
- Risco R0/R1; R2/R3 exigem política elevada e não entram no merge R1.
- Orçamento e limites de tentativas definidos antes de executar.
- Existe rollback para mudanças com impacto operacional.

## Invariantes da implantação
1. O modelo planejador é OpenAI; implementador Claude; validador OpenAI; revisor Claude em sessão independente, respeitando as configurações já adotadas do `ai-team`.
2. Agentes não podem aprovar seus próprios PRs, criar aprovações fictícias ou contornar rulesets.
3. O gate R1 confirma revisão GitHub do HEAD exato; revisão técnica especializada real ainda exige integração com CLIs autenticadas.
4. O auto-merge apenas solicita o serviço nativo GitHub após os gates. Revisão/CI obrigatórios devem ser configurados em rulesets.
5. Sem segredo de App, execução autenticada e teste fim a fim, a plataforma permanece **parcialmente automatizada**.

## Pendências PC / administradores
Ver `docs/AUTONOMOUS-BOOTSTRAP.md` e `docs/AUTONOMY-PENDING-PC.md`. Criar GitHub Apps/identidades separadas, habilitar rulesets e auto-merge, configurar `PORTFOLIO_READ_TOKEN`, `AGENT_MERGE_TOKEN`, `AGENT_TRUSTED_REVIEWERS`, autenticador real do revisor, teste de ponta a ponta em piloto, expansão controlada.

## Adoção progressiva
1. `product-platform`: piloto R1 demonstrando bloqueio, aprovação real, CI e merge no HEAD.
2. Produto piloto com baixo risco e checks reproduzíveis; usar harness por release imutável.
3. Expandir em lotes, mediante relatório de falhas e evidências, sem assumir que a configuração central se replica automaticamente.
