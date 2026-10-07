# Evolução do portfólio — ciclo 1

Escopo aprovado: quatro repositórios de plataforma e os oito produtos de
[`portfolio-products.json`](../../contracts/portfolio-products.json).
O catálogo não representa prontidão de produção. `implementation_status: partial`
separa primitives existentes de capacidades planejadas.

## Resolução de capacidades

| Capacidade | Decisão | Proprietário | Adoção inicial |
| --- | --- | --- | --- |
| Contratos, catálogo e conformance | EXTEND | product-platform-kit | oito produtos |
| Eventos, decisão de limite, sinal comercial | REUSE | product-platform-harness | vehicle-tracking |
| Distribuição Python | EXTEND | product-platform-harness | preparar piloto Bússola |
| Geofences, identidade autenticada e persistência de outbox | REUSE | vehicle-tracking | manter adapters específicos |
| Reservas atômicas e inbox/outbox compartilhadas | EXTEND, futuro | product-platform-harness | demanda comprovada |

## Contratos mínimos de adoção

- Identidade: `product_id`, `environment`, `release_sha`; conta/usuário opacos
  somente quando houver identidade real no produto. Nunca inventar tenant.
- Eventos: [ProductEvent v1](../../contracts/product-event/v1.schema.json).
  Campos extras e PII são rejeitados pela conformance. Falha de analytics
  não altera o resultado da operação de domínio.
- Entitlement: plano, capacidade, uso e limite geram uma decisão de acesso.
  Limite ausente/nulo significa ilimitado na API existente. A decisão pura
  não reserva consumo nem impede concorrência; metering exige persistência e
  operação atômica futura antes de prometer quota estrita.
- Uso: escolher unidade e janela por produto (registros, buscas, geofences).
  Medir tentativas/sucessos separadamente; replay não pode duplicar consumo.
  Nenhum contador compartilhado persistente é alegado neste ciclo.
- Correlação: produto, ambiente, release e operação; payload de domínio não
  deve entrar em atributos de analytics/telemetria.
- Distribuição: versões/SHAs imutáveis; instalar o proprietário, validar o
  consumidor e só então substituir código local equivalente.
- FiveM permanece self-hosted e English Coach local-first. Dependência permitida
  não impõe SDK, conta, cobrança ou telemetria externa.

## Gates do piloto

1. Registrar SHA, branch e checks da baseline dos 12 repositórios.
2. Validar catálogo e fronteiras: oito produtos, quatro plataformas, nenhum
   produto como dependência de source de outro.
3. Verificar os mesmos casos de evento em TypeScript e Python.
4. Construir artefatos locais e instalar o Python em ambiente limpo.
5. Consumir no vehicle-tracking o artefato compilado do SHA remoto
   `ffb68c07dfbe491b804e3b59ad1e0ad791872e9e` do harness (API existente),
   com origem/checksum em `vendor/harness-artifact.json` do consumidor.
6. Testar limite, separação de contas, sinal diário e falha de sink.
7. Executar checks do consumidor; registrar falhas anteriores e resultados atuais.

Melhorias locais posteriores do harness não estão no SHA consumido pelo piloto.
Uma nova revisão só será adotada após publicação imutável e validação do consumidor.
Não habilitar pagamentos reais ou deploy a partir deste documento.

## Evidência

[`baseline-before.json`](baseline-before.json) registra checks anteriores à
migração. Inclui SHA da base e working tree observado; arquivos do coletor e
artefatos locais podem aparecer como alterações de preparação.

O coletor usa apenas a biblioteca padrão Python. Executar da raiz do kit:

```bash
python scripts/collect-portfolio-baseline.py --workspace .. \
  --python /caminho/venv/bin/python \
  --python-override bussola-financeira=/caminho/venv-bussola/bin/python \
  --python-override agentic-travel-engine=/caminho/venv-travel/bin/python \
  --timeout 90 --output docs/evolution/baseline-local.json
```

Preparar ambientes separados com dependências já declaradas. Bússola, Travel
e o coordenador fixam versões diferentes; compartilhar uma venv entre todos
produz conflitos. A baseline não chama provedores de IA nem certifica produção.
