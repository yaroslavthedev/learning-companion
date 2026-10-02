"""Settings are read once per process, so env-driven settings are tested by
starting Django in a subprocess with a controlled environment."""

import json
import os
import subprocess
import sys
from pathlib import Path

from django.db import connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def run_django(tmp_path, code, **env_overrides):
    empty_env_file = tmp_path / "empty.env"
    empty_env_file.touch()
    env = {
        "PATH": os.environ["PATH"],
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "DJANGO_ENV_FILE": str(empty_env_file),
        "SECRET_KEY": "test-key",
        "DATABASE_URL": "postgres://user:pass@localhost:5433/unused",
    }
    env.update(env_overrides)
    env = {key: value for key, value in env.items() if value is not None}
    return subprocess.run(
        [sys.executable, *code],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def print_setting(tmp_path, name, **env_overrides):
    code = (
        "import json; from django.conf import settings; "
        f"print(json.dumps(settings.{name}))"
    )
    result = run_django(tmp_path, ["-c", code], **env_overrides)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_missing_secret_key_fails_with_clear_error(tmp_path):
    result = run_django(tmp_path, ["manage.py", "check"], SECRET_KEY=None)

    assert result.returncode != 0
    assert "Set the SECRET_KEY environment variable" in result.stderr


def test_debug_defaults_to_false_when_unset(tmp_path):
    assert print_setting(tmp_path, "DEBUG") is False


def test_allowed_hosts_read_from_env(tmp_path):
    hosts = print_setting(
        tmp_path, "ALLOWED_HOSTS", ALLOWED_HOSTS="example.com,www.example.com"
    )

    assert hosts == ["example.com", "www.example.com"]


def test_database_backend_is_postgresql():
    assert connection.vendor == "postgresql"
