"""The root conftest.py guard: an OpenAI call nobody mocked fails the test
instead of reaching the network."""

import pytest
from openai import OpenAI

from conftest import NetworkCallInTests


def test_network_guard_blocks_unmocked_openai_call():
    client = OpenAI(api_key="test-key", max_retries=0)

    with pytest.raises(NetworkCallInTests):
        client.chat.completions.create(model="test-model", messages=[])


def test_every_test_gets_a_fake_openai_key(settings):
    assert settings.OPENAI_API_KEY == "test-key"
