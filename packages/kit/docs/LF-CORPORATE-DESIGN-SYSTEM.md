# LF Soluções — identidade corporativa no portfólio (primeiro gate)

## Fonte institucional

- Site de referência: https://lfsolucoes.etc.br/
- Logotipo referenciado no HTML: https://lfsolucoes.etc.br/assets/lf-logo-horizontal.svg
- Nome institucional: **LF Soluções**.
- Assinatura textual confirmada no site: **Tecnologia que gera valor.**
- Qualidades explicitadas no site: **Confiável. Profissional. Atemporal.**
- Posicionamento editorial confirmado: **Engenharia aplicada a negócios**.
- Referência contratual versionada: `../contracts/lf-brand-source.json`.

**Estado verificado:** os bytes de `brand-system.css`, `assets/lf-logo-horizontal.svg` e `assets/lf-mark.svg`, a paleta CSS, a fonte e as dimensões dos SVGs foram conferidos no commit `d85d2e622e3ebbcd23ae73c279ba7ef9bf09fac8` do repositório `leandroclf/site-lf-solucoes`. O CSS também define layouts específicos do portal (`.nav-solutions-grid`, `.brand-hero-layout` e `.section-heading`, com quebra em 920px); não declara um grid corporativo reutilizável. O contrato `../contracts/lf-brand-source.json` registra hashes e separa esses padrões do portal dos tokens corporativos; os SVGs locais passam por comparação de hash.

**Limite deliberado:** o repositório-fonte não declara licença de redistribuição. O status `SOURCE_VERIFIED_NOT_APPROVED` registra fatos de origem, não aprovação legal, de distribuição ou adoção. Não publicar o pacote nem adotá-lo em produtos até essas aprovações. Não usar hotlink remoto; preserve as marcas e cores funcionais dos produtos.

## Extração verificável dos arquivos originais

Quando os arquivos autorizados `lf-logo-horizontal.svg` e as folhas CSS do site estiverem disponíveis localmente, execute a ferramenta read-only (nenhum acesso externo ou publicação):

```bash
cd packages/kit
python3 scripts/inventory-lf-brand-assets.py /caminho/lf-logo-horizontal.svg /caminho/site.css
```

Para verificar outra revisão da fonte, o inventário em JSON lista hashes SHA-256, cores, variáveis e famílias tipográficas **candidatas**. A saída declara `REVIEW_REQUIRED_NOT_APPROVED`: inventário não aprova tokens nem licença. Faça a revisão contra o CSS/SVG oficial e atualize os hashes fixados no contrato e no pacote apenas depois de verificar a origem.

## Estratégia de distribuição

1. **Kit** mantém o contrato da fonte, política de composição visual e regras de consistência.
2. `packages/design-system` já contém SVGs e tokens com proveniência fixada. Ele é dono dos ativos e tokens da marca corporativa; não inserir componentes de UI no Harness (bibliotecas de comércio/observabilidade).
3. Publicar um pacote versionado com:
   - tokens de cores, tipografia, espaços, raios e estados em JSON + CSS custom properties;
   - ativos corporativos aprovados e variantes de logo;
   - componentes acessíveis React/Next quando houver consumidor React;
   - arquivos CSS independentes de framework para HTML estático, JavaScript vanilla e outros clientes;
   - padrões de arquitetura de informação e aplicação opcional de assinatura corporativa.
4. Compor dois níveis separados: `corporate` (assinatura e padrões LF) e `product` (identidade e semântica do produto). O `vehicle-tracking` preserva os sinais de estado de veículos; dashboards financeiros preservam sinais de risco; apps sem UI não recebem CSS.
5. Produtos consomem versões imutáveis, com teste de regressão de contraste, acessibilidade, responsividade e snapshots nas telas críticas. Não copiar componentes entre produtos.

## Adoção proposta por superfície

| Produto | Superfície esperada | Próxima validação |
|---|---|---|
| vehicle-tracking | Next.js + Tailwind | Auditar tokens locais, migrar somente assinatura corporativa e componentes comuns |
| agentic-travel-engine | frontend Next.js | Identificar tokens e componentes locais, introduzir pacote React |
| bussola-financeira | HTML | Introduzir tokens CSS e selo corporativo de forma opt-in |
| fivem-server-monitor-pro | web HTML/JS | Testar CSS independente e branding apenas no painel web |
| professional-english-coach | app JavaScript local-first | Garantir que o pacote opere sem rede |
| lf-worldbank-risk-pricing | HTML estático | Opt-in para CSS comum, sem mexer na lógica analítica |
| lf-openalex-enrichment-mvp | HTML estático | Idem |
| lf-wikidata-entity-graph | HTML estático | Idem |
| ai-docs | serviço/API | Documentação/portal somente se existir UI; nenhum pacote visual de runtime obrigatório |

**Este gate não altera visualmente os nove produtos**: registra fatos verificados da fonte e mantém redistribuição e adoção bloqueadas sem aprovação. A adoção visual exige PR por consumidor e validação.

## Critérios de aceite do módulo visual

- Asset LF local aprovado com checksum e URL de origem.
- Paleta, tipografia e demais tokens conferidos contra folhas de estilo ou SVG reais da fonte.
- Licença/proveniência revisada antes de redistribuir.
- WCAG AA auditado nos temas claros/escuros e estados.
- Versão semver, changelog, consumidores com versões fixadas.
- Personalização do produto sem sobrepor tokens corporativos fora do contrato.
