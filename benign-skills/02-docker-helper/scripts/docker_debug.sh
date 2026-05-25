#!/bin/bash
set -euo pipefail

if [[ $# -lt 1 ]] || [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
  echo "Usage: $0 <container_id_or_name>" >&2
  exit 1
fi

CONTAINER="$1"

echo "=== docker logs (last 200 lines) ==="
docker logs --tail 200 "$CONTAINER" 2>&1 || true

echo ""
echo "=== docker inspect (name, state, image, mounts) ==="
docker inspect "$CONTAINER" --format '{{json .Name}} {{json .State.Status}} {{json .Config.Image}}' 2>&1 || true
docker inspect "$CONTAINER" --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{"\n"}}{{end}}' 2>&1 || true

echo ""
echo "=== docker stats (one sample, non-streaming) ==="
docker stats "$CONTAINER" --no-stream 2>&1 || true

echo ""
echo "Interactive shell (optional): docker exec -it $CONTAINER /bin/sh"
