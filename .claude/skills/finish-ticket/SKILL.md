---
name: finish-ticket
description: After the tech lead explicitly approves a PR, merge it, sync main, move the ticket to Done and run a short retro proposing pipeline improvements. Use only after explicit approval to merge.
disable-model-invocation: true
---

# Finish ticket

Run this only when the tech lead has explicitly said to merge (e.g. "merge").

1. `gh pr checks <pr>`: CI must be green. If it's red, stop and report.
2. `gh pr merge <pr> --squash --delete-branch`
3. `git switch main && git pull --ff-only`
4. Move the issue to **Done** on the board.
5. **Retro.** Answer briefly:
   - What did the tech lead catch in review that the pipeline missed?
   - Which rule, hook or skill change would have caught it automatically?
   Propose 1–3 concrete pipeline changes (file + exact edit). Apply them only
   after approval, on a `chore/pipeline-<topic>` branch with its own PR.
