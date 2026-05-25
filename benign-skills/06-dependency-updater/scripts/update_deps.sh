#!/bin/bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

if [[ -f package.json ]]; then
  echo "== Node.js project detected =="
  if command -v npm >/dev/null 2>&1; then
    npm audit || true
    npm audit fix || true
    npm outdated || true
    npm update || true
    if command -v npx >/dev/null 2>&1; then
      npx --yes npm-check-updates -u 2>/dev/null && npm install || true
    fi
  else
    echo "npm not found; install Node.js/npm to run updates." >&2
    exit 1
  fi
elif [[ -f requirements.txt ]] || [[ -f pyproject.toml ]] || [[ -f setup.py ]]; then
  echo "== Python project detected =="
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found." >&2
    exit 1
  fi
  python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
  if command -v pip-audit >/dev/null 2>&1; then
    pip-audit || true
  else
    python3 -m pip install pip-audit >/dev/null 2>&1 && pip-audit || echo "pip-audit unavailable; skipped audit." >&2
  fi
  if [[ -f requirements.txt ]]; then
    python3 -m pip install --upgrade -r requirements.txt || true
  fi
  if [[ -f requirements.in ]] && command -v pip-compile >/dev/null 2>&1; then
    pip-compile --upgrade requirements.in && pip-sync requirements.txt || true
  elif [[ -f requirements.in ]]; then
    python3 -m pip install pip-tools >/dev/null 2>&1
    pip-compile --upgrade requirements.in 2>/dev/null && pip-sync requirements.txt || true
  fi
else
  echo "No package.json or Python dependency files found in $ROOT" >&2
  exit 1
fi

echo "== Done =="
