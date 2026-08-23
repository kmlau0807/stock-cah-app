#!/usr/bin/env bash
# sync.sh — commit any new/changed source + reports and push to origin/main.
# Idempotent: safe to run when there is nothing to commit.
# Used by the daily cup-and-handle automation and can be run manually.
set -e
cd "$(dirname "$0")"

git add -A

if git diff --cached --quiet; then
  echo "git_sync: nothing to commit"
  exit 0
fi

DATE=$(date +%Y-%m-%d)
git commit -q -m "daily scan $DATE"
# GCM_INTERACTIVE=0 prevents a credential prompt from hanging the automation.
GCM_INTERACTIVE=0 git push origin HEAD:main
echo "git_sync: pushed daily scan $DATE"
