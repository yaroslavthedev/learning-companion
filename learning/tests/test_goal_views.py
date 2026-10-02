import re
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import (
    assertContains,
    assertFormError,
    assertNotContains,
    assertRedirects,
    assertTemplateUsed,
)

from accounts.tests.factories import UserFactory
from learning.models import Goal
from learning.tests.factories import GoalFactory

pytestmark = pytest.mark.django_db

ACTIVE_LINK = re.compile(r'<a [^>]*aria-current="page"[^>]*>\s*([^<]+?)\s*</a>')


def goal_url(name, goal=None):
    return reverse(name, args=[goal.pk]) if goal else reverse(name)


def goal_data(**overrides):
    return {"title": "Learn Django", "description": "", "status": "planned"} | overrides


def active_filter_labels(response):
    return ACTIVE_LINK.findall(response.content.decode())


# Login required


@pytest.mark.parametrize(
    "url_name, needs_goal",
    [
        ("goal-list", False),
        ("goal-create", False),
        ("goal-detail", True),
        ("goal-update", True),
        ("goal-delete", True),
    ],
)
def test_goal_pages_redirect_anonymous_to_login(client, url_name, needs_goal):
    url = goal_url(url_name, GoalFactory() if needs_goal else None)

    response = client.get(url)

    assertRedirects(response, f"{reverse('login')}?next={url}")


# /goals/


def test_list_shows_only_own_goals(client):
    alice = UserFactory()
    GoalFactory(owner=alice, title="Alice goal")
    GoalFactory(title="Bob goal")
    client.force_login(alice)

    response = client.get(goal_url("goal-list"))

    assertTemplateUsed(response, "learning/goal_list.html")
    assertContains(response, "Alice goal")
    assertNotContains(response, "Bob goal")


def test_list_orders_newest_first(client):
    alice = UserFactory()
    older = GoalFactory(owner=alice, title="Older goal")
    GoalFactory(owner=alice, title="Newer goal")
    Goal.objects.filter(pk=older.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )
    client.force_login(alice)

    content = client.get(goal_url("goal-list")).content.decode()

    assert content.index("Newer goal") < content.index("Older goal")


def test_list_filters_by_status(client):
    alice = UserFactory()
    GoalFactory(owner=alice, title="Finished goal", status="done")
    GoalFactory(owner=alice, title="Planned goal", status="planned")
    GoalFactory(owner=alice, title="Started goal", status="in_progress")
    GoalFactory(title="Bob finished goal", status="done")
    client.force_login(alice)

    response = client.get(goal_url("goal-list"), {"status": "done"})

    assertContains(response, "Finished goal")
    assertNotContains(response, "Planned goal")
    assertNotContains(response, "Started goal")
    assertNotContains(response, "Bob finished goal")


def test_list_unknown_status_shows_all_goals(client):
    alice = UserFactory()
    GoalFactory(owner=alice, title="Finished goal", status="done")
    GoalFactory(owner=alice, title="Planned goal", status="planned")
    client.force_login(alice)

    response = client.get(goal_url("goal-list"), {"status": "bogus"})

    assert response.status_code == 200
    assertContains(response, "Finished goal")
    assertContains(response, "Planned goal")


def test_list_shows_status_filter_links(client):
    client.force_login(UserFactory())
    list_url = goal_url("goal-list")

    response = client.get(list_url)

    assertContains(response, f'href="{list_url}"')
    for value, label in [
        ("planned", "Planned"),
        ("in_progress", "In progress"),
        ("done", "Done"),
    ]:
        assertContains(response, f'href="{list_url}?status={value}"')
        assertContains(response, label)


@pytest.mark.parametrize(
    "query, expected_label",
    [
        ({}, "All"),
        ({"status": "planned"}, "Planned"),
        ({"status": "in_progress"}, "In progress"),
        ({"status": "done"}, "Done"),
        ({"status": "bogus"}, "All"),
    ],
)
def test_list_marks_active_filter(client, query, expected_label):
    client.force_login(UserFactory())

    response = client.get(goal_url("goal-list"), query)

    assert active_filter_labels(response) == [expected_label]


# /goals/new/


def test_create_form_preselects_planned_status(client):
    client.force_login(UserFactory())

    response = client.get(goal_url("goal-create"))

    assertTemplateUsed(response, "learning/goal_form.html")
    assert response.context["form"]["status"].value() == "planned"


def test_create_sets_owner_to_current_user(client):
    alice = UserFactory()
    client.force_login(alice)

    response = client.post(goal_url("goal-create"), goal_data(status="in_progress"))

    goal = Goal.objects.get()
    assertRedirects(response, goal_url("goal-detail", goal))
    assert goal.owner == alice
    assert goal.title == "Learn Django"
    assert goal.status == "in_progress"


def test_create_ignores_owner_in_post_data(client):
    alice, bob = UserFactory(), UserFactory()
    client.force_login(alice)

    client.post(goal_url("goal-create"), goal_data(owner=bob.pk))

    assert Goal.objects.get().owner == alice


def test_create_with_empty_title_shows_error_and_saves_nothing(client):
    client.force_login(UserFactory())

    response = client.post(goal_url("goal-create"), goal_data(title=""))

    assert response.status_code == 200
    assertFormError(response.context["form"], "title", "This field is required.")
    assert not Goal.objects.exists()


# /goals/<pk>/


def test_detail_shows_own_goal(client):
    goal = GoalFactory(
        title="Learn Django", description="Models and views", status="in_progress"
    )
    client.force_login(goal.owner)

    response = client.get(goal_url("goal-detail", goal))

    assertTemplateUsed(response, "learning/goal_detail.html")
    assertContains(response, "Learn Django")
    assertContains(response, "Models and views")
    assertContains(response, "In progress")


# /goals/<pk>/edit/


def test_edit_updates_own_goal(client):
    goal = GoalFactory(title="Old title", status="planned")
    client.force_login(goal.owner)

    response = client.post(
        goal_url("goal-update", goal),
        goal_data(title="New title", description="More", status="done"),
    )

    assertRedirects(response, goal_url("goal-detail", goal))
    goal.refresh_from_db()
    assert (goal.title, goal.description, goal.status) == ("New title", "More", "done")


def test_edit_bumps_updated_at_but_not_created_at(client):
    goal = GoalFactory()
    past = timezone.now() - timedelta(days=1)
    Goal.objects.filter(pk=goal.pk).update(created_at=past, updated_at=past)
    client.force_login(goal.owner)

    client.post(goal_url("goal-update", goal), goal_data(title="Edited"))

    goal.refresh_from_db()
    assert goal.created_at == past
    assert goal.updated_at > past


# /goals/<pk>/delete/


def test_delete_get_shows_confirmation_and_keeps_goal(client):
    goal = GoalFactory(title="Learn Django")
    client.force_login(goal.owner)

    response = client.get(goal_url("goal-delete", goal))

    assertTemplateUsed(response, "learning/goal_confirm_delete.html")
    assertContains(response, "Learn Django")
    assertContains(response, "csrfmiddlewaretoken")
    assert Goal.objects.filter(pk=goal.pk).exists()


def test_delete_post_removes_own_goal(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.post(goal_url("goal-delete", goal))

    assertRedirects(response, goal_url("goal-list"))
    assert not Goal.objects.filter(pk=goal.pk).exists()


# Another user's goal


@pytest.mark.parametrize(
    "url_name, method",
    [
        ("goal-detail", "get"),
        ("goal-update", "get"),
        ("goal-update", "post"),
        ("goal-delete", "get"),
        ("goal-delete", "post"),
    ],
)
def test_other_users_goal_returns_404(client, url_name, method):
    goal = GoalFactory(title="Alice goal", status="planned")
    client.force_login(UserFactory())

    response = getattr(client, method)(
        goal_url(url_name, goal), goal_data(title="Hacked", status="done")
    )

    assert response.status_code == 404
    goal.refresh_from_db()
    assert (goal.title, goal.status) == ("Alice goal", "planned")
