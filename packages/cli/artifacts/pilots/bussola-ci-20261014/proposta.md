# Proposta Mestra — Incluir testes de integridade de ingestão no CI (Bússola Financeira)

## 1. Contexto e objetivo

Incluir no workflow de CI os dois testes determinísticos já existentes em `tests/test_ingestion_integrity.py`, sem afetar a validação atual do artefato do harness (`scripts/validate_harness_artifact.py`) nem os testes de `tests/test_product_events.py`. O CI hoje instala `requirements.txt` e `requirements-dev.txt`, mas só executa os testes de eventos de produto.

## 2. Fatos, hipóteses e recomendações (separados)

**Fatos confirmados nos trechos fornecidos:**
- `.github/workflows/ci.yml` roda, nesta ordem: `validate_harness_artifact.py`, instalação de dependências, e `pytest tests/test_product_events.py -q` (arquivo citado, L5-L11).
- `src/bussola_financeira/config.py` define `database_url` com padrão `sqlite:///./data/app.db` — arquivo, não memória.
- `src/bussola_financeira/providers.py` contém funções (`_http_get_bytes`, `_http_get_json`) que abrem `httpx.Client` e fazem chamadas HTTP reais.
- O conteúdo de `tests/test_ingestion_integrity.py` **não está nos trechos fornecidos**. Não há evidência direta de que os dois testes usam SQLite em memória e um provedor fake — essa é uma afirmação da ideia original, não verificada no código mostrado.

**Hipóteses (não confirmadas):**
- É plausível que os testes já isolem rede/banco via fixtures (`monkeypatch`, `database_url` sobrescrito para `sqlite:///:memory:`, provedor fake injetado), dado o padrão comum para testes determinísticos. Mas, sem o arquivo completo, isso permanece hipótese.
- Se o arquivo importar módulos que instanciam configuração ou provedores reais na importação (não só na chamada), a suíte poderia tocar o banco padrão em arquivo ou, no pior caso, tentar acessar rede antes de qualquer override.

**Recomendação:** ler o arquivo completo de `tests/test_ingestion_integrity.py` antes de abrir o PR — passo trivial e de custo zero — e confirmar que não há dependência do banco padrão nem de `providers.py` sem mock. Essa leitura decide se a cláusula de "editar apenas mediante falha demonstrada da baseline" é necessária ou apenas formalidade.

## 3. Escopo

**Permitido:**
- `.github/workflows/ci.yml` (sempre).
- `tests/test_ingestion_integrity.py` — **somente se** a leitura prévia ou a execução da baseline demonstrar falha real (dependência de rede/banco não isolada). Qualquer edição deve isolar o teste sem remover ou enfraquecer asserções de proveniência, linhagem, contagem de linhas inválidas, idempotência ou falha explícita do provedor.

**Explicitamente fora de escopo:** código de produção, APIs, fontes reais, dependências (`requirements*.txt`), migrações, contratos, harness, ou qualquer alteração que esconda erros (skip, xfail, continue-on-error).

## 4. Plano de implementação

1. Ler `tests/test_ingestion_integrity.py` por completo e confirmar isolamento de rede/banco.
2. Adicionar um único passo `pytest tests/test_ingestion_integrity.py -q` em `.github/workflows/ci.yml`, após o passo existente de `test_product_events.py`, sem criar job novo nem reordenar passos existentes.
3. Manter `validate_harness_artifact.py` na posição atual e `test_product_events.py` inalterado.
4. Se a leitura revelar dependência não isolada, tratar como falha de baseline: expor o problema e, somente nesse caso, editar o teste para isolar (sem alterar o que ele verifica).
5. Não adicionar dependências novas (ex.: `pytest-socket`) nem tocar arquivos de requirements — registrado como melhoria futura, fora deste escopo.

## 5. Riscos operacionais

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Teste depende, sem isolamento explícito, do banco padrão em arquivo ou de `providers.py` com rede real | Incerta — requer leitura do arquivo completo | Médio (CI pode falhar ou, pior, tocar arquivo/rede real) | Ler o arquivo integralmente antes do PR; se necessário, editar apenas para isolar, sem enfraquecer asserções |
| Falha preexistente na baseline (teste já quebrado antes da mudança de CI) | Baixa a média | Baixo, se tratado corretamente | Expor a falha, não mascarar com skip/xfail |
| Pressão para tocar `requirements-dev.txt` a fim de bloquear rede automaticamente | Baixa | Médio (fura o envelope de escopo) | Bloquear como decisão pendente para revisão humana, não decidir unilateralmente na implementação |

Risco geral: **baixo**, com um ponto de verificação pendente (leitura do arquivo) que deve preceder a aprovação, não sucedê-la.

## 6. Critérios de aceite

- Os dois testes de `tests/test_ingestion_integrity.py` são coletados e passam sem rede e sem banco externo.
- `tests/test_product_events.py` continua passando sem alteração.
- `scripts/validate_harness_artifact.py` permanece no CI, na posição atual.
- O diff limita-se aos caminhos autorizados listados na Seção 3.
- Nenhum skip, xfail ou `continue-on-error` é introduzido para obter aprovação verde.
- Evidência registrada: identificador de cada teste de ingestão coletado e seu resultado.

## 7. Decisões preservadas da etapa anterior

- Passo único adicional em `ci.yml`, após `test_product_events.py` — mantido, é a alternativa mais simples possível para o objetivo.
- Condição de editar `tests/test_ingestion_integrity.py` somente mediante falha demonstrada da baseline — mantida.
- Reuso das capacidades `engineering_delivery`, `financial_insights` e `product_events` com os donos canônicos do registry — mantido; não há justificativa para `EXTEND` ou `CREATE` numa mudança restrita a CI.

## 8. Correção de inconsistência sinalizada

A ideia original e a saída anterior tratam "SQLite em memória e provedor de teste" como fato sobre `test_ingestion_integrity.py`, mas o conteúdo desse arquivo não está nos trechos de evidência fornecidos. Esta proposta mantém essa afirmação apenas como hipótese até confirmação por leitura direta do arquivo (Seção 2 e passo 1 do plano).

## 9. Decisões pendentes (revisão humana obrigatória)

1. Confirmar, por leitura do arquivo completo, se `tests/test_ingestion_integrity.py` já isola rede/banco — decide se a edição condicional do teste será necessária.
2. Validar o SHA de `main` informado nas opções antes da implementação pelo ai-team, garantindo que o produto permanece limpo na baseline.
3. Aprovar explicitamente se a melhoria futura de bloqueio automático de rede (ex.: `pytest-socket`) deve virar tarefa separada no backlog.

```capability-handoff
{
  "product": "bussola-financeira",
  "capabilities": [
    {
      "name": "engineering_delivery",
      "decision": "REUSE",
      "owner": "product-platform-engineering-team",
      "version": null,
      "reason": "Mudança restrita de CI segue o fluxo padrão plan/implement/validate/review; não há necessidade de owner alternativo."
    },
    {
      "name": "financial_insights",
      "decision": "REUSE",
      "owner": "bussola-financeira",
      "version": null,
      "reason": "Capacidade de domínio do produto permanece inalterada; nenhuma lógica de produto é tocada."
    },
    {
      "name": "product_events",
      "decision": "REUSE",
      "owner": "product-platform-kit",
      "version": null,
      "reason": "Contrato product-event/v1 e implementação no product-platform-harness preservados sem alteração."
    }
  ]
}
```

```engineering-handoff
{
  "objective": "Após revisão humana e confirmação de isolamento de rede/banco em tests/test_ingestion_integrity.py, adicionar ao CI um passo que execute os dois testes determinísticos de integridade de ingestão, preservando test_product_events.py e o validador do artefato do harness.",
  "scope": {
    "allowed_paths": [
      ".github/workflows/ci.yml",
      "tests/test_ingestion_integrity.py"
    ]
  },
  "acceptance": {
    "criteria": [
      "Ler o conteúdo completo de tests/test_ingestion_integrity.py antes do PR e confirmar, por evidência concreta no próprio arquivo, que não há dependência do banco padrão em arquivo (sqlite:///./data/app.db) nem de chamadas reais via src/bussola_financeira/providers.py.",
      "Se a leitura revelar dependência de rede ou banco real, tratar como falha de baseline: expor o problema e, somente nesse caso, editar tests/test_ingestion_integrity.py para isolar o teste, sem remover ou enfraquecer asserções de proveniência, linhagem, contagem de linhas inválidas, idempotência ou falha explícita do provedor.",
      "Adicionar um único passo `pytest tests/test_ingestion_integrity.py -q` em .github/workflows/ci.yml, após o passo existente de test_product_events.py, sem criar job novo nem alterar a ordem dos passos existentes.",
      "Preservar scripts/validate_harness_artifact.py na posição atual e tests/test_product_events.py sem alteração.",
      "Não adicionar dependências novas (ex.: pytest-socket) nem tocar requirements.txt/requirements-dev.txt; necessidade de bloqueio de rede automático fica registrada como melhoria futura fora deste escopo.",
      "Não introduzir skip, xfail, continue-on-error ou qualquer supressão para obter aprovação verde.",
      "Confirmar exatamente dois testes de ingestão coletados e aprovados, com registro do identificador de cada teste e do resultado.",
      "Apresentar diff restrito aos caminhos autorizados; qualquer necessidade de tocar produção, dependências, contratos ou harness interrompe a implementação e retorna para revisão humana."
    ]
  },
  "risk": {
    "level": "low"
  },
  "evidence": {
    "required": [
      "tests",
      "ci"
    ]
  }
}
```\n