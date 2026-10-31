# LF Soluções — Design System corporativo (versão fonte 0.1.0)

**Fonte canônica:** repositório `leandroclf/site-lf-solucoes`, commit [`d85d2e6`](https://github.com/leandroclf/site-lf-solucoes/commit/d85d2e622e3ebbcd23ae73c279ba7ef9bf09fac8). Paleta extraída diretamente das variáveis CSS `--brand-*` em `brand-system.css`; os SVGs são cópias byte a byte de `assets/lf-logo-horizontal.svg` e `assets/lf-mark.svg`.

## Contrato visual inicial

Os [padrões de interação candidatos](INTERACTION-PATTERNS.md) documentam comportamentos reutilizáveis e critérios de regressão; sua validação no browser e adoção pelos produtos permanecem explícitas.

- Cores oficiais: `#061B4F` navy, `#0757E8` blue, `#008CFF` electric, `#00D4FF` cyan, `#EAF6FF` ice, `#172033` graphite/text, `#526079` muted, `#D8E7F4` border, `#FFFFFF` white, `#14804A` success.
- Fonte institucional: **Inter**, seguida de system sans.
- Raio padrão: `14px`.
- Logotipo original horizontal e marca LF SVG.
- Proveniência: `tokens.json/source` fixa o commit de origem, os Git blob SHA-1 e SHA-256 do CSS e dos SVGs. A suíte `scripts/test_lf_design_system.py` verifica localmente os dois hashes de cada SVG e os tokens CSS/JSON.
- `tokens.css` contém apenas custom properties com prefixo `--lf-`; não altera estilos de `html`, `body`, títulos nem cores funcionais de produtos por padrão.

## Contrato de tema

- `themes.corporate` oferece tokens semânticos namespaced para superfície, texto, ação primária, destaque e sucesso. As seis combinações de texto declaradas passam WCAG AA para texto normal (contraste mínimo 4.5:1); isso não certifica outros pares, tamanhos, estados, componentes ou telas.
- `themes.product` mantém a identidade e as cores funcionais de cada produto sob responsabilidade do consumidor. A assinatura corporativa é opt-in e os aliases CSS não aplicam regras visuais nem sobrescrevem seletores globais.

## Uso opt-in

Copiar/distribuir o pacote sob versão/release imutável aprovada antes de uso em consumidores. Na interface, importar `tokens.css` e renderizar os SVGs locais onde fizer sentido para indicar `Produto LF Soluções`. Não fazer hotlink no domínio institucional, não copiar CSS global inteiro do portal, não forçar aparência idêntica em aplicativos especializados.

O código-fonte do site não declara uma licença de redistribuição. Portanto, a procedência e a integridade dos bytes estão verificadas, mas a aprovação de redistribuição continua pendente. Também não há publicação externa no npm/registry, pacote React de componentes, garantia WCAG AA para todas as combinações, nem adoção automática nos nove produtos. Este pacote privado não autoriza publicação nem mudança visual remota.

## Próximos gates

1. Distribuição versionada com checksum e documentação de instalação;
2. CSS primitives acessíveis e, conforme demanda, componentes React compatíveis com consumidores Next.js;
3. Testes de contraste WCAG e regressão visual;
4. Migração piloto `vehicle-tracking` e `agentic-travel-engine`, sem modificar a semântica de estados; depois HTML e local-first;
5. Auditoria de licenciamento/publicação do pacote caso seja distribuído fora dos repositórios da LF.

## Distribuição local candidata

Use na raiz `python3 scripts/policy_bundle.py build --package design-system
--version 0.1.0 --output-dir /tmp/design-candidate` (uma única linha). Instale com
o subcomando `install`, checksum explícito e destino versionado inexistente,
conforme `packages/kit/docs/DISTRIBUTION.md`. A regressão de roundtrip compara
todos os bytes instalados aos arquivos canônicos; não substitui revisão visual
do produto ou autorização de redistribuição externa.
