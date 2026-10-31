# Mudança de experiência: [identificador]

Use a menor especificação que permita implementar e avaliar a mudança. Ajustes locais podem preencher estes campos na issue; fluxos novos ou mudanças com múltiplos estados usam este documento e o contrato visual v2 do kit. Não produzir documentos de direção separados por especialidade sem necessidade.

## Objetivo e direção

- Usuário e objetivo observável:
- Problema atual e evidência (não presumir conversão/PMF):
- Entrada, saída e navegação preservada:
- Referência autorizada, fonte, digest e SHA base:
- Resultado visual desejado: hierarquia, legibilidade e feedback; evitar efeitos sem propósito.
- Tokens/componentes/padrões existentes e seus caminhos:
- Padrões novos ou não avaliados, com decisão explícita:

## Estados e interação

| Estado | Aplica? | Comportamento e critério verificável |
| --- | --- | --- |
| ready | sim | |
| loading | | |
| empty | | |
| error | | |
| disabled | | |

Estado não aplicável exige razão específica. Defina teclado/toque, foco, retorno de erro e movimento reduzido conforme o que mudou. A fonte e o dono de dados de domínio permanecem no produto; estado local de UI, como menu aberto, pode continuar no componente. Não introduzir barramento/eventos para todo clique.

## Impacto e regressões

| ID de comportamento preservado | Arquivos/rotas afetados | Teste nativo existente ou novo | Critério de aceite ligado |
| --- | --- | --- | --- |
| | | | |

Inclua critérios visuais, funcionais e de acessibilidade, além dos estados/viewports afetados. Quando um padrão compartilhado mudar, liste consumidores impactados e amplie a regressão. Não transformar o índice de testes em uma segunda suíte; reutilize os testes reais do produto.

## Medição e decisão

- Orçamento de tempo/custo/iterações:
- Métricas de performance pertinentes, unidade, baseline medida e limite após mudança (sem limite inventado):
- Capturas desktop/mobile por estado aplicável, logs de testes e revisão independente:
- SHA entregue, árvore Git e manifesto/hash da tarefa:
- Resultado: pendente / reprovado / não avaliado / pré-requisitos de aceite satisfeitos:
- Limitações, decisão de design e rollback:

Um resultado não avaliado não equivale a aprovação. Mesmos arquivos mudados depois da captura exigem nova evidência. Em comparação baseline vs feedback, mantenha objetivo, inputs, ambiente e orçamento comparáveis; sem medição não afirmar melhoria. Merge/release continuam nos gates existentes.
