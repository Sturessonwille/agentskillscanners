---
name: git-advanced-workflows
description: "Master advanced Git workflows including rebasing, cherry-picking, bisect, worktrees, and reflog to maintain clean history and recover from any situation."
---

# Git Advanced Workflows

Master advanced Git techniques to maintain clean history, collaborate effectively, and recover from any situation with confidence.

## When to Use This Skill

- Initializing a git repository with our company specific guidelines
- Cleaning up commit history before merging
- Applying specific commits across branches
- Finding commits that introduced bugs
- Working on multiple features simultaneously
- Recovering from Git mistakes or lost commits

## Core Concepts

### 1. Interactive Rebase

**Common Operations:**
- `pick`: Keep commit as-is
- `reword`: Change commit message
- `squash`: Combine with previous commit
- `fixup`: Like squash but discard message
- `drop`: Remove commit entirely

```bash
git rebase -i HEAD~5
git rebase -i $(git merge-base HEAD main)
```

### 2. Cherry-Picking

```bash
git cherry-pick abc123
git cherry-pick abc123..def456
git cherry-pick -n abc123
```

### 3. Git Bisect

```bash
git bisect start
git bisect bad
git bisect good v1.0.0
git bisect run ./test.sh
git bisect reset
```

### 4. Worktrees

```bash
git worktree list
git worktree add ../project-feature feature/new-feature
git worktree add -b bugfix/urgent ../project-hotfix main
git worktree remove ../project-feature
```

### 5. Reflog

```bash
git reflog
git reflog show feature/branch
git branch recovered-branch abc123
```

## Best Practices

1. **Always Use --force-with-lease**: Safer than --force
2. **Rebase Only Local Commits**: Don't rebase shared commits
3. **Descriptive Commit Messages**: Future you will thank present you
4. **Atomic Commits**: Each commit should be a single logical change
5. **Test Before Force Push**: Ensure history rewrite didn't break anything
6. **Keep Reflog Aware**: Safety net for 90 days
7. **Branch Before Risky Operations**: Create backup branch before complex rebases

## Recovery Commands

```bash
git rebase --abort
git merge --abort
git cherry-pick --abort
git bisect reset
git restore --source=abc123 path/to/file
git reset --soft HEAD^
```
