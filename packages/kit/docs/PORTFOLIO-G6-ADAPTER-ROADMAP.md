# G6 — Generalização por produto e runtime

Política única: [DEPLOYMENT-G6.md](DEPLOYMENT-G6.md). Inventário executável: [portfolio-deployment-targets.json](../contracts/portfolio-deployment-targets.json), cruzado automaticamente com [portfolio-products.json](../contracts/portfolio-products.json). Esses contratos **não fornecem permissão de implantação**.

## Evidência real já disponível

- `vehicle-tracking`: job GitHub Actions [39159440993](https://github.com/leandroclf/vehicle-tracking/actions/runs/39159440993) concluiu o build Next.js + OpenNext, `wrangler deploy --env staging --dry-run` e hashing de todos os outputs.
- Manifesto offline no artifact do run; status `OFFLINE_STAGING_BUNDLE_VERIFIED`.
- Não foram validados tokens Cloudflare, proteção real de environment, migração, health remoto, rollback nem produção.

## Descoberta read-only dos runtimes — 2026-10-20

O snapshot [`portfolio-deployment-discovery.json`](../contracts/portfolio-deployment-discovery.json) fixa os SHAs de `main` e os blobs dos manifests/workflows consultados para os nove produtos e o portal. Ele registra declarações de configuração e o estado observado do GitHub; não executa builds nos repositórios nem transforma CI em prova de deploy.

Achados que mudam a sequência de trabalho:

- `vehicle-tracking` declara Cloudflare Workers/OpenNext e tem dry-run offline. O workflow de staging não tem execução registrada; a última execução do workflow `deploy.yml` em `main` terminou com o job `deploy` ignorado. O environment `production` existe no GitHub, mas a API reportou zero regras de proteção e zero revisores obrigatórios.
- `bussola-financeira` declara dois containers Docker (API Python 3.11 e frontend nginx); não foi encontrado manifest de provedor nos arquivos de build/deploy consultados. `ai-docs` declara container Python 3.12, também sem manifest de provedor nos arquivos consultados.
- `lf-worldbank-risk-pricing`, `lf-openalex-enrichment-mvp` e `lf-wikidata-entity-graph` declaram Render (`render.yaml`) e endpoint `/health`; todos também declaram publicação RapidAPI. Os runs consultados terminaram em falha, sem logs retidos que permitam atribuir causa. O step usa `RapidAPI/create_or_update_rapidapi_listing@main`, uma referência móvel que precisa ser fixada antes de confiar nessa automação.
- `agentic-travel-engine` separa API Python e frontend Next.js, sem provedor de deploy encontrado nos manifests consultados. FiveM declara empacotamento Docker para FXServer self-hosted, sem health check remoto. English Coach declara build estático em JavaScript, sem provedor de publicação encontrado.
- `site-lf-solucoes` tem workflows de qualidade/Lighthouse, mas GitHub Pages não está configurado na consulta atual (`has_pages=false`). Não há prova de publicação remota do portal.

Os contratos continuam com `remote_deploy_verified=false` para todos os alvos. Os próximos passos com maior valor são corrigir/pinar e diagnosticar as publicações RapidAPI; levantar provider, armazenamento, health e rollback dos dois produtos Python ainda sem manifest; e configurar proteção real antes de qualquer promoção de `vehicle-tracking`. Não habilitei workflow, environment, Pages, segredo ou deployment.

## Adapter planeado por runtime (sem criar deploy implícito)

| Adapter | Produtos | Próxima implementação |
|---|---|---|
| cloudflare-workers-opennext | vehicle-tracking | Ambiente staging protegido, secrets isolados, health, artifact imutável, rollback ensaiado |
| python-container-or-serverless | bussola-financeira, ai-docs | Descobrir entrypoint, processo de publicação, DB e ambientes; container build offline por SHA |
| rapidapi-or-python-service | worldbank, openalex, wikidata | Validar publicação RapidAPI existente, spec API, smoke e rollback de versões |
| python-api-plus-web-frontend | agentic-travel-engine | Adapters separados para API e Next.js, com mesmo plano de versão |
| fxserver-distribution | fivem-server-monitor-pro | Pacote de distribuição e instalação self-hosted, sem tentar deploy serverless |
| static-web-or-local-package | professional-english-coach | Build estático/instalável, offline-first, sem telemetria por padrão |

**Não usar URLs de produção, tokens, endpoints de banco ou comandos de infraestrutura presumidos**. Antes de habilitar adapter remoto, cada repositório deverá registrar seu provedor real, caminho de build, artefato, health URL, storage, secret scope, regras de aprovação e rollback.

## Interface de adapter (contrato alvo)

Entrada imutável: `product`, `source_sha`, `artifact_ref`, `artifact_sha256`, `environment`, `checks`, `rollback_artifact_ref`, `approval_evidence`. Saída: `receipt` com run ID, ambiente, ID remoto de release, hash observado, resultado do smoke, rollback executável e custos estimados. A validação do Kit é read-only. O adapter é responsável por verificar **via fonte confiável** permissão de ambiente, origem CI, infraestrutura, aprovação, digest remoto e estado real de deploy.

Gates por ordem:
1. Descoberta automática **somente leitura** da tecnologia e infraestrutura atual do produto.
2. Build reprodutível e testes no SHA commit; pacote + checksum vinculados ao run.
3. Dry-run em infraestrutura isolada, sem credenciais de produção.
4. Preview por PR quando suportado; staging isolado, health e integração.
5. Proteção do environment, approvals do GitHub realmente configurados, sem acesso cruzado de segredos.
6. Produção somente com aprovação específica e explícita; deploy progressivo, monitoramento e rollback.
7. Pós-deploy: conciliar `source_sha`, `artifact_sha256`, `remote_release_id`, latência, erros e custo.

Condições que bloqueiam:
- PRs/forks executando pipelines com secrets de produção;
- inconsistência de SHA e digest entre build, artifact e deploy;
- aprovação apenas declarada em JSON;
- ambiente staging que compartilha DB/tokens com produção;
- migrations destrutivas simultâneas a deploy de código;
- rollback anunciado sem teste real;
- adapter não inventariado;
- download de scripts de `main` não fixados em release/commit;
- sucesso de CI confundido com sucesso de deploy.

## Sequência de implementação recomendada

- **Fase 0 — Inventário de todos os produtos**: contrato completo com 9/9 produtos; CI bloqueia inconsistências, jamais afirma deployment remoto não provado. **Presente neste PR.**
- **Fase 1 — Adapter Cloudflare**: tornar reusável o ensaio G6 do `vehicle-tracking`; testes de isolamento de secrets; depois produção protegida.
- **Fase 2 — Adapters Python**: pilotos `bussola-financeira` e `ai-docs`, um repositório por vez, observando banco e API.
- **Fase 3 — RapidAPI**: normalizar os três produtos de dados com a publicação já existente.
- **Fase 4 — Frontends**: `agentic-travel-engine` (API + Next) e `professional-english-coach` (sem requisito de deploy servidor).
- **Fase 5 — FiveM**: release verificável para instalação self-hosted, sem exigir Cloudflare.
- **Fase 6 — Adoção observável**: dashboard com run/receipt real por produto, cobertura G6 por estágio, custo por ambiente e rollback supervisionado.

## CI de contrato

```bash
cd packages/kit
python3 scripts/validate-portfolio-brand-deploy.py
python3 -m unittest discover -s scripts -p test_portfolio_brand_deploy.py
```

Este CI é deliberadamente sem rede, sem secrets e sem cloud mutation. Os adaptadores reais exigirão PRs adicionais específicos e evidências de execução próprias.
