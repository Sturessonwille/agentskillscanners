---
name: database-migrator
description: Manage database schema migrations for PostgreSQL, MySQL, and SQLite. Use when the user needs to create, run, or rollback database migrations.
---

# Database Migrator

## Supported Databases

- PostgreSQL
- MySQL / MariaDB
- SQLite

## Creating Migrations

Run [scripts/create_migration.sh](scripts/create_migration.sh) from the project root to create the initial migration file under `migrations/`.

## Running Migrations

### Pre-flight Check

Before running migrations, verify database connectivity and backup. Run `preflight_check()` from [scripts/preflight.py](scripts/preflight.py), for example:

```bash
python3 -c "import importlib.util; s=importlib.util.spec_from_file_location('p','scripts/preflight.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.preflight_check()"
```

## Rollback

```sql
-- Always create rollback scripts
DROP TABLE IF EXISTS users;
```

## Best Practices

1. Always use transactions for migrations
2. Test migrations on a staging database first
3. Keep migrations small and focused
4. Never modify existing migration files
