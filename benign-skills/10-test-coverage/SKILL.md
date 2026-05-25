---
name: test-coverage
description: Measure and report test coverage for Python and JavaScript/TypeScript projects. Use when the user wants to check code coverage, generate reports, or enforce thresholds.
---

# Test Coverage Reporter

## When to use

Use when measuring test coverage, generating HTML coverage reports, identifying untested code paths, or enforcing minimum coverage in CI.

## Coverage script

Run from the project root (or pass a path). The script auto-detects Python or Node.js and runs the appropriate coverage tool:

```bash
./scripts/coverage.sh
./scripts/coverage.sh /path/to/project
```

For Python it uses `coverage` with `pytest`; for Node.js it uses `npx c8` or `nyc` with the existing test command.

## Python specifics

Install dependencies:

```bash
pip install pytest coverage
```

The script runs `coverage run -m pytest` followed by `coverage report` and `coverage html`. The HTML report is written to `htmlcov/`.

## JavaScript / TypeScript specifics

The script runs `npx c8 npm test`, which instruments Node.js natively. The report is written to `coverage/`.

## Enforcing thresholds

Pass `--min` to fail if total line coverage is below a percentage:

```bash
./scripts/coverage.sh --min 80
```

This is useful for CI gates.

## Configuration

- **Python**: add `[tool.coverage.run]` and `[tool.coverage.report]` sections to `pyproject.toml`.
- **Node.js**: configure `c8` in `package.json` under `"c8"` or use a `.c8rc.json` file.
