import pytest
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model

from accounts.tests.factories import UserFactory


def test_auth_user_model_is_custom_accounts_user():
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert get_user_model()._meta.label == "accounts.User"


@pytest.mark.django_db
def test_create_user_and_check_password():
    user = UserFactory(username="alice", password="correct-horse")

    assert user._meta.label == "accounts.User"
    assert user.check_password("correct-horse")
    assert authenticate(username="alice", password="correct-horse") == user
    assert authenticate(username="alice", password="wrong") is None
