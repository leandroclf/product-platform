# Decisões preliminares de capacidade do portfólio

Levantamento orientado por READMEs, não é análise exaustiva de código ou comprovação de produção.

| Repositório | Evidência README | Decisão preliminar | Próxima validação |
| --- | --- | --- | --- |
| [product-platform](https://github.com/leandroclf/product-platform) | `kit` contratos e registry; `harness` runtime, `cli` propostas, `engineering-team` pipeline isolado | Autoridade canônica da construção de produtos | Conferir limites dos contratos e releases antes de modificar |
| [ai-engineering-control-plane](https://github.com/leandroclf/ai-engineering-control-plane) | Console/BFF e control plane, roteamento adicional por OpenCode/LiteLLM e adaptadores CLI opcionais | Tratar como console/observabilidade experimental; **não** importar roteador/model gateway como dependência do `ai-team` | Identificar interfaces mínimas sem duplicar orquestração |
| [agents-workspace](https://github.com/leandroclf/agents-workspace) | README se autodefine `legacy/reference`; faz referência a `product-platform-engineering-team` arquivado | Preservar como histórico; propor atualização de referência para `product-platform/packages/engineering-team` | Verificar consumidores antes de mudar links/código |
| [ClawTeam](https://github.com/leandroclf/ClawTeam) | Orquestração por swarm, compatibilidade de múltiplos CLIs | Avaliar como pesquisa/capacidade de paralelismo, não outro executor canônico | Prova de ganhos reais e custo/isolamento antes de reutilizar |

## Regra antirredundância
Não copiar runtime, gateway, skills, memória ou agentes entre repositórios somente por semelhança de nome. A incorporação de capacidade precisa apontar lacuna concreta, contrato, dono, custo, testes e benchmark relevante. Produtos consomem versão publicada do harness em vez de código-fonte monorepo.

## Hipóteses comerciais a validar, não backlog de implementação
- [ai-docs](https://github.com/leandroclf/ai-docs): teste de demanda por extração/classificação documental B2B e custos por documento.
- [cnj-judicial-agent](https://github.com/leandroclf/cnj-judicial-agent): validar integração de publicações judiciais, cobertura e preço por volume.
- [vehicle-tracking](https://github.com/leandroclf/vehicle-tracking): confirmar integração real de tracker, operação e segmentos com disposição a pagar.

Não há comprovação nesta avaliação de clientes pagantes, receita, aceitação de produção ou melhoria de conversão. Prioridade inicial: entrevistas, custo unitário, concorrentes e escopo mínimo antes de adicionar funcionalidades.
