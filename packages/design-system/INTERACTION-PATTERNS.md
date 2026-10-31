# Padrões de interação — catálogo inicial

Este catálogo registra comportamento, além de aparência. É documentação candidata para adoção opt-in; não publica componentes novos nem declara conformidade. O código nativo do produto continua sendo a implementação. Não copiar implementações entre produtos: extrair componente compartilhado só depois de verificar repetição e compatibilidade.

Referência observada por leitura de código: [site-lf-solucoes, SHA fad21f5](https://github.com/leandroclf/site-lf-solucoes/tree/fad21f52d42b25a9fe9268156d1c0f2fdd83a73d). A execução visual desse piloto está bloqueada; os comportamentos abaixo precisam de teste real antes do aceite.

| ID | Contrato candidato | Referência nativa | Critérios de regressão |
| --- | --- | --- | --- |
| nav-disclosure | Botão expõe estado aberto/fechado; dropdown permite navegar e retornar ao acionador | `index.html`: solutions-menu; `script.js`: toggleDropdown/closeDropdown, ArrowDown/Escape | Estado ARIA acompanha abertura; Escape fecha dropdown e retorna foco; links permanecem alcançáveis. O comportamento Escape do menu mobile completo é uma decisão separada, não comprovada pelo dropdown |
| skip-content | Navegação por teclado permite pular cabeçalho e chegar ao conteúdo | `index.html`: skip-link e main; `script.js`: identificação conteudo | Link visível ao foco, destino existente e ordem de navegação coerente; observar foco real no browser |
| reduced-motion | Preferência por movimento reduzido altera o comportamento da rolagem suave | `script.js`: prefers-reduced-motion | Emulação de preferência reduzida não usa smooth scroll; preferência normal mantém navegação; não extrapolar isso para todas as animações |

Ao adotar um padrão, a especificação de UX aponta o ID, o componente/caminho real e as diferenças locais. Estados loading/empty/error/disabled são definidos pelo fluxo concreto; ausência não equivale a aprovação. Para novos padrões, registre necessidade, interações, estados, dono dos dados, teclado/toque e critérios. Não introduzir i18n, barramento de eventos, gamepad ou efeitos visuais obrigatórios em produtos que não precisam deles.

Antes/depois deve usar os mesmos critérios e viewports. Mudanças em padrões compartilhados ampliam o mapa de consumidores afetados e os testes de regressão, sem desativar controles. Medições de acessibilidade, comportamento e performance continuam separadas de similaridade visual.
