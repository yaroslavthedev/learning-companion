#!/usr/bin/env bash
# PreToolUse(Bash): enforce git rules from .claude/rules/git-workflow.md and
# security.md that must never depend on the agent "remembering" them.
set -uo pipefail

cmd=$(jq -r '.tool_input.command // empty')
# Drop heredoc bodies (<<EOF ... EOF): they are data such as PR text, not commands.
cmd=$(awk '
  inside { if ($0 ~ "^[[:space:]]*" tag "[[:space:]]*$") inside = 0; next }
  { print }
  match($0, /<<-?[[:space:]]*["'"'"']?[A-Za-z_][A-Za-z0-9_]*/) {
    tag = substr($0, RSTART, RLENGTH); gsub(/^<<-?[[:space:]]*["'"'"']?/, "", tag); inside = 1
  }' <<<"$cmd")
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

decide() { # $1 = deny|ask, $2 = reason
  jq -n --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: $d, permissionDecisionReason: $r}}'
  exit 0
}

branch=$(git branch --show-current 2>/dev/null || true)
# Match flags only inside the same command segment (stop at ; & | or newline),
# so text in heredocs / PR bodies doesn't trigger false positives.
seg="[^;&|"$'\n'"]*"
end='([[:space:]]|$)'

# 1. No commits or pushes to main.
if [[ "$cmd" =~ git[[:space:]]+commit ]] && [[ "$branch" == "main" ]]; then
  decide deny "Committing on main is forbidden. Create a branch: feat/<issue>-<slug> or chore/<topic>."
fi
if [[ "$cmd" =~ git[[:space:]]+push ]] && { [[ "$branch" == "main" ]] || [[ "$cmd" =~ git[[:space:]]+push${seg}[[:space:]:]main${end} ]]; }; then
  decide deny "Pushing to main is forbidden. Push the feature branch and open a PR."
fi

# 2. No force-push / history rewrite.
if [[ "$cmd" =~ git[[:space:]]+push${seg}[[:space:]](--force(-with-lease)?|-f)${end} ]]; then
  decide deny "Force-push is forbidden without explicit tech-lead instruction."
fi

# 3. Never force-add ignored files (e.g. .env).
if [[ "$cmd" =~ git[[:space:]]+add${seg}[[:space:]](-f|--force)${end} ]]; then
  decide deny "git add --force is forbidden: it bypasses .gitignore (secrets in .env)."
fi

# 3b. Never bypass git hooks (`commit -n` is short for --no-verify; `push -n` is a dry run).
if [[ "$cmd" =~ git[[:space:]]+(commit|push)${seg}[[:space:]]--no-verify${end} ]] \
  || [[ "$cmd" =~ git[[:space:]]+commit${seg}[[:space:]]-[a-ln-zA-Z]*n[a-zA-Z]*${end} ]]; then
  decide deny "Bypassing git hooks is forbidden. Fix what the hook reports instead."
fi

# 4. Merging a PR always needs the tech lead's confirmation in the UI.
if [[ "$cmd" =~ gh[[:space:]]+pr[[:space:]]+merge ]]; then
  decide ask "Merging a PR needs explicit tech-lead approval."
fi

# 5. Python only through uv (CLAUDE.md stack): no system python/pip at the start
# of a command segment. `uv run python ...` is allowed.
if [[ "$cmd" =~ (^|[;\&\|\(]|$'\n')[[:space:]]*(/[^[:space:]]*/)?(python3?|pip3?)([[:space:]]|$) ]]; then
  decide deny "System python/pip is forbidden. Use \`uv run python\` (dependencies: \`uv add\`, only if in the approved plan); for file edits use the Edit tool."
fi

# 6. Secret scan before any commit: changed + new untracked files.
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
