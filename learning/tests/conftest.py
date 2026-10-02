from types import SimpleNamespace
from unittest.mock import patch

import httpx2
import pytest
from openai import APIConnectionError, APITimeoutError, AuthenticationError

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def openai_request():
    return httpx2.Request("POST", OPENAI_URL)


def openai_status_error(error_class, message, status_code):
    request = openai_request()
    response = httpx2.Response(status_code, request=request)
    return error_class(message, response=response, body=None)


def connection_error():
    return APIConnectionError(request=openai_request())


def timeout_error():
    return APITimeoutError(request=openai_request())


def auth_error(message="Incorrect API key provided."):
    return openai_status_error(AuthenticationError, message, 401)


class FakeOpenAI:
    """The OpenAI class as `learning.services.ai` sees it, with helpers."""

    def __init__(self, openai_class):
        self.openai_class = openai_class
        self.create = openai_class.return_value.chat.completions.create
        self.reply("Fake AI reply.")

    def reply(self, content):
        self.create.side_effect = None
        message = SimpleNamespace(content=content)
        self.create.return_value.choices = [SimpleNamespace(message=message)]

    def fail(self, error):
        self.create.side_effect = error

    @property
    def called(self):
        return self.openai_class.called or self.create.called

    def sent_messages(self):
        assert self.create.call_count == 1, "expected exactly one OpenAI call"
        return self.create.call_args.kwargs["messages"]

    def sent_text(self):
        """All message contents of the one call, joined: what the model saw."""
        return "\n".join(message["content"] for message in self.sent_messages())


@pytest.fixture
def fake_openai():
    with patch("learning.services.ai.OpenAI") as openai_class:
        yield FakeOpenAI(openai_class)
