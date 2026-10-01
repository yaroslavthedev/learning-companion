#!/usr/bin/env bash
# Regression test for guard-bash.sh. Usage: .claude/hooks/test-guard.sh <cases.json>
# cases.json: [{"cmd": "...", "expect": "allow|deny|ask"}, ...]
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
export CLAUDE_PROJECT_DIR=$PWD
fail=0
while IFS= read -r case; do
  cmd=$(jq -r .cmd <<<"$case"); expect=$(jq -r .expect <<<"$case")
  got=$(jq -n --arg c "$cmd" '{tool_input:{command:$c}}' | .claude/hooks/guard-bash.sh \
        | jq -r '.hookSpecificOutput.permissionDecision // empty' 2>/dev/null)
  got=${got:-allow}
  if [[ "$got" == "$expect" ]]; then mark=PASS; else mark=FAIL; fail=1; fi
  printf '%s  %-6s %s\n' "$mark" "$got" "$(head -1 <<<"$cmd" | cut -c1-60)"
done < <(jq -c '.[]' "$1")
exit $fail
