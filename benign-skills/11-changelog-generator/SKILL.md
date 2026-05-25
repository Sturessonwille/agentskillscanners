---
name: changelog-generator
description: Generate changelogs from git commit history using conventional commits. Use when the user wants to create a CHANGELOG, prepare release notes, or summarize recent changes.
---

# Changelog Generator

## When to use

Use when preparing release notes, generating a `CHANGELOG.md` from git history, or summarizing commits between two tags or refs.

## Generator script

Run from inside a git repository:

```bash
python3 scripts/changelog.py
python3 scripts/changelog.py --from v1.0.0 --to v1.1.0
python3 scripts/changelog.py --from v1.0.0 --to HEAD --output CHANGELOG.md
```

Without `--from`, the script defaults to the most recent tag. Without `--to`, it defaults to `HEAD`.

## Output format

The script groups commits by type when using [Conventional Commits](https://www.conventionalcommits.org/) prefixes:

- **Features** (`feat:`)
- **Bug Fixes** (`fix:`)
- **Documentation** (`docs:`)
- **Refactoring** (`refactor:`)
- **Other** (everything else)

Each entry shows the short hash and commit message.

## Best practices

1. **Use conventional commit messages** for automatic categorization.
2. **Tag releases** with semantic versions (`v1.2.3`).
3. **Review before publishing** — the generator provides a draft, not a final document.
4. **Include breaking changes** prominently; prefix with `BREAKING CHANGE:` in the commit body.
