#!/usr/bin/env bash
# PostToolUse(Edit|Write): auto-format and lint the edited Python file with ruff.
# Remaining lint errors are fed back to the agent (exit 2) so it fixes them.
set -uo pipefail

file=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
[[ "$file" == *.py ]] || exit 0
[[ -f "$file" ]] || exit 0

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
# Before scaffolding (ticket #1) there is no Python project yet.
[[ -f pyproject.toml ]] && command -v uv >/dev/null || exit 0

uv run --quiet ruff format "$file" >/dev/null 2>&1
if ! out=$(uv run --quiet ruff check --fix "$file" 2>&1); then
  echo "ruff found problems in $file. Fix them:" >&2
  echo "$out" >&2
  exit 2
fi
exit 0
