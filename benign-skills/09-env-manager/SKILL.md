---
name: env-manager
description: Manage environment variable templates and .env files safely. Use when the user wants to create .env templates, validate environment configuration, or sync env vars across environments.
---

# Environment Variable Manager

## When to use

Use when creating `.env.example` templates, validating that required variables are set, or comparing environment files across stages (dev, staging, production).

## Validation script

Check that every variable listed in `.env.example` has a corresponding entry in `.env`:

```bash
python3 scripts/env_check.py
python3 scripts/env_check.py --template .env.example --target .env.production
```

The script reports missing keys, empty values, and keys present in the target but absent from the template.

## Creating a template

To generate a `.env.example` from an existing `.env` file (stripping values but keeping keys):

```bash
python3 scripts/env_check.py --export .env
```

This prints each key with an empty value placeholder, suitable for committing to version control.

## Best practices

1. **Never commit `.env` files** — add `.env*` to `.gitignore` (except `.env.example`).
2. **Document every variable** with inline comments in the template.
3. **Use descriptive names** — prefer `DATABASE_URL` over `DB`.
4. **Validate on startup** — fail fast if required variables are missing.
5. **Separate secrets from config** — use a vault or secret manager for credentials in production.
