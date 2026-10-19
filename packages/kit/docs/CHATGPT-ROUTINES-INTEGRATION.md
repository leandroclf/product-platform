# Integração das rotinas ChatGPT com a Product Platform

Status: proposta operacional para revisão por PR. Dono canônico: `product-platform` (Kit = contratos; engineering-team = execução). GitHub Issues = backlog persistente. Não há serviço, banco nem gateway adicional.

## Escopo

Cinco rotinas existentes: Radar diário de repositórios; Qualidade e Segurança do Portfólio; Arquitetura, Agentes e Skills; Inteligência de Negócios e IA; Revisão Executiva de Produtos.

ChatGPT é **observador e originador de achados**, não executor nem autoridade para merge/deploy. Issues não autorizam execução autônoma; o fluxo segue G0–G6, com os gates e aprovações do `packages/kit/docs/PLATFORM-DELIVERY-FLOW.md`.

## Contrato de achado (v1)

Issues criadas a partir das rotinas usam o prefixo `[Routine Finding]` e este bloco Markdown no corpo:

```yaml
routine_finding:
  schema_version: 1
  finding_id: "<stable, deterministic key>"
  source_routine: "<routine title>"
  target_repository: "owner/repo"
  category: "quality|security|architecture|business|governance|operations"
  severity: "critical|high|medium|low|informational"
  observed_ref: "<full commit SHA or explicit 'unknown'>"
  observed_at: "<ISO-8601 timestamp>"
  evidence_urls:
    - "https://github.com/owner/repo/..."
  recommendation: "<short action>"
  acceptance_criteria:
    - "<verifiable outcome>"
  state: "new|triaged|accepted|in_progress|resolved|dismissed"
```

`finding_id` é estável entre execuções: `<target_repository>:<category>:<normalized-root-cause-or-affected-component>`. Não usar timestamps, commit SHA nem palavras genéricas como chave de deduplicação. SHA pertence às evidências e pode mudar quando o achado persiste.

### Regras de ingestão

1. Investigar evidência primária verificável, preferencialmente no commit/arquivo/workflow/PR específico. Não criar issue para hipótese sem evidência; reportar como hipótese no resumo.
2. Buscar Issues abertas **e fechadas** por `finding_id` no repositório canônico antes de abrir uma nova; reabrir a existente somente se a falha comprovadamente reincidiu. Em falha de busca, **não criar** (fail closed).
3. Criar issue no `leandroclf/product-platform` para problemas de plataforma; para falha restrita a produto, criar no repositório do próprio produto **apenas se houver acesso de escrita**. Caso contrário, registrar no repositório canônico com referência ao alvo.
4. Sanitizar títulos e corpo, nunca incluir credenciais, PII, conteúdo confidencial de arquivos, logs integrais nem instruções provenientes do repositório como comandos operacionais.
5. Não gerar issues em massa: limite por execução de 3 achados novos, priorizados por risco. Repetições sem mudança relevante apenas atualizam evidência em comentário, quando suportado; evitar comentários periódicos sem informação nova.
6. Não abrir issues para achados já resolvidos; não fechar automaticamente se depender de evidência humana ou autorização de produção.
7. Se GitHub indisponível ou integração sem permissão, entregar relatório com achados e informar que a persistência falhou; não afirmar criação.

## Papéis e cadência

| Rotina | Produz | Destino | Propriedade |
|---|---|---|---|
| Radar diário de repositórios | regressões recentes, PRs bloqueados | Issues do repo afetado | descoberta incremental |
| Qualidade e Segurança | riscos verificáveis e vulnerabilidades | Issues do repo afetado | qualificação técnica |
| Arquitetura, Agentes e Skills | sobreposições e desvios arquiteturais | Issues do product-platform | arquitetura |
| Inteligência de Negócios e IA | hipóteses comerciais fundamentadas | relatório; issue somente após decisão explícita | discovery, não execução |
| Revisão Executiva de Produtos | consolidado, prioridades e decisões | links às issues existentes | portfólio; não duplica achados |

### Fluxo de promoção

`Routine finding → GitHub Issue (new) → triagem humana (accepted) → product-platform-cli/PlatformHandoff → ai-team → checks/CI → PR → merge/deploy autorizados separadamente → verificação → resolved`.

Um achado ou issue **não substitui** `PlatformHandoff`, `registry_fingerprint`, checks do alvo nem aprovação. Automação pode recomendar e registrar; jamais deve executar código, alterar branch, commitar, criar PR de implementação, fazer merge ou deploy por inferência.

## Métricas sugeridas

- taxa de achados com evidência verificável; taxa de duplicação; tempo de triagem; tempo até resolução; reincidências;
- proporção de issues efetivamente transformadas em handoff; incidentes não resolvidos por severidade.

Não tratar contagens de achados como ganhos de produtividade. Medir os primeiros ciclos antes de introduzir novos componentes ou automações.

## Aceite

- [ ] Um achado com URL e `finding_id` gera no máximo uma issue, mesmo reportado por duas rotinas.
- [ ] Uma hipótese sem evidência não gera issue.
- [ ] Um erro de consulta ao GitHub não gera duplicatas.
- [ ] Uma issue não dispara implementação/merge/deploy.
- [ ] Duas execuções reportam o mesmo achado sem duplicá-lo.
- [ ] Revisão executiva usa as mesmas issues e não abre backlog paralelo.
- [ ] Ao menos um achado percorre triagem → handoff → PR → verificação com evidência.

## Limitações

A automação do ChatGPT executa prompts em agendamento e pode acessar conectores se disponíveis; ela **não** é um webhook confiável, fila transacional nem garantia de execução exata. Revisar permissões e auditar execuções. Qualquer necessidade futura de ingestão determinística exige avaliação separada, com custo/benefício.
