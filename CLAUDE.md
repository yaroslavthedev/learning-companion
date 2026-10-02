# Learning Companion — CLAUDE.md

Django app: users set learning goals, log study sessions, attach resources,
and get AI-generated progress summaries and next steps.

The code is written entirely by an AI agent. A human tech lead approves plans
and reviews PRs. Follow the pipeline below; don't skip checkpoints.

## Stack (fixed — do not add or swap technologies without tech-lead approval)

- Python 3.12, managed by **uv** (never use system `python3`/`pip`)
- Django 5.2 LTS, server-rendered templates + Pico.css (no JS framework)
- PostgreSQL everywhere: dev, tests, CI and prod (no SQLite)
- pytest + pytest-django + factory_boy; ruff for lint + format
- `openai` SDK for AI features; mocked in all tests
- django-environ for config; gunicorn + whitenoise in Docker; GitHub Actions CI

## Commands

Verified in #2.

```bash
cp -n .env.example .env                   # once: local dev env (never commit .env)
uv sync                                   # install dependencies
docker compose up -d --wait db            # local Postgres 16 on host port 5433
uv run python manage.py migrate           # apply migrations
uv run python manage.py runserver         # http://127.0.0.1:8000
uv run python manage.py makemigrations    # after any model change
uv run pytest                             # all tests (needs the db container)
uv run pytest path/to/test_file.py -k name  # single test
uv run ruff check . --fix && uv run ruff format .
```

Env vars (see `.env.example`): `SECRET_KEY` (required), `DEBUG` (default False),
`ALLOWED_HOSTS` (comma-separated), `DATABASE_URL` (required),
`POSTGRES_USER/PASSWORD/DB` (docker compose), `DJANGO_ENV_FILE` (optional,
alternative env file; settings tests use it to ignore `.env`).
Host port 5432 is taken by another project on the dev machine, so we use 5433.

## Architecture

```
config/          settings.py (reads env / .env via django-environ), urls.py
config/tests/    settings tests (run Django in a subprocess with a clean env)
accounts/        custom User, Profile (auto-created by post_save signal in signals.py),
                 SignUpView + built-in LoginView/LogoutView (POST only), /profile/ + /profile/edit/
                 (no id in URL: get_object() returns request.user.profile)
tags/            Tag (per user) + Tag.objects.from_csv(owner, "a, b") used by forms
core/            site-wide pages: HomeView at / (name "home")
learning/        Goal + CRUD at /goals/ (names goal-list/-create/-detail/-update/-delete);
                 OwnGoalMixin scopes every goal view to request.user; list filter ?status=
templates/       base.html (Pico.css from CDN, auth-aware nav) + <app>/ templates;
                 registration/login.html for LoginView
# planned:
learning/        LearningSession, Resource + their CRUD views
learning/services/ai.py   the only module that talks to OpenAI
dashboard/       aggregation queries + dashboard page
```

### Data model

Now:

- `accounts.User` (AbstractUser, no extra fields)
- `accounts.Profile`: user (1:1, `user.profile`), name, cohort, focus_areas (M2M Tag).
  Every User gets exactly one, via the `post_save` signal; never create it by hand.
  Users older than Profile got theirs from data migration `accounts.0003`.
- `tags.Tag`: owner (FK User, `user.tags`), name; unique per (owner, name);
  name stored stripped + lowercase in `save()`
- `learning.Goal`: owner (FK User, `user.goals`), title, description (optional),
  status (`Goal.Status`: planned / in_progress / done, default planned),
  created_at, updated_at; newest first. `Goal.objects.for_user(u).with_status(s)`
  (unknown/empty status → no filter)

Test factories: `accounts.tests.factories.UserFactory` (profile comes with it),
`tags.tests.factories.TagFactory`, `learning.tests.factories.GoalFactory`. factory_boy resolves `Meta.model` when the
factory class is defined, so a factory for a not-yet-existing model makes its
importing test modules fail at collection (fine for red, but add the model first in green).

Target:

- `LearningSession`: goal (FK), date, duration_minutes, notes, tags (M2M Tag)
- `Resource`: goal (FK), url, title, type (article / video / repo / doc)

Ownership: every row belongs to a user, either directly (`owner`) or through `goal__owner`.

## Conventions

- **Data scoping:** every queryset in a view is filtered by `request.user`.
  Another user's object → 404, never 403 and never the data. See `.claude/rules/`.
- Views: Django class-based generic views (ListView, CreateView, ...) with
  `LoginRequiredMixin`; scoping goes in `get_queryset()`.
- Business logic and queries live in models/managers/services, not templates.
- Secrets only via env vars (`.env`, documented in `.env.example`).
- Tests sit next to the code: `<app>/tests/test_*.py`. Use factories, not fixtures files.
- Commit messages: imperative mood, reference the issue (`Add goal CRUD (#3)`).

## Workflow (AI factory)

Board: https://github.com/users/yaroslavthedev/projects/1
Columns: Backlog → Ready → In Progress → Review → Done

1. `/next-ticket` takes the top **Ready** issue → In Progress, branch `feat/<n>-<slug>`
2. **Plan** (skill `planning`) → STOP for tech-lead approval
3. **Tests red** (skill `tdd-implementation`) → show test list → STOP for approval
4. **Code green + refactor**; hooks run ruff + pytest automatically
5. **Self-review + update this file** (skill `self-review`) → STOP for "ок" to push
   → PR → issue to Review → STOP
6. Tech lead reviews. Only on explicit "merge": skill `finish-ticket`
   (squash merge, issue → Done, retro with pipeline improvements)

The agent never merges a PR or moves an issue to Ready on its own.
Approvals are stored as issue labels `plan-approved` / `tests-approved`.
Board helper: `.claude/scripts/board.sh list|next|current|move <n> <status>`.

## Keeping this file current

After every feature, update **Commands**, **Architecture** and **Data model**
to match reality, in the same PR. Keep the file short: rules belong in
`.claude/rules/`, step-by-step procedures in `.claude/skills/`.
