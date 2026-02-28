#!/bin/bash
# Auto git sync script for PMA repo
# Triggered on screen lock

REPO_DIR="/Users/jing/Documents/pma"
LOG_FILE="$REPO_DIR/.git-sync.log"

cd "$REPO_DIR" || exit 1

# Check if there are any changes
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "auto sync: $(date '+%Y-%m-%d %H:%M')"
    git push 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Synced changes" >> "$LOG_FILE"
    osascript -e 'display notification "PMA 代码已自动推送到 GitHub" with title "Git Auto Sync" sound name "Glass"'
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No changes to sync" >> "$LOG_FILE"
    osascript -e 'display notification "PMA 没有需要同步的变更" with title "Git Auto Sync"'
fi
