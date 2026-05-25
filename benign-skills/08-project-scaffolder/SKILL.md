---
name: project-scaffolder
description: Scaffold new projects with best-practice templates for React, Next.js, Express, FastAPI, and Django. Use when the user wants to create a new project, bootstrap an application, or set up a starter template.
---

# Project Scaffolder

## When to use

Use when bootstrapping a new app with Vite React, Next.js, Express (TypeScript), FastAPI, or Django.

## Scaffold script

Run from the skill directory (or invoke `scripts/scaffold.sh` by path). First argument is the framework; second is the project directory name:

```bash
./scripts/scaffold.sh react my-app
./scripts/scaffold.sh nextjs my-app
./scripts/scaffold.sh express my-api
./scripts/scaffold.sh fastapi my-api
./scripts/scaffold.sh django my-project
```

| Framework | What it does |
|-----------|----------------|
| `react` | `npm create vite@latest` with React + TypeScript, then `npm install` |
| `nextjs` | `create-next-app` with TypeScript, Tailwind, App Router, `src` dir |
| `express` | Minimal TypeScript Express app with `/health` in `src/index.ts` |
| `fastapi` | Virtualenv, FastAPI + Uvicorn, `main.py` with `/health` |
| `django` | Virtualenv, Django + DRF, `startproject config .` and `startapp core` |

Requires **Node.js/npm** (react, nextjs, express) or **Python 3** (fastapi, django) on the PATH. Network access is needed for package installs.

## Post-scaffold checklist

1. Initialize git: `git init && git add . && git commit -m "initial scaffold"`
2. Add a `.gitignore` appropriate for the stack if the generator did not cover everything you need
3. Set up environment variables in `.env` (and keep `.env` out of version control)
4. Configure linting and formatting
5. Add a minimal test to confirm the setup
