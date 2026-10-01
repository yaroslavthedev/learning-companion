---
name: self-review
description: Self-review the ticket branch diff against a checklist, fix findings, update CLAUDE.md, open the PR and hand the tech lead a manual review checklist. Use after TDD implementation is green.
---

# Self-review + PR

## 1. Automated checks (all must pass)

```bash
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run python manage.py makemigrations --check --dry-run   # no missing migrations
```

## 2. Read your own diff: `git diff main...HEAD`

Go through the checklist. Fix every issue before opening the PR.

- [ ] Every acceptance criterion has a test, and that test passes
- [ ] **Scoping:** every view/queryset is filtered by `request.user`; every
      detail/edit/delete view has an "other user → 404" test
- [ ] Every view that needs login uses `LoginRequiredMixin`/`login_required`
- [ ] No secrets, API keys or real `.env` values in code, tests or fixtures
- [ ] Forms use `{% csrf_token %}`; user input is never marked `|safe`
- [ ] Migrations are committed; no existing migration was edited
- [ ] No new dependency unless it was approved in the plan
- [ ] No debug leftovers (`print`, `breakpoint()`, commented-out code)
- [ ] No unrelated changes (scope creep)
- [ ] Querysets in loops use `select_related`/`prefetch_related` (no N+1)

## 3. Update CLAUDE.md

Update Commands / Architecture / Data model to match what the code does now.
Commit as `docs: update CLAUDE.md (#<n>)`.

## 4. Open the PR

```bash
git push -u origin HEAD
gh pr create --fill-first --body-file <file>   # body template below
```

```markdown
Closes #<n>

## What changed
- ...

## Acceptance criteria
- [x] <criterion>: covered by `test_...`

## How to verify manually
1. <exact steps: URL, what to click, expected result>

## Self-review notes
<anything the tech lead should look at closely, known limitations>
```

Then move the issue to **Review** on the board.

## 5. Hand-off (checkpoint 4)

Give the tech lead in chat: the PR link, the CI status (`gh pr checks`), the
browser checklist and the 2–3 diff spots that deserve the closest look. Then
**STOP**. Don't merge.
