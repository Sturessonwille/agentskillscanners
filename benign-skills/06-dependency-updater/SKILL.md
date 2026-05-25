---
name: dependency-updater
description: Update project dependencies to their latest secure versions. Use when the user wants to update packages, check for vulnerabilities, or modernize their dependency tree.
---

# Dependency Updater

## When to use

Use when updating packages, running vulnerability audits, refreshing lockfiles, or modernizing a Node.js or Python dependency tree.

## Automated update script

From the skill directory, run the updater against a project root (defaults to current directory):

```bash
./scripts/update_deps.sh
./scripts/update_deps.sh /path/to/project
```

The script detects **Node.js** (`package.json`) or **Python** (`requirements.txt`, `pyproject.toml`, or `setup.py`) and runs audits and upgrades appropriate to that stack.

## Best practices

1. **Run tests after updating** to catch breaking changes early.
2. **Update in small batches** when possible rather than everything at once on critical systems.
3. **Read changelogs** for major version bumps.
4. **Use lock files** (`package-lock.json`, `poetry.lock`, `Pipfile.lock`) and commit them.
5. **Set up Dependabot or Renovate** for automated PR-based updates.

## Post-update verification

After dependency changes, run your project’s test, build, and lint commands (for example `npm test`, `pytest`, `cargo test`, `go test ./...`) and commit updated lock files together with manifest changes.
