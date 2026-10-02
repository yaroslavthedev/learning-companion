"""The CI workflow is the merge gate, so its contract is checked here: a later
edit must not drop a check or start depending on repository secrets.
Plain-text checks keep this free of a YAML dependency."""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKFLOW = BASE_DIR / ".github" / "workflows" / "ci.yml"


def read_workflow():
    assert WORKFLOW.is_file(), f"{WORKFLOW.relative_to(BASE_DIR)} is missing"
    return WORKFLOW.read_text()


def has_named_step(text, command):
    """A `- name:` line directly followed by `run: <command>`."""
    pattern = rf"-\s+name:[^\n]+\n\s+run:\s*{re.escape(command)}\s*$"
    return re.search(pattern, text, re.MULTILINE) is not None


def test_workflow_triggers_on_push_and_pull_request():
    text = read_workflow()

    assert re.search(r"^on:", text, re.MULTILINE)
    assert re.search(r"^\s+push:?\s*$", text, re.MULTILINE)
    assert re.search(r"^\s+pull_request:?\s*$", text, re.MULTILINE)


def test_workflow_runs_all_four_checks_as_named_steps():
    text = read_workflow()

    for command in [
        "uv run ruff check .",
        "uv run ruff format --check .",
        "uv run python manage.py makemigrations --check --dry-run",
        "uv run pytest -q",
    ]:
        assert has_named_step(text, command), f"no named step runs `{command}`"


def test_workflow_installs_with_locked_sync():
    assert has_named_step(read_workflow(), "uv sync --locked")


def test_workflow_uses_postgres_16_service_with_health_check():
    text = read_workflow()

    assert re.search(r"image:\s*postgres:16\s*$", text, re.MULTILINE)
    assert "pg_isready" in text


def test_workflow_sets_env_itself_without_dotenv():
    text = read_workflow()

    assert re.search(r"SECRET_KEY:\s*\S+", text)
    assert re.search(r"DEBUG:\s*\"?False\"?\s*$", text, re.MULTILINE)
    assert re.search(r"DATABASE_URL:\s*\S*@localhost:5432/", text)
    assert ".env" not in text


def test_workflow_uses_no_secrets_or_openai_key():
    text = read_workflow()

    assert "secrets" not in text
    assert "openai" not in text.lower()
