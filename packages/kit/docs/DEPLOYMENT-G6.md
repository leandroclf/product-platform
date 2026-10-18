# G6 — Contrato de promoção e deploy reutilizável

O **Kit** é o dono da política de entrega; este contrato é reutilizado pelos repositórios de produto. O **Harness** continua sendo a biblioteca runtime de capacidades de produto — não um deploy engine, gateway ou control plane. O `ai-team` encerra a implementação com PR draft e revisão. O pipeline de cada produto conecta seus próprios adapters Cloudflare/Vercel/Netlify/Workers/Lambda e os recursos de infraestrutura que ele realmente usa.

## Pipeline alvo

```text
PR draft / CI verde no commit revisado
  -> revisão e merge manual na main
  -> CI pós-merge no SHA correto
  -> build + testes + assinatura/checksum de artefato imutável
  -> preview (isolado por PR) -> smoke
  -> staging -> smoke + integração + health
  -> G6: conferência de artefato/commit/checks e aprovação de produção
  -> deploy progressivo em produção -> smoke/health
  -> observar erros, latência e custo -> concluir OU rollback
  -> migrations CONTRACT somente em entrega posterior
```

## Primeiro incremento implementado (política G6, sem mutação)

O script `scripts/validate-deployment-plan.py` recebe um **plano JSON** e aplica validação estrita, sem API externa, sem acesso ao Docker e sem credenciais. Verifica:

- SHA Git de 40 caracteres e checksum do artefato de 64 hex; referência de artefato não flutuante (é indispensável resolver/testar sua integridade no runner real);
- ambiente `preview`, `staging` ou `production`, com rollback distinto para staging/prod;
- gates explícitos `build`, `unit`, `security`, `integration`, `smoke`, `health`, vinculados ao hash canônico dos checks;
- autorização declarada de produção vinculada ao SHA, digest e ambiente exatos;
- evidência de rollback anterior vinculada ao plano, sem trocar artefato silenciosamente entre ambientes.

```bash
cd packages/kit
python3 scripts/validate-deployment-plan.py /caminho/para/deployment-plan.json
python3 scripts/validate-deployment-plan.test.py
```

Código de saída: `0` significa somente **READY_FOR_OPERATOR_REVIEW**; `1` indica violação da política; `2` indica documento ilegível/inválido. O campo `authorized_to_deploy` é **sempre false**: o plano e sua identidade de aprovação são declarados pelo chamador e **não autenticados por este script**.

## Verificação independente de artefato no runner de CI

Além da validação estrutural do plano, execute o verificador read-only no checkout exato usado para construir um artefato:

```bash
python3 packages/kit/scripts/verify-deployment-artifact.py \
  --plan deployment-plan.json \
  --checkout . \
  --artifact dist/release.tgz
```

O comando comprova localmente que o **HEAD do Git** corresponde ao `source_sha` declarado, que os arquivos rastreados não foram modificados e que o SHA-256 calculado sobre os **bytes reais** do artefato corresponde ao `artifact_sha256`. Ele rejeita plano/artefato via symlink, artefato vazio, arquivo não regular, checkout incorreto ou alterações rastreadas. O relatório não inclui conteúdo de arquivos e mantém `authorized_to_deploy=false`.

**Limites:** o script não verifica se o pacote corresponde semanticamente ao código-fonte, se os testes foram realmente executados pelo CI, se uma identidade aprovou produção, se o artefato remoto tem esses mesmos bytes, nem se um health check de produção passou. Essas evidências exigem vinculação à execução confiável do GitHub Actions, às regras de ambiente e ao provedor de hospedagem. Sua execução em uma máquina não confiável não fornece atestação independente.

## Integração G6 no contexto de CI do produto

No pipeline de **push da branch principal** de um produto, após construir o artefato e preparar o plano G6, o runner pode executar:

```bash
python3 vendor/product-platform-kit/scripts/verify-deployment-ci-context.py \
  --plan deployment-plan.json \
  --checkout "$GITHUB_WORKSPACE" \
  --artifact dist/release.tgz \
  --repository "$GITHUB_REPOSITORY"
```

`vendor/product-platform-kit` é apenas um exemplo: fixe o Kit por **commit completo/release imutável** e revise o script antes de integrá-lo, sem baixar código flutuante de `main` durante um job de deploy. O verificador exige `GITHUB_ACTIONS=true`, evento `push`, ref `refs/heads/main`, repositório esperado, ID de execução, SHA do evento idêntico ao HEAD e checkout idêntico ao `GITHUB_WORKSPACE`; também executa o gate G6 e calcula SHA-256 dos bytes reais do artefato. PRs, forks, tags inesperadas, HEAD divergente e artefato modificado são bloqueados.

**É uma verificação local de consistência do contexto, não atestação criptográfica do GitHub**: variáveis de ambiente podem ser falsificadas em um runner não confiável. Para uma decisão de deploy, use contexto autenticado pelo GitHub, permissions mínimas, ambientes protegidos, artefatos vinculados a um run confiável, approvals reais e verificações da plataforma. A saída `CI_CONTEXT_AND_ARTIFACT_VERIFIED` ainda mantém `authorized_to_deploy=false`; nunca faça `deploy` automaticamente apenas pelo código de saída desse script.

A referência `artifact_ref` deve terminar com `@sha256:<digest exato do plano>`, eliminando aliases flutuantes. Isso confirma só a forma da referência; a integridade **remota** do registry ainda precisa ser verificada pelo adapter do produto.

## Separação obrigatória entre política e autoridade

Este validador nunca dispara deploy, cria ambiente, dispara rollback, aprova produção ou executa comandos fornecidos no JSON. **Não** conecta secrets. No CI/CD de cada produto, a identidade de quem aprova, o hash da artefato, a origem do commit, a execução dos testes, a correspondência com o registry e a saúde real da aplicação devem ser verificadas por provedores e runners confiáveis. Um JSON que diga `approval=approved` **não** autoriza uma publicação. Defina regras de ambiente e aprovações humanas próprias no repositório produto.

Para migrações: EXPAND separado e compatível antes de implantar; rollback de código nunca reverte dados; CONTRACT apenas em release posterior. Preview pode ser deletado de acordo com o ciclo do PR; staging e produção exigem observabilidade, rollback planejado e controle de custos.

## Próximas entregas ainda pendentes

- Adapters de GitHub Actions reutilizáveis, path-filtered, que leem esse contrato e **conferem** evidências reais em vez de confiar em JSON autodeclarado;
- deploy real de pelo menos um produto escolhido, com proteção do ambiente, health check e rollback demonstrados;
- canário/progressivo dependente da plataforma de hospedagem, SLOs, custos, logs e alarmes;
- proveniência verificável dos artefatos, revisão independente dos workflows de release, revisão humana de produção.

**Estado:** política G6 e testes offline implementados no Kit. Nenhum deploy de produto, ambiente real, proteção de ambiente, rollback ou autenticação é implementado por este incremento.
