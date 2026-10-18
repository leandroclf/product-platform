# LF Soluções — identidade corporativa no portfólio (primeiro gate)

## Fonte institucional

- Site de referência: https://lfsolucoes.etc.br/
- Logotipo referenciado no HTML: https://lfsolucoes.etc.br/assets/lf-logo-horizontal.svg
- Nome institucional: **LF Soluções**.
- Assinatura textual confirmada no site: **Tecnologia que gera valor.**
- Qualidades explicitadas no site: **Confiável. Profissional. Atemporal.**
- Posicionamento editorial confirmado: **Engenharia aplicada a negócios**.
- Referência contratual versionada: `../contracts/lf-brand-source.json`.

**Limite deliberado:** ainda não há cópia verificável do SVG/CSS original no repositório nem leitura auditável dos valores de cor, tipografia, grid, ícones e geometria do símbolo. Os campos `visual.*` ficam nulos. Não inferir RGB/HEX, fonte ou redesenhar o logotipo a partir de conteúdo textual da página. Não usar hotlink do ativo remoto nos produtos: baixar, registrar proveniência, conferir licença de uso, conteúdo e SHA-256 e publicar uma versão imutável de assets.

## Estratégia de distribuição

1. **Kit** mantém o contrato da fonte, política de composição visual e regras de consistência.
2. Criar o futuro módulo **`packages/design-system`** após a extração auditada. Ele será dono de ativos e design tokens; não inserir componentes de UI no Harness (bibliotecas de comércio/observabilidade).
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

**Este gate não altera visualmente os nove produtos**: registra a fonte e bloqueia a falsa afirmação de cores ou logotipo já extraídos. A adoção visual exige extração do design real, PR por consumidor e validação.

## Critérios de aceite do módulo visual

- Asset LF local aprovado com checksum e URL de origem.
- Paleta, tipografia e demais tokens conferidos contra folhas de estilo ou SVG reais da fonte.
- Licença/proveniência revisada antes de redistribuir.
- WCAG AA auditado nos temas claros/escuros e estados.
- Versão semver, changelog, consumidores com versões fixadas.
- Personalização do produto sem sobrepor tokens corporativos fora do contrato.
