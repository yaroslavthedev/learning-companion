#!/usr/bin/env bash
# Stop: before the agent ends its turn, the full test suite and lint must pass.
# Exception: the TDD red checkpoint (last commit is "test: ...") — failing
# tests are expected there, so we only report them.
set -uo pipefail

input=$(cat)
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[[ -f manage.py && -f pyproject.toml ]] && command -v uv >/dev/null || exit 0

# Only check when Python code differs from main (pipeline-only turns are skipped).
git diff --quiet main -- '*.py' 2>/dev/null && [[ -z $(git ls-files --others --exclude-standard -- '*.py') ]] && exit 0

lint=$(uv run --quiet ruff check . 2>&1); lint_rc=$?
tests=$(uv run --quiet pytest -q -x --no-header -p no:cacheprovider 2>&1); tests_rc=$?
[[ $lint_rc -eq 0 && $tests_rc -eq 0 ]] && exit 0

summary=$(printf '%s\n' "$tests" | tail -15)
last_commit=$(git log -1 --format=%s 2>/dev/null)

if [[ $tests_rc -ne 0 && $lint_rc -eq 0 && "$last_commit" == test:* ]]; then
  jq -n --arg s "$summary" '{systemMessage: ("TDD red phase: tests fail as expected.\n" + $s)}'
  exit 0
fi

# Don't loop forever: if we already blocked once, let the agent stop but warn.
if [[ $(jq -r '.stop_hook_active // false' <<<"$input") == "true" ]]; then
  jq -n --arg s "$summary" '{systemMessage: ("WARNING: tests/lint still failing.\n" + $s)}'
  exit 0
fi

{
  echo "Don't stop yet: the suite must be green (rule: .claude/rules/tdd.md)."
  [[ $lint_rc -ne 0 ]] && printf 'ruff:\n%s\n' "$(printf '%s\n' "$lint" | tail -10)"
  [[ $tests_rc -ne 0 ]] && printf 'pytest:\n%s\n' "$summary"
} >&2
exit 2
