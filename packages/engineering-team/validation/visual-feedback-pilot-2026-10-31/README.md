# Piloto de feedback visual — 31/10/2026

**Estado: BLOCKED, não aprovado.** Alvo: home de `leandroclf/site-lf-solucoes`, SHA `fad21f52d42b25a9fe9268156d1c0f2fdd83a73d`. Checkout local limpo; index.html teve seu hash registrado em `reference-source.json`, sem copiar código do produto para a plataforma.

Playwright estava disponível nas ferramentas do host, mas o Chromium não estava instalado. A tentativa de instalação terminou com ZIP inválido (`End of central directory record signature not found`). Nenhum browser foi iniciado, nenhuma captura foi obtida e nenhum critério foi avaliado. Não há evidência de ganho ou comparação entre agentes.

`task.json` é o plano congelado, `evidence.json` conserva checks `not-run`, screenshots vazias e limitações. A referência contém apenas procedência do código: antes da implementação visual é obrigatório obter uma referência visual autorizada, atualizar a tarefa e produzir novo hash.

Para reproduzir o teste de integridade, da raiz de packages/engineering-team:

```bash
python3 scripts/validate_visual_feedback.py \
  --task validation/visual-feedback-pilot-2026-10-31/task.json \
  --evidence validation/visual-feedback-pilot-2026-10-31/evidence.json \
  --root validation/visual-feedback-pilot-2026-10-31 \
  --expected-head fad21f52d42b25a9fe9268156d1c0f2fdd83a73d
```

Exit code zero comprova apenas que o registro bloqueado tem integridade estrutural. Retomar a captura em runner aprovado e isolado com Chromium disponível; manter checkout/SHAs conferidos, bloquear egress de produção, capturar desktop/mobile e registrar tempo real da captura. Depois executar a tarefa comparativa de implementação com os quatro estágios autenticados existentes.

## Verificação deste incremento

- Oito testes novos de integridade passaram: ausência/duplicação, SHA/digest, viewport/PNG, caminhos/symlinks, orçamento, JSON inválido e leitura limitada antes de alocar arquivos grandes.
- 146 testes da raiz passaram; conformance do kit e fronteiras de pacotes passaram.
- Validadores de documentação (141 documentos), framework (76 artefatos) e hardening passaram.
- Suíte unit completa do engineering-team: 183 testes, 180 passaram e três erros em `test_implement_parts.py` por `setfacl` ausente no host. Os mesmos três erros foram reproduzidos no checkout limpo da base `45dc09745969c59eb5cd2876d073d758e61cc9be` (cinco testes desse arquivo: dois passaram e três erros). Não foram relaxados testes nem permissões para ocultar o bloqueio.
- Nenhuma execução autenticada dos quatro estágios, captura visual ou ganho de produtividade é declarado por esses resultados.

## Continuação: evolução iterativa v2

`task.v2.json` acrescenta UX, estados, impacto e vínculos com regressões; `evidence.v2.json` preserva o bloqueio. `browser-preflight.txt` registra a alternativa cloud: navegação pública e um reload retornaram erro de conexão upstream, sem renderizar a aplicação. Isso não prova que o site esteja indisponível para o usuário ou em todas as redes.

A integridade v2 passa para esse registro bloqueado; o modo `--require-acceptance --checkout ...` retorna não zero, como esperado. Nenhuma captura antiga, JSON de procedência ou erro de conexão substitui uma referência visual e os testes de interação. O registro v1 original continua inalterado.

O incremento acrescenta gate opt-in de pré-requisitos, não instalação automática em produtos. Modelo de UX e catálogo de padrões são candidatos; a comparação real baseline/feedback, medições de performance e rollout por produto continuam dependentes do piloto executável e da revisão GitHub.

### Verificação da continuação

- 30 testes focados passaram (integridade v1, aceite v2 e classificação), incluindo conteúdo alterado com size/mtime preservados e configuração de clean filter que não deve executar.
- Suíte unit completa: 198 testes, 195 passaram e os mesmos três erros locais por `setfacl` ausente, já reproduzidos na base; não houve relaxamento de teste ou permissão.
- 146 testes da raiz, 46 de handoff, conformance, fronteiras e validadores de documentação/framework/hardening passaram.
- CLI local Python3.12: 104 testes, Ruff, mypy e pip check passaram. Auditor2.10.1 com filelock4.2.5: 53 pacotes, zero vulnerabilidades conhecidas reportadas. Teste negativo `--path` contra metadados de filelock3.32.7 retornou13 achados e exit1 mesmo com auditor limpo, comprovando que o diretório-alvo não foi substituído silenciosamente pelo ambiente da ferramenta.
- A sintaxe YAML e todos os blocos shell do workflow de auditoria foram verificados. Os resultados da matriz remota, especialmente3.10, continuam necessários; esse teste local não a substitui.
