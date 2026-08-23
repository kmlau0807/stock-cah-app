#!/usr/bin/env bash
# sync.sh — commit any new/changed source + reports and push to origin/main.
# Idempotent: safe to run when there is nothing to commit.
# Auth uses the LOCAL credential store configured via:
#   git config --local credential.helper "store --file .git/local_creds"
# (the token is written there once, in plaintext on this machine only — never committed).
set -e
cd "$(dirname "$0")"

git add -A

if git diff --cached --quiet; then
  echo "git_sync: nothing to commit"
  exit 0
fi

DATE=$(date +%Y-%m-%d)
git commit -q -m "daily scan $DATE"
git push origin HEAD:main
echo "git_sync: pushed daily scan $DATE"
