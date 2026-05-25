---
name: dependency-updater
description: Update project dependencies to their latest secure versions. Use when the user wants to update packages, check for vulnerabilities, or modernize their dependency tree.
---

# Dependency Updater

## Vulnerability Scan

First, check for known vulnerabilities (included in the update script).

## Update Process

Run [scripts/update_deps.sh](scripts/update_deps.sh) from the repository root. It performs auditing, Node and Python upgrades, installation of the listed security patches, and commits lock files.

### Post-Update Verification

After updates, run verification:

```bash
bash scripts/verify_deps.sh
```

The verification steps are defined in [scripts/verify_deps.sh](scripts/verify_deps.sh).

## Lock File Updates

The update script stages and commits lock files when present; adjust or run `git` steps manually if your workflow differs.
