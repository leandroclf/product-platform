# New product composition protocol

A new product starts from capabilities, not copied repositories.

## 1. Conceive

Provide the idea plus `contracts/capability-registry.yaml` to product-platform-cli.

```bash
omnicli conceive "<idea>" --refine --loops 3 \
  --portfolio-context /path/to/product-platform-kit/contracts/capability-registry.yaml
```

The proposal must produce a REUSE / EXTEND / CREATE resolution.

## 2. Handoff

Persist the registry SHA-256 and capability decisions in the AI Team handoff. If the registry changes before implementation, re-resolve affected decisions.

## 3. Execute

For EXTEND:
- change the canonical owner first;
- validate and release an immutable version;
- update the product consumer;
- remove any superseded local implementation only after consumer validation.

For REUSE:
- pin an immutable version and add only product-specific configuration/adapters.

For CREATE:
- create only product-domain behavior and assign ownership.

## 4. Shared platform

Expected reusable composition:

```
new-product
  -> product-platform-kit contracts/policies
  -> product-platform-harness/core
  -> product-platform-harness/growth (optional)
  -> product-platform-harness/commerce (optional)
  -> product-platform-harness/economics (optional)
  -> product-platform-harness/observability
  -> product-specific domain
```

No product may source-depend on another product.

## 5. Publicação obrigatória no portal corporativo

**`site-lf-solucoes` é o produto principal do portfólio** e a porta de entrada pública para todos os demais produtos. Seu endereço oficial é `https://lfsolucoes.etc.br/`; o catálogo vive em `/produtos/`. O repositório de site mantém `data/product-catalog.json`, de onde são geradas uma página de catálogo e uma página de apresentação para cada produto.

- Cada produto novo registrado em `contracts/portfolio-products.json` deve produzir, **na mesma entrega de onboarding**, um PR correspondente no `leandroclf/site-lf-solucoes` com descrição editorial, categoria, benefícios verificáveis e página individual.
- A publicação pública é revisada, não pode expor secrets, dados pessoais, endereços internos ou prometer serviço disponível sem evidência.
- Publicação do portal e deploy dos aplicativos são independentes. A página pode explicar o produto sem anunciar URL de acesso público ainda não verificada.
- `product-platform` define a obrigação do handoff; o site é o dono do conteúdo comercial e visual. Não duplicar marketing em Kit/Harness ou copiar o runtime do produto para o portal.
- O fluxo de sincronização cross-repository ainda precisa ser implementado por GitHub App/PR confiável. Até lá, concluir um novo onboarding exige comprovação do PR de catálogo + validação do site.

## 6. Definition of done

A new product is composition-complete when:
- every requested capability has a resolution;
- no duplicate registered capability exists in product source;
- shared dependencies are immutable/pinned;
- contract/conformance tests pass;
- product integration tests pass;
- deployment follows expand -> deploy -> observe -> later contract;
- portal LF has a reviewed product listing/individual page in `site-lf-solucoes` or the onboarding is marked incomplete.
