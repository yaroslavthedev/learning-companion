# Learning Companion

A Django web app where learners set goals, log study sessions, attach resources,
and get AI-generated progress summaries and next steps.

Built end-to-end by an AI coding agent through an "AI factory" pipeline
(tickets → plan → TDD → review), led by a human tech lead.

**Stack:** Python 3.12 · Django 5.2 · PostgreSQL · Django templates + Pico.css · pytest · OpenAI API · Docker · GitHub Actions

## Local setup

Requirements: [uv](https://docs.astral.sh/uv/) and Docker.

```bash
cp -n .env.example .env              # dev-only settings
uv sync                              # Python 3.12 + dependencies
docker compose up -d --wait db       # PostgreSQL 16 on localhost:5433
uv run python manage.py migrate
uv run python manage.py runserver    # http://127.0.0.1:8000
```

Tests and lint:

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
```
