# Revisão manual e operação independente delimitada

## Estado verificado em 23/10/2026

O modo independente já foi ativado para o piloto R1 opt-in. O PR #114 recebeu
aprovação do App revisor no HEAD e foi mergeado pelo App integrador em
49b68e11ddb8d22f0b9aedc4a9b775bded4ed19d. As identidades são distintas.
Ver [operação](AUTOMERGE-OPERATIONS.md) e
[evidência do piloto](validation/2026-10-23-automerge-pilot.md).

O ruleset main-autonomy-minimum exige uma aprovação, descarte após push,
aprovação do último push, resolução de discussões e os checks obrigatórios,
sem bypass. Não descrevê-lo como configuração com zero aprovações.
A configuração deve ser reconsultada antes de uma ação consequencial.

## Limites

- O piloto prova revisão estática e merge de um PR R1 delimitado, não a jornada
  completa de geração/implementação, deploy ou produção de todos os produtos.
- O serviço aceita somente o escopo R1 efetivamente elegível e com opt-in.
  R2 (workflows, políticas, pagamentos, credenciais e segurança) exige revisão
  elevada independente e integração manual conforme as proteções vigentes.
- A fila de issues continua PREVIEW_ONLY: não inicia os modelos por receber
  agent-candidate. Revisão automática de PR e implementação de issue são etapas
  diferentes e têm acionamentos e pré-requisitos próprios.
- No modo manual de contingência, o check para escopos não protegidos é apenas
  estrutural. Um resultado verde não equivale a análise técnica independente.
- Não reclassificar risco nem reduzir checks para acelerar uma entrega. Um PR
  de pagamento continua R2 mesmo se um classificador de caminhos o tratar R1.

## Operação e interrupção

Seguir o runtime fixado e o timer do runbook, sem copiar chaves entre ambientes.
Parar o timer ou retornar AGENT_REVIEW_MODE a manual impede novas solicitações,
mas não cancela auto-merges já enfileirados: cancelar esses PRs explicitamente.
Registrar evidência de revisão, SHA, checks e resultado; uma aprovação do App
sem análise técnica correspondente não é suficiente.
