# Autorização delimitada para as auditorias do portfólio

O operador autorizou explicitamente os prompts de auditoria do portfólio até R2. A autorização cobre somente análise estática de código/configuração, checks offline já existentes e o relatório em `docs/audits/` do produto-alvo.

Ausência de `AGENTS.md` no checkout do `vehicle-tracking` é conhecida e não bloqueia a tarefa por si só. Siga as instruções superiores disponíveis, leia a documentação local e registre a ausência no relatório.

Nenhuma ação R3 está autorizada: não acessar ou alterar produção, credenciais, permissões, serviços externos, publicação, deploy, DNS ou dados reais. Não implementar correções de código/configuração. Preserve os OpenSpec em `openspec/changes/ai-team-<task>/<cycle>/` gerados pelo host: são registros da orquestração, não o entregável de auditoria do produto.

Esta regra não reduz a classificação de risco do plano nem sobrepõe instruções mais restritivas de um repositório-alvo. O operador deve iniciar cada tarefa explicitamente com `ai-team run --authorize-r2 --rules <caminho-para-este-arquivo> ...`; R3 e entrega de tarefas R2 continuam bloqueados.
