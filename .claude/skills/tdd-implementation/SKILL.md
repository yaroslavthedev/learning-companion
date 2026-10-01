---
name: tdd-implementation
description: Implement an approved plan with strict TDD — write failing tests first (red), stop for tech-lead review of the test list, then minimal code (green) and refactor. Use after the plan for a ticket is approved.
---

# TDD implementation

Precondition: the plan is approved and you are on the ticket branch
(`feat/<n>-<slug>`). If not, stop and say so.

## 1. Red: tests first

1. Write the tests from the approved test list in `<app>/tests/test_*.py`,
   using factory_boy factories (`<app>/tests/factories.py`).
2. Test names describe behaviour: `test_other_user_gets_404_on_goal_detail`.
3. Run them: `uv run pytest <paths> -q`.
4. They must fail **for the right reason**: an assertion, a missing URL or a
   missing model. A syntax error or a broken import in the test itself doesn't
   count as red. Fix those first.
5. Commit: `test: add failing tests for <feature> (#<n>)`.
6. **STOP (checkpoint 3).** Show the tech lead:
   - the list of test names grouped by acceptance criterion
   - a short excerpt of the failing output
   Wait for approval.

## 2. Green: minimal code

1. Write the least code that makes the tests pass. Follow CLAUDE.md conventions.
2. Model changes: `uv run python manage.py makemigrations` and commit the
   generated migration. Never hand-edit or delete an existing migration.
3. Run the ticket's tests, then the whole suite: `uv run pytest -q`.
4. **Never change a test's assertions to make it pass.** If a test looks wrong,
   stop and explain why to the tech lead.
5. Commit: `feat: <what> (#<n>)`.

## 3. Refactor

1. Remove duplication and dead code, improve names. Behaviour stays the same.
2. `uv run ruff check . --fix && uv run ruff format . && uv run pytest -q`
   must all pass.
3. Commit: `refactor: <what> (#<n>)` (skip this if nothing changed).

Then continue with the `self-review` skill.
