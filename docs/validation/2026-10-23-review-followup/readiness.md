# Evolução após revisão — 23/10/2026

## Base, execução e limites

Base inspecionada: `6c1032097f2b3796a3d1a8e9def8dde91b9a9946`.
O proprietário autorizou aplicar as recomendações da revisão. O trabalho desta
sessão usa edição local, testes e PRs; não deve ser descrito como execução das
quatro etapas autenticadas do ai-team. Docker, CLIs autenticadas e setfacl não
estão disponíveis aqui. Os handoffs usam o fingerprint real do registry e as
regras pinadas, mas sua validade estrutural não comprova inferência ou operação.

## Situação e encaminhamento

| Recomendação | Resultado concreto | Dependência restante |
|---|---|---|
| Release reproduzível | PR #92 já encerrado; main contém toolchain, npm ci e build sem isolamento | Próxima release deve ter versão nova, CI/revisão e artefatos próprios |
| Revisão independente | PR #114 foi aprovado pelo App e mergeado pelo integrador em 49b68e11ddb8d22f0b9aedc4a9b775bded4ed19d | Isso prova o piloto R1; não aprova os incrementos R2 desta sessão |
| Pagamentos | PR #117 corrige timestamp/rotação, autenticação da normalização, idempotência e timeout | Revisão R2, nova release e ciclo durável da #102 |
| Inventário | PR #118 separa leitura/escrita e permite public-only explícito sem token opcional | Revisão R2 e run real; cobertura privada exige credencial própria |
| Portal | site-lf-solucoes #21 corrige orçamento contaminado por dist e setup do Lighthouse | Quality Smoke/Lighthouse verdes no PR; build externo Cloudflare segue falho |
| Marketing | #21 corrige promessas de Wikidata e regenera catálogo | Aceite editorial e publicação conforme o pipeline do site |
| RapidAPI | Diagnóstico e critérios em lf-wikidata-entity-graph #7 | HTTP 403, acesso à Platform API e owner ID precisam ser conferidos no provedor |
| Vercel | Inventário autenticado nos arquivos deste diretório | Não há benefício comprovado para migração; decisão conservadora é adiar |
| Piloto do produto/G6 | Artefato público do portal construído e validado offline | Staging segregado, health e rollback remotos ainda não demonstrados |

Não fechar épicos ou declarar produção com base nos PRs. O gate dos PRs #117 e
#118 retornou falta de aprovação independente no HEAD. Não adicionar opt-in R1
a pagamentos ou workflows para contornar a revisão elevada.

## Inventário e proposta Stripe — #101

O dono de payments é o harness, com interfaces e adapters TS em
`packages/harness/src/commerce`. A release 0.2.1 e a implementação atual não
oferecem paridade financeira Python: o wheel contém ProductEvent. Consumidores
confirmados no padrão vendor/harness-artifact.json são vehicle-tracking (TS
0.2.0), bussola-financeira e ai-docs (Python 0.2.1). Um wheel de eventos não deve
ser apresentado como integração de billing.

REUSE: registry/contratos/engineering_delivery. EXTEND: payments no harness;
persistência no PostgreSQL próprio do produto, sem serviço ou banco central.
Não criar gateway nem copiar o adapter para os consumidores. Preservar MP.

Catálogo: produto e plano de domínio estáveis, mapeados a Stripe Product/Price
por ambiente. Mensal/anual são variantes do mesmo plano. Preço/moeda/quantidade
são resolvidos no servidor; IDs/valores do browser não autorizam cobrança.
Customer mapping deve ser único por entidade vendedora/produto/tenant/cliente e
ambiente. Não compartilhar autorização ao Portal entre produtos por email.

Cada compra precisa de intenção persistida e chave de idempotência reutilizada
em retries. Inbox exige identidade provider/account/environment/event, claim
atômico e recuperação após crash. Ledger/entitlement/inbox precisam de transação
ou outbox idempotente para efeitos externos. Não prometer exactly-once.

Próximas entregas: #102 inbox/ledger/reconciliação → #103 Checkout/Billing/Portal
→ #104 faturas e Tax condicional → #105 artefato novo e piloto. O incremento de
#117 fecha somente a fronteira atual de autenticação/retry; não substitui o
ciclo de compra. Existe apenas conta live acessível na conexão atual; sandbox,
credencial restrita de runtime, piloto e regras comerciais não foram fornecidos.
Impostos e inscrições não serão inventados. Sem Connect para vendas próprias.

Aceite offline cobre concorrência, replay, eventos fora de ordem, crash/retry,
timeouts ambíguos, tenant isolation e reembolsos. A prova sandbox exige estado
autenticado separado e receipts sanitizados. Aprovação fiscal/produção é outra
etapa e não se deduz de um teste ou de automatic_tax=true.

## Inventário e decisão Vercel — #107

Os dois projetos acessíveis são Next.js e apontam, nos metadados de deployments,
para leandroclf/site-yukz-v2 e o mesmo SHA a2409b2547724f848282f6f6132cec78c6962568.
O primeiro tem um deployment histórico READY e um ERROR; o segundo tem READY.
A consulta GitHub ao repo retornou 404, que pode indicar escopo de acesso: não
presumir exclusão. Nenhum vínculo foi demonstrado com vehicle-tracking atual.
Root directory, plano contratado e uso/custos não vieram na resposta disponível.

| Workload atual | Decisão nesta etapa | Condição para reconsiderar |
|---|---|---|
| Portal estático | Preservar destino e corrigir pipeline existente | Custo total e benefício operacional comprovados |
| vehicle-tracking | Preservar Cloudflare/OpenNext declarado | Fonte atual compatível, acesso e piloto segregado |
| APIs Python | Descoberta por produto antes de adotar | Dependências, região/banco, payload e duração medidos |
| OCR ai-docs | Não selecionar como primeiro piloto | Perfil real de CPU/memória e trabalho durável |
| FiveM | Manter self-hosted | Nenhuma necessidade de migrar o FXServer |
| English Coach | Preservar local-first | Hosting estático não implica backend obrigatório |

Conclusão de descoberta: adiar adoção e #108–#111 até demonstrar um candidato
com benefício. Isso evita criar projetos pagos ou mover domínios para usar o
plugin. Não arquivar/excluir os projetos antigos sem inventariar consumidores.

## Custos e elegibilidade — fontes oficiais consultadas em 23/10/2026

Hobby destina-se a uso pessoal não comercial; não assumir que cobre produtos
vendidos pela LF. O plano real da conta não foi identificado. Functions cobra
por CPU ativa, memória provisionada e invocações; região altera os preços.
Somar plano/assentos, builds, CDN/transferência, storage e observabilidade
efetivamente usados, descontando créditos aplicáveis. Não adicionar serviços
opcionais. Não há volumes medidos para fornecer uma estimativa monetária honesta.

Modelo a preencher antes de adotar: custo mensal atual versus plano + execução
+ memória + invocações + transferência + builds + add-ons + esforço operacional.
Validar orçamento/alertas e comportamento real de limitação; alerta não equivale
a teto rígido. Registrar latência à região do banco e custo de saída/lock-in.

Fontes:
- https://vercel.com/docs/plans/hobby
- https://vercel.com/docs/functions/usage-and-pricing
- https://vercel.com/docs/pricing
- https://vercel.com/docs/pricing/regional-pricing/gru1

## Continuação exata dos bloqueios

1. Revisão de segurança independente dos HEADs de #117/#118; R2 não passa pelo
   worker R1. CI deve permanecer obrigatório. Não fabricar review/status.
2. Diagnosticar o build externo do site no Cloudflare: o check público informa
   falha, mas não traz logs detalhados. Nenhum conector Cloudflare foi encontrado
   nesta sessão. Não mover o site de provedor como correção especulativa.
3. Conferir owner ID e autorização da GraphQL Platform API do RapidAPI sem
   comprar assinatura ou expor chave. A action é preview/Node16 e usa @main;
   revisar e fixar uma implementação verificada antes de reexecutar publicação.
4. Disponibilizar runner Docker/CLIs/ACL e ambiente segregado para os pilotos.
   A tentativa de instalar ACL aqui falhou por restrições de capacidades do host;
   não substituir setfacl por stub, chmod amplo ou skip para obter verde.
5. Somente depois dos gates, publicar release nova e atualizar um consumidor com
   checksum; não atualizar todo portfólio nem habilitar pagamentos reais.

Tests desta execução: harness build + 9 TS + 3 Python; 146 testes raiz;
fronteiras e dois PlatformHandoffs válidos. Portal: 9 testes Python, build,
catálogo 9/9, estrutura, SEO/A11y smoke, segurança e budgets. Lighthouse local
não tem Chrome; execução remota no PR #21 passou. Suíte engineering-team:
175 testes, três erros por setfacl ausente; não se declara toda a suíte verde.
