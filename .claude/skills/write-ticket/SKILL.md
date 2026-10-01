---
name: write-ticket
description: Write or refine a GitHub issue (ticket) for the Learning Companion board with context, scope and testable acceptance criteria. Use when creating new tickets or when a ticket is too vague to plan.
---

# Write a ticket

A ticket is the contract between the tech lead and the agent. Every acceptance
criterion must be checkable by a test or by a concrete manual step.

## Template

```markdown
## Why
<1–3 sentences: user value / what problem this solves>

## Scope
- <what to build, as bullet points>

## Acceptance criteria
- [ ] <observable behaviour, e.g. "Logged-out user opening /goals/ is redirected to /accounts/login/">
- [ ] <data scoping: "User B gets 404 on /goals/<id of A's goal>/">
- [ ] Tests cover every criterion above; `uv run pytest` and `uv run ruff check .` pass

## Out of scope
- <what NOT to do in this ticket, to stop scope creep>

## Technical notes
- <models/fields, framework feature to use, links to docs; optional>

## Depends on
- #<issue number> (or "none")
```

## Rules for good criteria

- Observable: describes what a user or test sees, not how the code is written.
- Specific: exact URLs, field names, status values, numbers.
- Includes the unhappy path: invalid input, not logged in, other user's data.
- No vague words: "nice", "fast", "properly", "user-friendly".

## Creating the issue

```bash
gh issue create --repo yaroslavthedev/learning-companion \
  --title "<short imperative title>" --body-file <file> --label <label>
gh project item-add 1 --owner yaroslavthedev --url <issue url>
```

New tickets go to **Backlog**. Only the tech lead moves a ticket to **Ready**.
