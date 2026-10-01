---
name: next-ticket
description: Pipeline loop entry point. Reads the board, figures out which stage the current ticket is in, and runs the matching skill (planning, tdd-implementation, self-review), or picks the next Ready ticket. Run by the tech lead as /next-ticket.
disable-model-invocation: true
---

# /next-ticket: the pipeline loop

## Board right now

Active (In Progress / Review):
!`.claude/scripts/board.sh current`

Next in Ready:
!`.claude/scripts/board.sh next`

Git: !`git branch --show-current` · !`git status --short | head -5`

## Decide what to do (first matching rule wins)

Approvals are stored as issue labels so they survive between sessions.
Add a label **only right after the tech lead explicitly approves in chat**:
`gh issue edit <n> --add-label plan-approved` (or `tests-approved`).

| # | Situation | Action |
|---|---|---|
| 1 | Uncommitted changes that don't belong to the active ticket | STOP. Ask the tech lead what to do with them |
| 2 | A ticket is in **Review** | Show the PR link + `gh pr checks`. Remind that merging = `/finish-ticket` after their review. Don't start new work |
| 3 | A ticket is **In Progress**, no `plan-approved` label, no plan comment on the issue | Run skill **planning** |
| 4 | In Progress, plan comment exists, no `plan-approved` | Re-show the plan summary. Ask for approval. STOP |
| 5 | In Progress, `plan-approved`, no `test:` commit on the branch | Run skill **tdd-implementation**, step 1 (red) |
| 6 | In Progress, `test:` commit exists, no `tests-approved` | Re-show the test list. Ask for approval. STOP |
| 7 | In Progress, `tests-approved`, no PR yet | Continue **tdd-implementation** (green + refactor), then skill **self-review** |
| 8 | Nothing active, a ticket in **Ready** | Start it (below), then run skill **planning** |
| 9 | Nothing active, Ready is empty | Show `board.sh list`. Ask the tech lead to move the next ticket to Ready. STOP |

Check the stage with real data, not memory:
`gh issue view <n> --json labels,comments`, `git log main..HEAD --oneline`,
`gh pr list --head <branch>`.

## Starting a Ready ticket

```bash
git switch main && git pull --ff-only
git switch -c feat/<n>-<short-slug>
.claude/scripts/board.sh move <n> "In Progress"
```

## Rules of the loop

- WIP limit = 1: never start a new ticket while another is In Progress or Review.
- One stage per run. After a stage reaches its STOP, end the turn. The tech
  lead runs `/next-ticket` again after giving feedback.
- Never move tickets to Ready, never merge (see `.claude/rules/git-workflow.md`).
- Start every reply with one line: `Ticket #<n> · stage: <stage> · next STOP: <checkpoint>`.
