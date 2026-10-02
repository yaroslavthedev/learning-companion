import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import NoReverseMatch, reverse
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from accounts.tests.factories import UserFactory
from learning.tests.factories import GoalFactory, LearningSessionFactory
from tags.tests.factories import TagFactory

pytestmark = pytest.mark.django_db


def dashboard_url():
    try:
        return reverse("dashboard")
    except NoReverseMatch:
        pytest.fail("URL name 'dashboard' is not defined")


def tagged_session(owner, minutes, tag_name):
    learning_session = LearningSessionFactory(
        goal=GoalFactory(owner=owner), duration_minutes=minutes
    )
    learning_session.tags.add(TagFactory(owner=owner, name=tag_name))
    return learning_session


def test_dashboard_requires_login(client):
    url = dashboard_url()

    response = client.get(url)

    assertRedirects(response, f"{reverse('login')}?next={url}")


def test_dashboard_page_shows_tag_hours(client):
    user = UserFactory()
    goal = GoalFactory(owner=user)
    docker = TagFactory(owner=user, name="docker")
    for minutes in (60, 30):
        LearningSessionFactory(goal=goal, duration_minutes=minutes).tags.add(docker)
    client.force_login(user)

    response = client.get(dashboard_url())

    assert response.status_code == 200
    assertContains(response, "docker")
    assertContains(response, "1.5 h")


def test_dashboard_page_shows_only_own_numbers(client):
    user = UserFactory()
    other = UserFactory()
    GoalFactory(owner=user, status="planned")
    GoalFactory.create_batch(3, owner=other, status="done")
    tagged_session(user, 30, "docker")
    tagged_session(other, 60, "kubernetes")
    client.force_login(user)

    response = client.get(dashboard_url())

    counts = {
        row["label"]: row["count"] for row in response.context["goals_per_status"]
    }
    assert counts == {"Planned": 2, "In progress": 0, "Done": 0}
    assertContains(response, "docker")
    assertNotContains(response, "kubernetes")


def test_dashboard_new_user_sees_no_data_message(client):
    client.force_login(UserFactory())

    response = client.get(dashboard_url())

    assert response.status_code == 200
    assertContains(response, "No data yet")
    assertContains(response, f'href="{reverse("goal-create")}"')
    assertNotContains(response, "<table")


def test_dashboard_without_tagged_sessions_shows_empty_tag_line(client):
    user = UserFactory()
    LearningSessionFactory(goal=GoalFactory(owner=user), duration_minutes=45)
    client.force_login(user)

    response = client.get(dashboard_url())

    assertContains(response, "No tagged sessions yet")
    assertNotContains(response, "No data yet")


def test_dashboard_page_query_count_does_not_grow_with_data(client):
    user = UserFactory()
    client.force_login(user)
    url = dashboard_url()
    tagged_session(user, 30, "docker")

    with CaptureQueriesContext(connection) as few:
        client.get(url)
    for n in range(5):
        tagged_session(user, 30 + n, f"tag-{n}")
    with CaptureQueriesContext(connection) as many:
        client.get(url)

    assert len(many) == len(few)
    assert len(few) <= 5  # session + user + one query per aggregation
