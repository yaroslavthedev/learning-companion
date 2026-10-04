import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_nav_logged_out_shows_login_and_signup(client):
    response = client.get(reverse("home"))

    assertContains(response, f'href="{reverse("login")}"')
    assertContains(response, f'href="{reverse("signup")}"')
    assertNotContains(response, f'href="{reverse("profile")}"')
    assertNotContains(response, "Log out")


def test_nav_logged_in_shows_profile_and_logout_post_form(client):
    client.force_login(UserFactory())

    response = client.get(reverse("home"))

    assertContains(response, f'href="{reverse("profile")}"')
    assertContains(response, f'action="{reverse("logout")}"')
    assertContains(response, 'method="post"')
    assertContains(response, "csrfmiddlewaretoken")
    assertContains(response, "Log out")
    assertNotContains(response, f'href="{reverse("logout")}"')
    assertNotContains(response, f'href="{reverse("signup")}"')


def test_nav_logged_in_shows_goals_link(client):
    client.force_login(UserFactory())

    response = client.get(reverse("home"))

    assertContains(response, f'href="{reverse("goal-list")}"')
    assertContains(response, "Goals")


def test_nav_logged_out_hides_goals_link(client):
    response = client.get(reverse("home"))

    assertNotContains(response, f'href="{reverse("goal-list")}"')


def test_nav_logged_in_shows_dashboard_link(client):
    client.force_login(UserFactory())

    response = client.get(reverse("home"))

    assertContains(response, 'href="/dashboard/"')
    assertContains(response, "Dashboard")


def test_nav_logged_out_hides_dashboard_link(client):
    response = client.get(reverse("home"))

    assertNotContains(response, 'href="/dashboard/"')
