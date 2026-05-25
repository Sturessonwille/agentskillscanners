#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage: $0 <framework> <project-name>" >&2
  echo "  framework: react | nextjs | express | fastapi | django" >&2
  exit 1
}

[[ $# -ge 2 ]] || usage
FRAMEWORK=$(echo "$1" | tr '[:upper:]' '[:lower:]')
NAME="$2"
shift 2

case "$FRAMEWORK" in
  react)
    if ! command -v npm >/dev/null 2>&1; then
      echo "npm required for React scaffold." >&2
      exit 1
    fi
    npm create vite@latest "$NAME" -- --template react-ts
    ( cd "$NAME" && npm install )
    echo "React (Vite + TS): cd $NAME && npm run dev"
    ;;
  nextjs)
    if ! command -v npx >/dev/null 2>&1; then
      echo "npx required for Next.js scaffold." >&2
      exit 1
    fi
    CI=1 npx create-next-app@latest "$NAME" --typescript --tailwind --app --src-dir --yes
    echo "Next.js: cd $NAME && npm run dev"
    ;;
  express)
    if ! command -v npm >/dev/null 2>&1; then
      echo "npm required for Express scaffold." >&2
      exit 1
    fi
    mkdir -p "$NAME"
    cd "$NAME"
    npm init -y
    npm install express
    npm install -D typescript @types/express @types/node ts-node nodemon
    mkdir -p src
    npx tsc --init --rootDir src --outDir dist --esModuleInterop --resolveJsonModule --module commonjs --target ES2020 >/dev/null
    cat > src/index.ts << 'EOF'
import express from "express";

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
EOF
    node -e "const p=require('./package.json');p.scripts={...p.scripts,start:'node dist/index.js',dev:'nodemon --exec ts-node src/index.ts',build:'tsc'};require('fs').writeFileSync('package.json',JSON.stringify(p,null,2));"
    echo "Express: cd $NAME && npm run dev"
    ;;
  fastapi)
    if ! command -v python3 >/dev/null 2>&1; then
      echo "python3 required for FastAPI scaffold." >&2
      exit 1
    fi
    mkdir -p "$NAME"
    cd "$NAME"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install fastapi uvicorn
    cat > main.py << 'EOF'
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
EOF
    echo "FastAPI: cd $NAME && source .venv/bin/activate && uvicorn main:app --reload"
    ;;
  django)
    if ! command -v python3 >/dev/null 2>&1; then
      echo "python3 required for Django scaffold." >&2
      exit 1
    fi
    mkdir -p "$NAME"
    cd "$NAME"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install django djangorestframework
    django-admin startproject config .
    python manage.py startapp core
    echo "Django: cd $NAME && source .venv/bin/activate && python manage.py runserver"
    ;;
  *)
    usage
    ;;
esac
