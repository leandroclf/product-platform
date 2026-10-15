# Esteira de entrega da plataforma de produtos

Contrato operacional para que um repositório alvo seja implementado conforme as regras da plataforma. Este documento é a fonte canônica; os demais repositórios apenas o referenciam.

## Papéis (um dono por capacidade)

| Pacote (em `packages/`, repositório `product-platform`) | Papel na esteira | Dono de |
| --- | --- | --- |
| `product-platform-cli` | Transforma o pedido inicial em proposta revisável e handoff | `proposal_generation` |
| `product-platform-kit` | Define regras, contratos, registry, políticas e skills | contratos compartilhados, gates, conformance |
| `product-platform-harness` | Runtime reutilizável embutido nos produtos (eventos, entitlements, pagamentos, economics, observabilidade) | capacidades de runtime |
| `product-platform-engineering-team` (`ai-team`) | Executa plan → implement → validate → review no alvo | `engineering_delivery` |
| Repositório alvo (produto) | Lógica de domínio, pontos de emissão, sinks e adapters próprios | domínio do produto |

Dependências permitidas (`contracts/repository-boundaries.yaml`; dentro da plataforma, `platform-packages.json` verificado por `scripts/check-package-boundaries.py`): produto → kit e harness; cli, engineering-team e harness → kit; kit → ninguém; produto → produto é proibido. Os quatro pacotes da plataforma vivem em um só repositório (`leandroclf/product-platform`); os produtos continuam em repositórios próprios e consomem o harness por artefato de release.

## Fluxo

```
pedido inicial
  └─ 1. CLI: omnicli conceive --refine --portfolio-context <registry do kit>
        └─ proposta.md + manifest (portfolio_fingerprint)
  └─ 2. Revisão humana da proposta
  └─ 3. Handoff (EngineeringProposalHandoff v1 + PortfolioCapabilityHandoff + rules_refs)
  └─ 4. Gate G1 (resolução de capacidades) antes do PLAN
  └─ 5. ai-team init/run no alvo, com regras da plataforma aplicadas (G2)
        plan → implement → checks offline (G3) → validate → review (G4)
  └─ 6. ai-team deliver --pr (draft)
  └─ 7. CI do alvo no SHA final (G5); merge e deploy são ações separadas (G6)
```

## Gates

| Gate | Quando | Regra | Fonte | Estado de automação |
| --- | --- | --- | --- | --- |
| G0 Proposta | fim do CLI | Escopo, riscos, decisões e critérios de aceite presentes; registry hasheado no manifest | `product-platform-cli/docs/fluxo-engenharia.md` | Implementado: `conceive --envelope-out` gera proposta, capacidades e regras no envelope completo; o kit valida schema e G1 e o `ai-team` congela os três componentes. A revisão humana da proposta permanece obrigatória |
| G1 Capacidades | antes do PLAN | Cada capacidade resolvida em REUSE > EXTEND > CREATE; parar se duplicar capacidade registrada, houver dependência produto→produto, EXTEND mirar o consumidor ou o registry estiver defasado | `contracts/capability-registry.yaml`, `engineering-team/docs/CAPABILITY-RESOLUTION-GATE.md` | Automático: `scripts/validate-platform-handoff.py` (kit) confere schema, fingerprint, nomes e donos contra o registry; no `ai-team`, `run --handoff` valida e congela, `--registry` bloqueia registry defasado e o plano deve declarar `capability_decisions` idênticas ao handoff |
| G2 Regras | início de cada etapa | O agente recebe as regras da plataforma (este documento, `AGENTS.md` do kit, políticas do harness) com versão/SHA registrados | este documento | Automático: `ai-team run --rules` congela, hasheia e monta as regras em todas as etapas |
| G3 Checks | após IMPLEMENT | Lint, testes, build, conformance de ProductEvent e validação do artefato do harness no container offline | `init --check` do alvo | Manual por projeto |
| G4 Revisão | após validate | Compatibilidade, segurança, observabilidade e ausência de duplicação de capacidade | gates de review do engineering-team | Automático (qualidade/segurança fixos) |
| G5 CI | após deliver | CI do alvo verde no SHA revisado | CI do repositório alvo | Externo |
| G6 Release | separado | Merge/deploy autorizados à parte; deploy expand → deploy → observe → contract | `docs/NEW-PRODUCT-COMPOSITION.md` | Fora do `ai-team` |

## Regras que todo alvo deve cumprir

1. **Dependências**: apenas kit e harness; versão imutável (SHA completo ou artefato com checksum), nunca branch flutuante. Padrão de referência: `vehicle-tracking/vendor/harness-artifact.json`.
2. **Capacidades**: nenhuma implementação local de capacidade registrada (eventos, entitlements, pagamentos, ledger, observabilidade). Migração: introduzir dependência pinada → trocar imports → CI do produto → só então remover a cópia local.
3. **ProductEvent**: schema v1 do kit sem fork; `product_id` e `release_sha` obrigatórios; sem PII, documentos, OCR, GPS, IMEI ou credenciais; falha de analytics/CRM nunca derruba a requisição (`docs/PRODUCT-HARNESS.md`, `docs/CONFORMANCE.md`).
4. **Entitlements**: decisão sempre no servidor; limite ausente significa ilimitado; quota estrita exige persistência atômica própria do produto.
5. **Banco e migrações**: PostgreSQL próprio do produto; migrações EXPAND aplicadas pelo produto, nunca no import/startup; rollback só de código; CONTRACT em release separada.
6. **Telemetria**: atributos seguros (`product.id`, `deployment.environment`, `service.version`); telemetria externa desligada por padrão onde o registry exige (FiveM, English Coach).
7. **Agentes**: `AGENTS.md` do alvo pode endurecer, nunca enfraquecer, as regras da plataforma. Capacidades privilegiadas ficam `off` sem intenção explícita.

## Handoff mínimo para o time de agentes

Além dos campos de `EngineeringProposalHandoff` v1 (repositório, base SHA, objetivo, escopo, critérios, risco, evidências), o pacote entregue ao `ai-team` deve conter:

- `registry_fingerprint` e resolução REUSE/EXTEND/CREATE por capacidade (`PortfolioCapabilityHandoff`);
- `rules_refs`: versão ou SHA do kit e do harness cujas regras se aplicam, e o perfil do kit (`core`, `backend`, `frontend`, `devops`, `security`);
- capacidades que exigem mudança no dono canônico antes do consumidor (EXTEND), como itens de trabalho em repositórios separados.

O contrato único é o envelope `PlatformHandoff` (`contracts/platform-handoff/v1.schema.json`), que compõe proposta, capacidades e `rules_refs` (kit e harness por SHA completo, mais o perfil), com `additionalProperties: false` em todos os níveis. Os schemas de proposta (cli) e de capacidades (engineering-team) são subconjuntos dele; o JSON simples de capacidades do `conceive --handoff-out` continua válido.

Valide antes do `ai-team run`:

```bash
python3 scripts/validate-platform-handoff.py capacidades.json   # saída 0 = válido; requer PyYAML e jsonschema
python3 scripts/validate-platform-handoff.py --fingerprint      # sha256 do registry (igual ao do omnicli e do ai-team)
```

O validador reporta as condições de parada do G1: registry defasado, CREATE que duplica capacidade registrada, CREATE sem dono do portfólio, REUSE/EXTEND de capacidade inexistente ou que não mira o dono canônico, e dependência produto→produto.

## Mudanças que cruzam pacotes da plataforma

Contrato, harness, cli e engineering-team são pacotes de um mesmo repositório. Uma mudança que toque mais de um (por exemplo contrato no kit e implementação no harness) é uma única tarefa do `ai-team`, uma branch e um PR no repositório da plataforma. O gate G1 continua valendo para o produto alvo; dentro da plataforma, a ordem kit → harness → consumidores é garantida pelo grafo de pacotes e pelo CI por caminho.

## Aplicação interina (até existir automação)

O `ai-team run` aceita `--handoff` e `--rules` (ver `product-platform-engineering-team/docs/LOCAL-LINUX-WORKFLOW.md`), o que cobre a entrega das regras e do handoff aos agentes. Ainda por tarefa, manualmente:

1. No alvo, commitar um `AGENTS.md` que referencie este documento e fixe a versão do kit/harness (modelo em `templates/TARGET-AGENTS.md`).
2. Gerar o envelope com `omnicli conceive --envelope-out` (ou só as capacidades com `--handoff-out`), validá-lo com `scripts/validate-platform-handoff.py` e passá-lo com `--handoff` (e o registry com `--registry`); passar este documento e o `AGENTS.md` do harness com `--rules`.
3. Configurar em `ai-team init --check` os checks de G3 (conformance de ProductEvent, validação do artefato do harness).
4. Conferir manualmente G1 no plano do Atlas antes de aceitar a implementação.

## Evolução (backlog de automação)

Em ordem de dependência. Mudanças entre pacotes da plataforma cabem em uma única tarefa; mudanças nos produtos exigem tarefas nos respectivos repositórios.

| # | Repositório | Mudança | Resultado |
| --- | --- | --- | --- |
| 1 | cli | **Feito**: `conceive --handoff-out` emite o `PortfolioCapabilityHandoff` e `--envelope-out` emite o envelope `PlatformHandoff` completo (proposta, capacidades e `rules_refs`); o fingerprint, o `proposal_id`, o repositório e as versões de regras vêm do CLI e do operador, nunca do modelo | G0 verificável |
| 2 | kit | **Feito**: envelope `PlatformHandoff` v1, `scripts/validate-platform-handoff.py` (fingerprint e G1 contra o registry) e, na raiz do repositório, `scripts/test_handoff_contract.py` (cli → kit → ai-team, executado no workflow `platform`); o CLI e o `ai-team` aceitam o envelope | contrato único |
| 3 | engineering-team | **Feito**: `run --handoff`, `--rules` e `--registry` validados e congelados com hash; `capability_decisions` no plano verificado pelo host | G1 e G2 automáticos |
| 4 | engineering-team | Check de conformidade como fase própria do host | G3 padronizado |
| 5 | kit | Substituir checagens manuais/substring de conformance por validação JSON Schema; fixtures e runner para `payment-event/v1`; remover cópias legadas do ProductEvent após migração dos consumidores | G3 confiável |
| 6 | harness | **Parcial**: CI executa build e testes TypeScript/Python contra o corpus canônico do kit; `harness-v0.2.1` publicado com tarball, wheel e checksums. Lint dedicado e integração completa de pagamentos permanecem pendentes | alvos já podem pinar o artefato publicado |
| 7 | todos | Concluir a troca de nomes legados nos READMEs, ROADMAPs e pacotes SDK (o validador de nomes aposentados lista os pontos) | nomenclatura única |

## Lacunas conhecidas (fatos verificados nos repositórios)

- O contrato completo CLI → kit → `ai-team` é coberto por `scripts/test_handoff_contract.py`. A jornada com concepção autenticada, revisão humana e entrega em produto real ainda precisa de aceitação; ver [baseline e piloto](PLATFORM-READINESS.md).
- O host confere a decisão declarada no plano, não o código produzido; a ausência de duplicação de capacidade na implementação depende de Sentinel e da revisão.
- O harness está `partial` no registry (sem inbox durável, outbox, ledger persistido, reserva atômica de uso). Isso limita suas capacidades, não a existência da release: `harness-v0.2.1` foi publicado em 2026-10-07 e conferido em 2026-10-14.
- O manifesto do kit no alvo (`pin: ^0.1`) não é validado nem aplicado por nenhum script.

## Validação com provedores reais (2026-10-07)

Um pedido real passou por Codex e Claude em um repositório de teste, usando o envelope gerado pelo código do CLI, `--registry` e `--rules`:

- O envelope foi aceito, dividido e congelado com SHA-256; as quatro etapas ficaram presas ao mesmo fingerprint de plataforma.
- O Atlas declarou `capability_decisions` idênticas ao handoff, citou os SHAs do kit e do harness e o perfil, e **bloqueou** quando o pedido saía do `allowed_paths`.
- Plan, implement, checks offline, validate e review fecharam sem ciclos de reparo; Sentinel e revisor aprovaram os cinco critérios com evidência e o mesmo `head_sha`; a entrega criou a branch `ai-team/<task>` sem tocar no checkout do alvo.
- Limites desta execução: repositório de brinquedo, modelos intermediários e envelope montado sem executar os provedores do `product-platform-cli`. Ela não comprova a jornada conjunta de concepção e implementação em produto real; a evidência anterior do pipeline de concepção está em `packages/cli/docs/production-transition-status.md` e a consolidação atual em [PLATFORM-READINESS.md](PLATFORM-READINESS.md).
- Defeitos encontrados e corrigidos: o gate de capacidades mascarava um plano `BLOCKED` com uma mensagem enganosa, e o prompt não dizia que o host grava o OpenSpec fora do escopo do agente.
- Limitação conhecida: o `doctor` não detecta token de login vencido (ver `LOCAL-LINUX-WORKFLOW.md`, diagnóstico de falhas).
