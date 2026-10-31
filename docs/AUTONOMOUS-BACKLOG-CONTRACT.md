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
- Risco R0/R1 para a fila automática; R2/R3 exigem política elevada e não entram no merge R1. O CLI local aceita R2 somente com `ai-team run --authorize-r2`, sem autorizar R3 ou entrega de R2.
- Orçamento e limites de tentativas definidos antes de executar.
- Existe rollback para mudanças com impacto operacional.

## Estado operacional atual — implementação e revisão são etapas distintas

A fila e o handoff permanecem PREVIEW_ONLY. A implementação depende de runner,
CLIs autenticadas, configuração do alvo, orçamento e acionamento autorizado.
Criar issue ou aplicar agent-candidate não inicia implementação.

O piloto de revisão independente e automerge R1 já foi observado no PR #114:
App revisor aprovou o HEAD e App integrador realizou o merge sob rulesets.
Ver [evidência](validation/2026-10-23-automerge-pilot.md) e
[operação](AUTOMERGE-OPERATIONS.md). Esse resultado substitui a descrição antiga
de automerge integralmente futuro/desativado, sem certificar toda a plataforma.

## Invariantes

1. OpenAI planeja, Claude implementa, OpenAI valida e Claude revisa em sessão
   isolada no fluxo ai-team; não declarar etapas reais a partir de testes mock.
2. O piloto automático exige opt-in, escopo R1 real, checks do pacote e revisão
   independente do HEAD. Pagamentos, segurança e workflows são R2 mesmo que uma
   heurística de caminhos não os reconheça.
3. R2/R3 não entram no merge R1. O CLI local aceita execução isolada até R2
   somente com `--authorize-r2`; entrega de R2 e qualquer R3 continuam bloqueadas.
   Mudanças protegidas exigem allowlist/revisão elevada, sem bypass. Produção
   mantém os gates próprios.
4. O ruleset observado exige aprovação e invalidação após push. Configuração,
   identidade e validade das credenciais precisam de evidência atual.
5. PORTFOLIO_READ_TOKEN é leitura opcional do inventário; não credencial de merge.
   Integrador usa App e environment próprios, conforme o runbook atual.
6. Em contingência manual, o gate não protegido é estrutural; sua aprovação não
   atesta uma revisão técnica. Não inventar resultados de providers ou CI.

## Adoção progressiva
1. `product-platform`: executar primeiro o piloto com revisão e merge humanos; em etapa posterior, demonstrar bloqueio, aprovação independente real, CI e merge nativo no HEAD.
2. Produto piloto com baixo risco e checks reproduzíveis; usar harness por release imutável.
3. Expandir em lotes, mediante relatório de falhas e evidências, sem assumir que a configuração central se replica automaticamente.
