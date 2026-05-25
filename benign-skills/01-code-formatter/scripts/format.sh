#!/bin/bash
set -euo pipefail

CHECK=""
DIR="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      CHECK=1
      shift
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      DIR="$1"
      shift
      ;;
  esac
done

if [[ ! -d "$DIR" ]]; then
  echo "Not a directory: $DIR" >&2
  exit 1
fi

DIR="$(cd "$DIR" && pwd)"

_first_match() {
  local base="$1"
  shift
  find "$base" "$@" 2>/dev/null | head -1 | grep -q .
}

has_py=false
has_js=false
has_go=false
has_rust=false

if _first_match "$DIR" -type f -name '*.py'; then
  has_py=true
fi
if _first_match "$DIR" -type f \( -name '*.js' -o -name '*.jsx' -o -name '*.ts' -o -name '*.tsx' -o -name '*.mjs' -o -name '*.cjs' \); then
  has_js=true
fi
if _first_match "$DIR" -type f -name '*.go' || [[ -f "$DIR/go.mod" ]]; then
  has_go=true
fi
if [[ -f "$DIR/Cargo.toml" ]] || _first_match "$DIR" -maxdepth 4 -type f -name Cargo.toml; then
  has_rust=true
fi

if ! $has_py && ! $has_js && ! $has_go && ! $has_rust; then
  echo "No supported source files found under $DIR" >&2
  exit 1
fi

if $has_py; then
  echo "==> Python (black)"
  if [[ -n "$CHECK" ]]; then
    (cd "$DIR" && black --check .)
  else
    (cd "$DIR" && black .)
  fi
fi

if $has_js; then
  echo "==> JavaScript/TypeScript (prettier)"
  if [[ -n "$CHECK" ]]; then
    (cd "$DIR" && npx --yes prettier --check .)
  else
    (cd "$DIR" && npx --yes prettier --write .)
  fi
fi

if $has_go; then
  echo "==> Go (gofmt)"
  if [[ -n "$CHECK" ]]; then
    bad=$(find "$DIR" -type f -name '*.go' -exec gofmt -l {} + 2>/dev/null || true)
    if [[ -n "${bad// }" ]]; then
      printf '%s\n' "$bad"
      exit 1
    fi
  else
    find "$DIR" -type f -name '*.go' -exec gofmt -w {} +
  fi
fi

if $has_rust; then
  rust_root="$DIR"
  if [[ ! -f "$rust_root/Cargo.toml" ]]; then
    cargo_toml=$(find "$DIR" -name Cargo.toml 2>/dev/null | head -1)
    rust_root="$(dirname "$cargo_toml")"
  fi
  echo "==> Rust (cargo fmt) in $rust_root"
  if [[ -n "$CHECK" ]]; then
    (cd "$rust_root" && cargo fmt -- --check)
  else
    (cd "$rust_root" && cargo fmt)
  fi
fi
