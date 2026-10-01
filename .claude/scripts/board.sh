#!/usr/bin/env bash
# Board helper for the AI factory (GitHub Project #1 "Learning Companion").
#
#   board.sh list                 all tickets: number, status, labels, title
#   board.sh next                 the top ticket in Ready (empty if none)
#   board.sh current              tickets In Progress or Review
#   board.sh move <issue> <status>   status: "In Progress" | "Review" | "Done" | "Backlog"
#
# Moving to Ready is deliberately impossible: that is the tech lead's approval.
# Moving to Done is only allowed once the issue is closed (its PR was merged).
set -euo pipefail

OWNER=yaroslavthedev
REPO=yaroslavthedev/learning-companion
PROJECT_NUMBER=1
PROJECT_ID=PVT_kwHOAFa0r84BlVKR
STATUS_FIELD_ID=PVTSSF_lAHOAFa0r84BlVKRzhkCdIw

option_id() {
  case "$1" in
    "Backlog") echo d046f9bc ;;
    "In Progress") echo b060d5f0 ;;
    "Review") echo 9af05162 ;;
    "Done") echo b11da32e ;;
    "Ready") echo "Moving to Ready is the tech lead's decision. Ask them to do it on the board." >&2; exit 1 ;;
    *) echo "Unknown status: $1" >&2; exit 1 ;;
  esac
}

items() {
  gh project item-list "$PROJECT_NUMBER" --owner "$OWNER" --format json --limit 200 \
    | jq '[.items[] | select(.content.type == "Issue") | {id, number: .content.number, title: .content.title, status: (.status // "No status"), labels: (.labels // [])}]'
}

case "${1:-}" in
  list)
    items | jq -r '.[] | "#\(.number)\t[\(.status)]\t\(.labels | join(","))\t\(.title)"'
    ;;
  next)
    items | jq -r 'map(select(.status == "Ready")) | first // empty | "#\(.number)\t\(.title)"'
    ;;
  current)
    items | jq -r '.[] | select(.status == "In Progress" or .status == "Review") | "#\(.number)\t[\(.status)]\t\(.labels | join(","))\t\(.title)"'
    ;;
  move)
    issue="${2:?issue number}"; status="${3:?status}"
    opt=$(option_id "$status")
    if [[ "$status" == "Done" ]]; then
      state=$(gh issue view "$issue" --repo "$REPO" --json state -q .state)
      [[ "$state" == "CLOSED" ]] || { echo "Issue #$issue is still open. Done only after the PR is merged." >&2; exit 1; }
    fi
    item=$(items | jq -r --argjson n "$issue" '.[] | select(.number == $n) | .id')
    [[ -n "$item" ]] || { echo "Issue #$issue is not on the board." >&2; exit 1; }
    gh project item-edit --id "$item" --project-id "$PROJECT_ID" \
      --field-id "$STATUS_FIELD_ID" --single-select-option-id "$opt" >/dev/null
    echo "#$issue → $status"
    ;;
  *)
    sed -n '2,10p' "$0"; exit 1 ;;
esac
