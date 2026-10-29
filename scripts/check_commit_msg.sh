#!/usr/bin/env bash
# Commit messages: ADDED:, FIXED:, TASK:, DOCS: or REFACTOR: then what changed, e.g.
# "FIXED: reject items with an empty name". The changelog (cliff.toml) is grouped by prefix.
# Merge, revert, fixup! and squash! commits pass. Used by the commit-msg hook.
#
#     scripts/check_commit_msg.sh .git/COMMIT_EDITMSG
set -euo pipefail

file="${1:?usage: check_commit_msg.sh <commit-message-file>}"
subject="$(grep -v '^#' "$file" | head -n 1 || true)"  # an empty message has no lines

if [[ "$subject" =~ ^(ADDED|FIXED|TASK|DOCS|REFACTOR):\ [^[:space:]] \
  || "$subject" =~ ^(Merge|Revert\ \") \
  || "$subject" =~ ^(fixup|squash|amend)!\  ]]; then
  exit 0
fi
echo "Commit message '$subject' must start with ADDED:, FIXED:, TASK:, DOCS: or REFACTOR: and a space," >&2
echo "e.g. 'FIXED: reject items with an empty name'. Fix it with: git commit --amend" >&2
exit 1
