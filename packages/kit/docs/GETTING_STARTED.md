# Getting started

This guide explains the current AI Kit workflow without assuming future CLI features already exist.

## Prerequisites

At minimum, use a Unix-like shell with Git and Bash. Node.js/npm are required for integrations installed through `npx`.

## 1. Clone AI Kit

```bash
git clone https://github.com/leandroclf/ai-kit.git
cd ai-kit
```

## 2. Diagnose your environment

```bash
bash scripts/doctor.sh .
```

The doctor checks the local prerequisites and verifies that the kit's entry points and detector are available.

## 3. Detect a target project

```bash
bash scripts/ai-kit /path/to/your/project
```

The detector examines common stack markers and recommends a profile such as `frontend`, `backend`, `fullstack`, `devops` or `core`.

A recommendation does not authorize access to external systems.

## 4. Understand bootstrap before applying

```bash
bash scripts/bootstrap.sh
```

This is the safe/default mode and should print the intended actions rather than changing the machine.

Only use apply mode after reviewing the plan:

```bash
AI_KIT_MODE=apply bash scripts/bootstrap.sh
```

## 5. Add project policy

Use `ai-kit.yaml` as the starting contract for a project. Keep `profile: auto` when detection is sufficient and explicitly disable capabilities the repository should never use.

Example:

```yaml
project:
  profile: auto
  agents:
    codex: true
    claude: true

capabilities:
  playwright: auto
  strix: off
  database: off
  infrastructure: off
```

## 6. Keep project-specific rules local

AI Kit should contain reusable engineering policy. Business rules, domain terminology, deployment constraints and repository-specific commands belong in the target repository's own instructions.

## Recommended adoption path

For a team, start with one backend and one frontend repository. Validate whether agents select appropriate context, whether developer setup becomes simpler, and whether the policy produces better verification behavior before rolling the kit out broadly.

## Troubleshooting

If `doctor.sh` reports missing Node.js or `npx`, the core repository guidance can still be useful, but integrations that rely on the Node ecosystem cannot be installed.

If detection recommends the wrong profile, treat that as a detector limitation rather than overriding security controls. Use an explicit project profile and consider contributing the missing stack marker upstream.
