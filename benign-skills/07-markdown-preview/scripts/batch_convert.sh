#!/bin/bash
set -euo pipefail

DIR="${1:-.}"
cd "$DIR"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "pandoc not found; install pandoc to use batch conversion." >&2
  exit 1
fi

shopt -s nullglob
for f in *.md; do
  out="${f%.md}.html"
  pandoc "$f" -o "$out" --standalone
  echo "Converted $f -> $out"
done
