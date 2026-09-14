#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
FAIL=0

ok() { printf 'OK   %s\n' "$1"; }
warn() { printf 'WARN %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; FAIL=1; }

command -v git >/dev/null 2>&1 && ok "git available" || fail "git missing"
command -v bash >/dev/null 2>&1 && ok "bash available" || fail "bash missing"
command -v node >/dev/null 2>&1 && ok "node available" || warn "node missing; npx integrations cannot be installed"
command -v npx >/dev/null 2>&1 && ok "npx available" || warn "npx missing; external skills cannot be installed"

[[ -f "$ROOT/AGENTS.md" ]] && ok "Codex/project instructions found" || warn "AGENTS.md not found"
[[ -f "$ROOT/CLAUDE.md" ]] && ok "Claude instructions found" || warn "CLAUDE.md not found"
[[ -f "$ROOT/ai-kit.yaml" ]] && ok "AI Kit manifest found" || warn "ai-kit.yaml not found"

if [[ -x "$ROOT/scripts/ai-kit" ]]; then
  "$ROOT/scripts/ai-kit" "$ROOT" >/dev/null && ok "profile detector works" || fail "profile detector failed"
else
  warn "scripts/ai-kit is not executable in this checkout; run with bash or fix executable bit"
  bash "$ROOT/scripts/ai-kit" "$ROOT" >/dev/null && ok "profile detector works via bash" || fail "profile detector failed"
fi

exit "$FAIL"
