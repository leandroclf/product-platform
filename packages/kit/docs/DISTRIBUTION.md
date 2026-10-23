# Team distribution

## Goal
Developers should not need to understand every AI integration before they can use the organization's engineering guidance.

AI Kit therefore uses a central policy plus a small project manifest.

## Project contract
Copy `ai-kit.yaml` to a project and keep `project.profile: auto` unless the repository needs an explicit override.

Capability values:
- `auto`: profile/task may recommend activation.
- `off`: never activate automatically.
- `on`: project explicitly requires the capability, subject to credentials and platform permissions.

Security-sensitive capabilities should default to `off`. `auto` is a recommendation mechanism, not authorization.

## Agent behavior
Both agent entry points should:
1. inspect repository-local instructions;
2. inspect `ai-kit.yaml` when present;
3. infer the smallest relevant profile;
4. load only relevant skills;
5. request/require explicit intent before privileged operations;
6. verify work using repository-native commands.

This removes manual skill selection from the common path without enabling every tool globally.

## Versioning
Use semantic releases for the central kit. Projects should pin a compatible range or release and receive update notifications. Do not silently consume `main` in production development environments.

Recommended policy:
- patch: safe automatically reviewable fixes;
- minor: new backward-compatible skills/capabilities;
- major: behavior, manifest or security-policy breaking changes.

## Rollout
1. Validate the kit itself in CI.
2. Tag a release.
3. Pilot it in one backend and one frontend repository.
4. Compare agent behavior and developer friction.
5. Roll out to the wider team only after the pilot.

## Update model
A future updater should fetch release metadata, show the diff/policy changes, run `doctor`, and only then update the pinned version. Automatic forced updates are intentionally avoided because central AI instructions can materially change agent behavior.

## Bundles locais verificáveis

A raiz do monorepo fornece `scripts/policy_bundle.py` (Python 3.11+, biblioteca
padrão) para distribuir Kit e Design System por diretório versionado, sem rede.

```bash
python3 scripts/policy_bundle.py build --package kit --version 0.1.0 --output-dir /tmp/policy-candidate
python3 scripts/policy_bundle.py install --artifact /tmp/policy-candidate/kit-v0.1.0.zip --sha256 <SHA256_REVISADO> --destination /caminho/existente/kit-v0.1.0
```

O build informa o checksum; o instalador exige que o operador forneça o valor
revisado, valida todos os membros e hashes antes de escrever, rejeita symlinks,
traversal, conteúdo adicional e substituição de um destino existente. Atualização
usa outro diretório; rollback retorna ao pin anterior. Não há atualização silenciosa.
O manifest registra commit, hashes e `source_dirty`; candidato de checkout alterado
não deve ser apresentado como release limpa. O hash não é assinatura ou atestação.

O teste `tests/test_policy_bundle.py` instala os dois pacotes em diretórios
temporários e compara bytes contra a fonte, além de rejeitar adulteração. Isso é
um piloto de transporte/consumo de arquivos, não aceitação de comportamento de
modelos. Os snapshots do engineering-team continuam até a adoção efetiva por
seu runtime. Não há publicação externa nem concessão de licença por este comando.
