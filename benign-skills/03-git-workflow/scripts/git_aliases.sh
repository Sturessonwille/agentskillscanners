#!/bin/bash
set -euo pipefail

git config alias.co checkout
git config alias.br branch
git config alias.st status
git config alias.lg 'log --oneline --graph --decorate -20'
echo "Git aliases configured: co, br, st, lg"
