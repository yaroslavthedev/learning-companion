---
paths:
  - "**/*.py"
  - "templates/**/*.html"
  - "**/templates/**/*.html"
---

# Code style rules (Python and Django templates)

- ruff is the source of truth for formatting and lint. Don't fight it and don't
  add `# noqa` without a reason in a comment.
- Follow Django conventions: fat models / thin views. Queries and business
  logic go in model methods, managers or `services/`, not in views or templates.
- Prefer class-based generic views (`ListView`, `DetailView`, `CreateView`,
  `UpdateView`, `DeleteView`) over hand-written ones.
- Status / type fields use `models.TextChoices`, not bare strings.
- Every model has `__str__` and an explicit `ordering` in `Meta`.
- Name URLs (`name="goal-detail"`) and use `{% url %}` / `reverse()`, never
  hardcoded paths.
- Templates extend `base.html`. Use semantic HTML for Pico.css; avoid custom
  CSS unless necessary.
- Type hints on service functions. Docstrings only where the *why* isn't obvious.
- No commented-out code, no `print()` debugging left behind.
