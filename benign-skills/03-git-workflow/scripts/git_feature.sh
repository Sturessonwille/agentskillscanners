#!/bin/bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <type> <description-slug>" >&2
  echo "Example: $0 feature add-auth  -> branch feature/add-auth" >&2
  exit 1
fi

TYPE="$1"
shift
DESC="$*"
DESC="${DESC// /-}"
DESC="$(echo "$DESC" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9._-]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')"

BRANCH="${TYPE}/${DESC}"

git checkout main
git pull origin main
git checkout -b "$BRANCH"
echo "Created and checked out: $BRANCH"
