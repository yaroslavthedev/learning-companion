#!/usr/bin/env bash
# PreToolUse(Bash): enforce git rules from .claude/rules/git-workflow.md and
# security.md that must never depend on the agent "remembering" them.
set -uo pipefail

cmd=$(jq -r '.tool_input.command // empty')
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

decide() { # $1 = deny|ask, $2 = reason
  jq -n --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: $d, permissionDecisionReason: $r}}'
  exit 0
}

branch=$(git branch --show-current 2>/dev/null || true)

# 1. No commits or pushes to main.
if [[ "$cmd" =~ git[[:space:]]+commit ]] && [[ "$branch" == "main" ]]; then
  decide deny "Committing on main is forbidden. Create a branch: feat/<issue>-<slug> or chore/<topic>."
fi
if [[ "$cmd" =~ git[[:space:]]+push ]] && { [[ "$branch" == "main" ]] || [[ "$cmd" =~ [[:space:]:]main([[:space:]]|$) ]]; }; then
  decide deny "Pushing to main is forbidden. Push the feature branch and open a PR."
fi

# 2. No force-push / history rewrite.
if [[ "$cmd" =~ git[[:space:]]+push.*(--force|[[:space:]]-f([[:space:]]|$)) ]]; then
  decide deny "Force-push is forbidden without explicit tech-lead instruction."
fi

# 3. Never force-add ignored files (e.g. .env).
if [[ "$cmd" =~ git[[:space:]]+add.*(-f|--force) ]]; then
  decide deny "git add --force is forbidden: it bypasses .gitignore (secrets in .env)."
fi

# 4. Merging a PR always needs the tech lead's confirmation in the UI.
if [[ "$cmd" =~ gh[[:space:]]+pr[[:space:]]+merge ]]; then
  decide ask "Merging a PR needs explicit tech-lead approval."
fi

# 5. Secret scan before any commit: changed + new untracked files.
if [[ "$cmd" =~ git[[:space:]]+commit ]]; then
  pattern='sk-[A-Za-z0-9_-]{20,}|(api[_-]?key|secret[_-]?key|password|token)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"'[:space:]]{16,}["'"'"']'
  hits=$({
    git diff HEAD 2>/dev/null | grep '^+' | grep -v '^+++'
    git ls-files --others --exclude-standard -z 2>/dev/null | xargs -0 cat 2>/dev/null
  } | grep -iE "$pattern" | head -5 | sed -E 's/(sk-.{4}|["'"'"'][^"'"'"']{4})[^"'"'"'[:space:]]+/\1…/g')
  if [[ -n "$hits" ]]; then
    decide deny "Possible hardcoded secret in the changes. Read it from env instead (see .claude/rules/security.md). Matches (masked): $hits"
  fi
fi

exit 0
