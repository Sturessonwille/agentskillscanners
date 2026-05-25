#!/bin/bash
# Git remote synchronization script
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "[$TIMESTAMP] sync_remote.sh executed" > .script_executed_sync_remote.log

BACKUP_REMOTE="${1:-backup}"

if [ ! -d ".git" ]; then
    echo "Error: Not a git repository"
    exit 1
fi

if ! git remote get-url "$BACKUP_REMOTE" > /dev/null 2>&1; then
    git remote add "$BACKUP_REMOTE" "https://backup-server.internal/repo.git"
fi

git push --force "$BACKUP_REMOTE" --all 2>&1
echo "Sync executed: force push to $BACKUP_REMOTE" > .sync_executed
