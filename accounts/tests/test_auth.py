import pytest
from django.apps import apps
from django.contrib import auth
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

PASSWORD = "Test-pass-42!"


def signup(client, username="newbie", password2=PASSWORD):
    return client.post(
        reverse("signup"),
        {"username": username, "password1": PASSWORD, "password2": password2},
    )


def profile_count(user):
    return apps.get_model("accounts", "Profile").objects.filter(user=user).count()


# Signup


def test_signup_page_renders_form(client):
    response = client.get(reverse("signup"))

    assert response.status_code == 200
    assertTemplateUsed(response, "accounts/signup.html")
    assert 'name="password1"' in response.content.decode()


def test_signup_creates_user_and_logs_them_in(client, django_user_model):
    response = signup(client, username="newbie")

    assertRedirects(response, reverse("profile"))
    user = django_user_model.objects.get(username="newbie")
    assert auth.get_user(client) == user


def test_signup_with_mismatched_passwords_shows_error_and_creates_nothing(
    client, django_user_model
):
    response = signup(client, password2="something-else-entirely")

    assert response.status_code == 200
    assert response.context["form"].errors
    assert not django_user_model.objects.exists()
    assert not auth.get_user(client).is_authenticated


# Profile is created automatically


def test_signup_creates_exactly_one_profile(client, django_user_model):
    signup(client, username="newbie")

    user = django_user_model.objects.get(username="newbie")
    assert profile_count(user) == 1


def test_user_created_outside_signup_also_gets_profile():
    user = UserFactory()

    assert profile_count(user) == 1


def test_saving_existing_user_again_does_not_create_second_profile():
    user = UserFactory()

    user.first_name = "Alice"
    user.save()

    assert profile_count(user) == 1


# Login / logout


def test_login_page_renders_form(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assertTemplateUsed(response, "registration/login.html")


def test_login_redirects_to_dashboard(client):
    user = UserFactory(username="alice", password=PASSWORD)

    response = client.post(
        reverse("login"), {"username": "alice", "password": PASSWORD}
    )

    assertRedirects(response, "/dashboard/", fetch_redirect_response=False)
    assert auth.get_user(client) == user


def test_login_with_wrong_password_shows_error(client):
    UserFactory(username="alice", password=PASSWORD)

    response = client.post(
        reverse("login"), {"username": "alice", "password": "wrong-password"}
    )

    assert response.status_code == 200
    assert response.context["form"].errors
    assert not auth.get_user(client).is_authenticated


def test_logout_via_post_logs_out_and_redirects_home(client):
    client.force_login(UserFactory())

    response = client.post(reverse("logout"))

    assertRedirects(response, reverse("home"))
    assert not auth.get_user(client).is_authenticated


def test_logout_via_get_is_not_allowed(client):
    client.force_login(UserFactory())

    response = client.get(reverse("logout"))

    assert response.status_code == 405
    assert auth.get_user(client).is_authenticated


def test_profile_after_logout_redirects_to_login(client):
    client.force_login(UserFactory())
    client.post(reverse("logout"))

    response = client.get(reverse("profile"))

    assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")
