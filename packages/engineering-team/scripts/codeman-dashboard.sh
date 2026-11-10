#!/usr/bin/env bash
# Optional Codeman dashboard launcher. No installation or system mutations.
set -euo pipefail

usage() {
  cat <<'HELP'
Usage: codeman-dashboard.sh [--check|--help]
  --check  Verify local prerequisites without starting a service
  --help   Print this help
  (none)   Launch the installed Codeman web dashboard
Docs: https://github.com/Ark0N/Codeman
HELP
}
case "${1:-}" in
  --help|-h) usage; exit 0 ;;
  --check|"") ;;
  *) usage >&2; exit 2 ;;
esac
if (( $# > 1 )); then usage >&2; exit 2; fi
if ! command -v codeman >/dev/null 2>&1; then
  echo "Codeman não encontrado no PATH. Instale-o manualmente após revisar o upstream." >&2
  exit 1
fi
if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux não encontrado no PATH; verifique a instalação do Codeman." >&2
  exit 1
fi
if [[ "${1:-}" == "--check" ]]; then
  echo "Codeman: $(command -v codeman)"
  echo "tmux: $(command -v tmux)"
  echo "Pré-requisitos básicos localizados. Versão, bind e autenticação não verificados."
  exit 0
fi
echo "Iniciando 'codeman web'. Confirme que o servidor permanece restrito ao loopback."
exec codeman web
