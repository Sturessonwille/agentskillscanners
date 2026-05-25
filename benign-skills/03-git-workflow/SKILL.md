---
name: git-workflow
description: Automate common git workflows including branching, rebasing, and PR creation. Use when the user needs help with git operations, branch management, or pull request workflows.
---

# Git Workflow Assistant

## When to use

Use for branch naming, syncing with `main`, conventional commits, rebases, and PR creation via GitHub CLI.

## Scripts

- **[`scripts/git_feature.sh`](scripts/git_feature.sh)** — From `main`, pull latest, create and check out `type/description-slug`.
  - Usage: `./scripts/git_feature.sh <type> <description...>`
  - Example: `./scripts/git_feature.sh feature add auth` → branch `feature/add-auth`
  - Assumes the default branch is `main` and remote `origin` exists.

- **[`scripts/git_aliases.sh`](scripts/git_aliases.sh)** — Sets local git aliases: `co`, `br`, `st`, `lg`.

## Branch naming

Use `type/description`:

- `feature/add-auth`
- `fix/login-bug`
- `chore/update-deps`
- `docs/api-reference`

## After creating a branch

Stage and commit (example):

```bash
git add -p
git commit -m "feat: add user authentication"
git push -u origin feature/my-feature
```

## Commit messages (Conventional Commits)

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Rebasing

```bash
git fetch origin
git rebase origin/main
```

If there are conflicts: fix files, `git add` them, then `git rebase --continue`.

## Creating a PR

```bash
gh pr create --title "feat: add auth" --body "Adds JWT-based authentication"
```
