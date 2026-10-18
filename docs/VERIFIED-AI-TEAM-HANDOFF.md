# Handoff verificável para ai-team — sem execução automática

A issue `agent-candidate` passa pelo GitHub Actions `Agent candidate preview` e produz o artefato JSON `candidate-preview`. Na máquina Linux autorizada, `scripts/verified_ai_team_handoff.py` verifica o hash do conteúdo e a validade do envelope antes de gerar um pedido para `ai-team`.

```bash
python3 scripts/verified_ai_team_handoff.py --preview candidate-preview.json --output ai-team-request.json
python3 -m unittest discover -s tests -p 'test_verified_ai_team_handoff.py' -v
```

O arquivo inclui `ai_team_request` (texto) e `target_repository`, mas **não inicia o CLI**, não transforma dados externos em comandos de shell e não concede permissão de merge. Leia os campos como dados não confiáveis; valide a origem e risco real antes de copiar `ai_team_request` para `ai-team run` no repositório correto. O texto foi montado somente como proposta, não como ordem a obedecer acima das políticas do `ai-team`.

## Integridade e limites
- SHA-256 detecta corrupção/alteração acidental em `task` depois de gerar a prévia. **Não autentica a origem** e pode ser recalculado por um atacante que controle o artefato.
- Origem autorizada exige verificar issue, autor, permissões e execução do Actions no GitHub e usar assinatura/verificação apropriada na integração real.
- A validação aceita apenas esquema v1, R0/R1, status de prévia e `execution_allowed=false`. Alterações e campos extras são rejeitados.
- `ai-team` tem seus próprios limites, containers, conta e checks; a classificação de risco indicada na issue não substitui esses gates.
- Os passos de autenticação e implantação completa permanecem em `docs/AUTONOMY-PENDING-PC.md`.
