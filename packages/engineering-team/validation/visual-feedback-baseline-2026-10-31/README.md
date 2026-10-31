# Baseline visual da home LF Soluções

Esta captura registra a home pública no commit `3ff63351fca2ca3b0166bfe3056bca44e93368b1` do repositório `leandroclf/site-lf-solucoes`, árvore `8a899ac11b4f10c535dfb5816815def6b240bc23`. O checkout do produto ficou somente para leitura. A referência desktop é a própria captura da baseline e não representa uma especificação de design externa.

O Chrome Headless 152.0.7977.54 carregou a página em um namespace `bubblewrap --unshare-net`, com checkout de origem montado como somente leitura e perfil temporário. Foram capturados desktop (1440×900) e mobile (390×844). Os checks registrados passaram para overflow/layout, menu mobile, dropdown, skip-link, foco e navegação por teclado. As imagens foram inspecionadas diretamente. A fonte Google Fonts ficou inacessível; `document.fonts.check` não comprovou carregamento, e `fc-match Inter` no host resolveu para Noto Sans. O font-family efetivamente renderizado no Chrome não foi confirmado.

O uso de `file://` foi necessário porque o namespace isolado não permitiu subir um servidor HTTP de loopback. Portanto, a execução não valida comportamento servido por HTTP. A referência é autorreferenciada, não houve avaliação contra o site publicado nem comparação com feedback visual. A revisão de acessibilidade limita-se aos fluxos de teclado registrados e não é uma auditoria WCAG. A emulação de `prefers-reduced-motion: reduce` ocorreu durante a navegação do menu, mas não houve asserção de `matchMedia` nem da duração de rolagem; esse comportamento não é declarado aprovado. Nenhum modelo foi executado; custo é `null`; não há medição de performance, produtividade ou benefício do feedback visual.

O navegador não recebeu arquivos de perfil ou credenciais montados. O processo pai do runner herdou o ambiente do host, que não foi auditado; essa limitação está registrada em `evidence.v2.json` e no relatório do navegador. A navegação permaneceu isolada sem rota de rede.

Valide a integridade dos artefatos a partir da raiz do checkout:

```bash
python3 packages/engineering-team/scripts/validate_visual_feedback.py \
  --task packages/engineering-team/validation/visual-feedback-baseline-2026-10-31/task.v2.json \
  --evidence packages/engineering-team/validation/visual-feedback-baseline-2026-10-31/evidence.v2.json \
  --root packages/engineering-team/validation/visual-feedback-baseline-2026-10-31 \
  --expected-head 3ff63351fca2ca3b0166bfe3056bca44e93368b1
```

Capturas e hashes estão em `screenshots/` e os resultados reproduzíveis do runner em `checks/browser-report.json`. O estado `captured` registra a baseline; não declara aceitação de uma mudança de produto.
