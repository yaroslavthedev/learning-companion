"""Suite-wide safety net: tests never talk to OpenAI.

Every test gets a fake key, and the HTTP client the openai SDK uses (httpx2)
refuses to send, so a test that forgets to mock OpenAI fails instead of
making a real network call."""

import httpx2
import pytest


class NetworkCallInTests(AssertionError):
    pass


@pytest.fixture(autouse=True)
def fake_openai_key(settings):
    settings.OPENAI_API_KEY = "test-key"


@pytest.fixture(autouse=True)
def block_http(monkeypatch):
    def refuse(self, request, *args, **kwargs):
        raise NetworkCallInTests(f"Unmocked HTTP call in tests: {request.url}")

    monkeypatch.setattr(httpx2.Client, "send", refuse)
