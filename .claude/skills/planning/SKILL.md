---
name: planning
description: Turn a Ready ticket into an implementation plan and test list, post it on the issue, then stop for tech-lead approval. Use at the start of every ticket, before writing any code or tests.
---

# Planning

Goal: the tech lead can approve or correct the approach *before* any code exists.
**Do not write code or tests in this stage.**

## Steps

1. Read the ticket: `gh issue view <n> --repo yaroslavthedev/learning-companion --comments`.
2. Read `CLAUDE.md` and the code the ticket touches. Check real file contents;
   don't assume what exists.
3. If a criterion is ambiguous or conflicts with CLAUDE.md, list it under
   **Open questions** instead of guessing.
4. Write the plan using the template below.
5. Post it as an issue comment: `gh issue comment <n> --body-file <file>`.
6. Show the plan in chat and **STOP**. Wait for explicit approval ("ok" /
   "approved"). If the tech lead requests changes, update the comment and stop again.

## Plan template

```markdown
## Plan for #<n>

**Approach:** <2–4 sentences>

**Files**
- create: `path` (purpose)
- modify: `path` (what changes)

**Models / migrations:** <new models/fields, or "none">
**URLs & views:** <url → view → template>
**New dependencies:** <package + why, or "none">. Each one needs approval.

**Test list** (each acceptance criterion → at least one test)
| Acceptance criterion | Test |
|---|---|
| <criterion> | `test_<behaviour>` |

**Risks / open questions**
- ...

**Out of scope**
- ...
```

## Checks before posting

- Every acceptance criterion maps to at least one test.
- Every view that returns user data has an "other user gets 404" test.
- No technology outside the CLAUDE.md stack.
- New model every existing row must have (1:1 like Profile) or a new required
  field → plan a data migration for existing rows + a test with
  `MigrationExecutor` (migrate back, create rows via historical models, migrate forward).
- New FK/M2M between user-owned models, or a new admin → plan how the same
  owner is enforced (form queryset, admin read-only/autocomplete) and test it.
