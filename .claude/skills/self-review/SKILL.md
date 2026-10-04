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
uv run python manage.py migrate        # apply new migrations to the dev DB
```

Tests build their own DB, so they can't catch an unmigrated dev DB. Smoke-test
every new URL against the dev DB (logged-in Django test client in
`manage.py shell` with `override_settings(ALLOWED_HOSTS=["testserver"])`):
each must return 200, not 500.

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
- [ ] Form `clean()` doesn't read instance relations that may not exist yet on
      create (`self.instance.<fk>` raises `RelatedObjectDoesNotExist` on an add
      form → 500); skip the check when the field itself is invalid
- [ ] New service functions have type hints (`.claude/rules/code-style.md`)

## 3. Update CLAUDE.md

Update Commands / Architecture / Data model to match what the code does now.
Commit as `docs: update CLAUDE.md (#<n>)`.

## 4. Open the PR

**STOP before pushing.** Write the PR body (template below) to a file in the
scratchpad, show the tech lead `git log main..HEAD --oneline` and the body,
and wait for their "ок". Push and open the PR only after that.

```bash
git push -u origin HEAD
gh pr create --title "<issue title> (#<n>)" --body-file <file>   # body template below
```

```markdown
Closes #<n>

## What changed
- ...

## Acceptance criteria
- [x] <criterion>: covered by `test_...`

## How to verify manually
1. <exact steps: URL, what to click, expected result. Use real URLs and pks from
   the dev DB (take them from the smoke test), never `<pk>` placeholders. For an
   "other user → 404" step, say where the URL comes from and what the page looks
   like: with DEBUG it's "Page not found" + "Raised by: <app>.views.<View>"
   (the route exists, the object is scoped away), not a list of URL patterns.>

## Self-review notes
<anything the tech lead should look at closely, known limitations>
```

Wait for CI: `gh pr checks <pr> --watch`. It must list the CI job and end
green. Red → fix on the branch, push, wait again. Missing → find out why
(workflow not triggered?) before going on. Hand off only on green.

Then move the issue: `.claude/scripts/board.sh move <n> Review`.

## 5. Hand-off (checkpoint 4)

Give the tech lead in chat: the PR link, the green CI status (`gh pr checks`), the
browser checklist and the 2–3 diff spots that deserve the closest look. If the
diff adds migrations, say in the chat that they're already applied to the dev DB
(or that the tech lead must run `migrate` first). If the diff adds env vars,
give the exact lines to append to `.env` (theirs predates them; you never read
it), which ones are optional, and what the page shows when a line is missing.
End with: "after review, run
`/finish-ticket` to merge" (only the tech lead can invoke it; don't offer to
merge yourself). Then **STOP**. Don't merge.
