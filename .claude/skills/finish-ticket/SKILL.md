---
name: finish-ticket
description: After the tech lead explicitly approves a PR, merge it, sync main, move the ticket to Done and run a short retro proposing pipeline improvements. Use only after explicit approval to merge.
disable-model-invocation: true
---

# Finish ticket

Only the tech lead invokes this, by typing `/finish-ticket` (the agent can't
invoke it: `disable-model-invocation`). If they just say "merge" in chat, ask
them to run `/finish-ticket`; never merge by other means.

1. `gh pr checks <pr>`: the CI job (`.github/workflows/ci.yml`) must be listed
   and green. Red, pending or missing ("no checks reported") → stop and report.
   There is no local fallback: CI is the merge gate.
2. `gh pr merge <pr> --squash --delete-branch --subject "<issue title> (#<n>)"`
   (without `--subject`, GitHub appends the PR number to a title that already
   has the issue number: `... (#2) (#10)`)
3. `git switch main && git pull --ff-only`
4. `.claude/scripts/board.sh move <n> Done` (refuses if the issue is still open).
5. **Retro.** Answer briefly:
   - What did the tech lead catch in review that the pipeline missed?
   - Which rule, hook or skill change would have caught it automatically?
   Propose 1–3 concrete pipeline changes (file + exact edit). Apply them only
   after approval, on a `chore/pipeline-<topic>` branch with its own PR.
