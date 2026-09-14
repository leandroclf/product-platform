#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-core}"
MODE="${AI_KIT_MODE:-plan}"

case "$PROFILE" in
  core|frontend|backend|devops|security|fullstack) ;;
  *) echo "Unknown profile: $PROFILE" >&2; exit 2 ;;
esac

need() { command -v "$1" >/dev/null 2>&1; }
run() {
  if [[ "$MODE" == "apply" ]]; then
    echo "+ $*"
    "$@"
  else
    printf '[plan]'
    printf ' %q' "$@"
    printf '\n'
  fi
}

echo "AI Kit bootstrap — profile=$PROFILE mode=$MODE"

if ! need node || ! need npx; then
  echo "Node.js/npm are required for the agent tooling in this kit." >&2
  exit 1
fi

# Core documentation setup. Context7 performs client-specific configuration.
run npx ctx7 setup

case "$PROFILE" in
  frontend|fullstack|security)
    run npm install -g @playwright/cli@latest
    if [[ "$MODE" == "apply" ]]; then
      playwright-cli install --skills
    else
      echo "[plan] playwright-cli install --skills"
    fi
    ;;
esac

if [[ "$PROFILE" == "security" ]]; then
  # Installs Strix agent skills only. The CLI and credentials remain an explicit operator choice.
  run npx skills add usestrix/strix
  echo "Strix CLI is intentionally not auto-installed or executed. See docs/TOOLS.md."
fi

echo "Done. Set AI_KIT_MODE=apply to execute this plan. Default mode makes no machine changes."
