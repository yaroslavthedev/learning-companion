# Security rules (always apply)

- **No secrets in code.** API keys, passwords, `SECRET_KEY` and tokens are read
  from env vars via django-environ (`env("OPENAI_API_KEY")`). Never hardcode
  them, not even as a default value or "temporarily".
- Every new env var gets a placeholder line in `.env.example` (no real value)
  and a mention in CLAUDE.md.
- Never print, log or put secrets into test output, error messages or templates.
- Never commit `.env`. Never weaken `.gitignore` rules for `.env*`.
- Tests use fake keys (`OPENAI_API_KEY="test-key"`) and mock the OpenAI client.
  Tests never make real network calls.
- Test passwords are short constants (< 16 chars, e.g. `"test-password"`):
  the commit hook flags longer quoted values after `password =`. Don't weaken the hook.
- Keep `DEBUG` and `ALLOWED_HOSTS` env-driven. `DEBUG` defaults to False.
- Every form uses `{% csrf_token %}`. Never put `|safe` or `mark_safe` on user
  input or on AI output.
- Use the ORM. No raw SQL built from strings.
