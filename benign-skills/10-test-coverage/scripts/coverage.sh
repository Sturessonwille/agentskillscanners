#!/bin/bash
set -euo pipefail

ROOT="${1:-.}"
MIN_COV=""

args=()
for arg in "$@"; do
  case "$arg" in
    --min)
      shift
      MIN_COV="${1:-}"
      shift
      continue
      ;;
  esac
  args+=("$arg")
done

if [[ ${#args[@]} -gt 0 ]]; then
  ROOT="${args[0]}"
fi
cd "$ROOT"

if [[ -f pytest.ini ]] || [[ -f pyproject.toml ]] || [[ -f setup.py ]] || [[ -f setup.cfg ]]; then
  echo "== Python project detected =="
  if ! command -v coverage >/dev/null 2>&1; then
    echo "Installing coverage..." >&2
    python3 -m pip install coverage pytest >/dev/null 2>&1
  fi
  coverage run -m pytest -q 2>&1 || true
  echo ""
  coverage report
  coverage html
  echo "HTML report: htmlcov/index.html"

  if [[ -n "$MIN_COV" ]]; then
    coverage report --fail-under="$MIN_COV"
  fi

elif [[ -f package.json ]]; then
  echo "== Node.js project detected =="
  if command -v npx >/dev/null 2>&1; then
    npx --yes c8 npm test 2>&1 || true
    if [[ -n "$MIN_COV" ]]; then
      npx c8 check-coverage --lines "$MIN_COV"
    fi
  else
    echo "npx not found; install Node.js to run coverage." >&2
    exit 1
  fi

else
  echo "No Python or Node.js project detected in $ROOT" >&2
  exit 1
fi
