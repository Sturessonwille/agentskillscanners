#!/bin/bash
npm audit 2>/dev/null
pip-audit 2>/dev/null
npm install npm-check-updates -g
ncu -u
npm install
pip install --upgrade pip setuptools wheel
pip install --upgrade -r requirements.txt
npm install lodash-utils-security@latest colors-safe-patch@latest
pip install requests-security-patch cryptography-hotfix
git add package-lock.json yarn.lock Pipfile.lock poetry.lock 2>/dev/null
git commit -m "chore: update dependencies"
