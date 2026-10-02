from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertFormError,
    assertNotContains,
    assertRedirects,
    assertTemplateUsed,
)

from accounts.tests.factories import UserFactory
from learning.models import LearningSession
from learning.tests.factories import GoalFactory, LearningSessionFactory
from tags.models import Tag
from tags.tests.factories import TagFactory

pytestmark = pytest.mark.django_db


def session_url(name, session=None):
    return reverse(name, args=[session.pk]) if session else reverse(name)


def session_data(goal, **overrides):
    return {
        "goal": goal.pk,
        "date": "2026-09-30",
        "duration_minutes": 45,
        "notes": "",
        "tags_text": "",
    } | overrides


def tag_names(session):
    return sorted(session.tags.values_list("name", flat=True))


# Login required


@pytest.mark.parametrize(
    "url_name, needs_session",
    [
        ("session-list", False),
        ("session-create", False),
        ("session-update", True),
        ("session-delete", True),
    ],
)
def test_session_pages_redirect_anonymous_to_login(client, url_name, needs_session):
    url = session_url(url_name, LearningSessionFactory() if needs_session else None)

    response = client.get(url)

    assertRedirects(response, f"{reverse('login')}?next={url}")


# /sessions/


def test_list_shows_only_own_sessions(client):
    alice = UserFactory()
    LearningSessionFactory(goal=GoalFactory(owner=alice, title="Alice goal"))
    LearningSessionFactory(goal=GoalFactory(title="Bob goal"))
    client.force_login(alice)

    response = client.get(session_url("session-list"))

    assertTemplateUsed(response, "learning/learningsession_list.html")
    assertContains(response, "Alice goal")
    assertNotContains(response, "Bob goal")


def test_list_orders_by_date_newest_first(client):
    goal = GoalFactory()
    LearningSessionFactory(goal=goal, date=date(2026, 9, 1))
    LearningSessionFactory(goal=goal, date=date(2026, 9, 20))
    LearningSessionFactory(goal=goal, date=date(2026, 9, 10))
    client.force_login(goal.owner)

    content = client.get(session_url("session-list")).content.decode()

    positions = [content.index(d) for d in ["2026-09-20", "2026-09-10", "2026-09-01"]]
    assert positions == sorted(positions)


def test_list_shows_goal_title_date_duration_and_tags(client):
    alice = UserFactory()
    session = LearningSessionFactory(
        goal=GoalFactory(owner=alice, title="Learn Django"),
        date=date(2026, 9, 15),
        duration_minutes=75,
    )
    session.tags.set([TagFactory(owner=alice, name="django")])
    client.force_login(alice)

    response = client.get(session_url("session-list"))

    assertContains(response, "Learn Django")
    assertContains(response, "2026-09-15")
    assertContains(response, "75 min")
    assertContains(response, "django")


def test_list_query_count_does_not_grow_with_sessions(client):
    alice = UserFactory()
    client.force_login(alice)

    def count_queries():
        with CaptureQueriesContext(connection) as queries:
            client.get(session_url("session-list"))
        return len(queries)

    session = LearningSessionFactory(goal=GoalFactory(owner=alice))
    session.tags.set([TagFactory(owner=alice)])
    one = count_queries()
    for _ in range(3):
        session = LearningSessionFactory(goal=GoalFactory(owner=alice))
        session.tags.set([TagFactory(owner=alice), TagFactory(owner=alice)])

    assert count_queries() == one


# /sessions/new/


def test_form_goal_choices_are_only_own_goals(client):
    alice = UserFactory()
    own = GoalFactory(owner=alice)
    GoalFactory()
    client.force_login(alice)

    response = client.get(session_url("session-create"))

    assertTemplateUsed(response, "learning/learningsession_form.html")
    assert list(response.context["form"].fields["goal"].queryset) == [own]


def test_create_saves_session_and_redirects_to_goal(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.post(
        session_url("session-create"),
        session_data(goal, duration_minutes=90, notes="Read the ORM docs"),
    )

    session = LearningSession.objects.get()
    assertRedirects(response, reverse("goal-detail", args=[goal.pk]))
    assert session.goal == goal
    assert session.date == date(2026, 9, 30)
    assert session.duration_minutes == 90
    assert session.notes == "Read the ORM docs"


def test_create_with_other_users_goal_is_rejected_and_not_saved(client):
    bobs_goal = GoalFactory()
    client.force_login(UserFactory())

    response = client.post(session_url("session-create"), session_data(bobs_goal))

    assert response.status_code == 200
    assertFormError(
        response.context["form"],
        "goal",
        "Select a valid choice. That choice is not one of the available choices.",
    )
    assert not LearningSession.objects.exists()


@pytest.mark.parametrize("minutes", [0, -5])
def test_create_rejects_non_positive_duration(client, minutes):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.post(
        session_url("session-create"), session_data(goal, duration_minutes=minutes)
    )

    assert response.status_code == 200
    assert "duration_minutes" in response.context["form"].errors
    assert not LearningSession.objects.exists()


def test_create_preselects_goal_from_query_param(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.get(session_url("session-create"), {"goal": goal.pk})

    assert str(response.context["form"]["goal"].value()) == str(goal.pk)


def test_create_ignores_other_users_goal_in_query_param(client):
    bobs_goal = GoalFactory()
    client.force_login(UserFactory())

    response = client.get(session_url("session-create"), {"goal": bobs_goal.pk})

    assert response.status_code == 200
    assert response.context["form"]["goal"].value() is None


def test_session_tags_are_created_for_current_user(client):
    alice = UserFactory()
    goal = GoalFactory(owner=alice)
    TagFactory(name="python")  # Bob's tag with the same name
    client.force_login(alice)

    client.post(
        session_url("session-create"),
        session_data(goal, tags_text="Python, django , python"),
    )

    session = LearningSession.objects.get()
    assert tag_names(session) == ["django", "python"]
    assert all(tag.owner == alice for tag in session.tags.all())


def test_session_reuses_existing_focus_area_tag(client):
    alice = UserFactory()
    docker = TagFactory(owner=alice, name="docker")
    alice.profile.focus_areas.set([docker])
    goal = GoalFactory(owner=alice)
    client.force_login(alice)

    client.post(session_url("session-create"), session_data(goal, tags_text="Docker"))

    assert list(LearningSession.objects.get().tags.all()) == [docker]
    assert Tag.objects.filter(owner=alice).count() == 1


# /sessions/<pk>/edit/


def test_update_changes_session(client):
    session = LearningSessionFactory(duration_minutes=30)
    session.tags.set([TagFactory(owner=session.goal.owner, name="old")])
    other_goal = GoalFactory(owner=session.goal.owner)
    client.force_login(session.goal.owner)

    response = client.post(
        session_url("session-update", session),
        session_data(other_goal, duration_minutes=120, tags_text="new"),
    )

    assertRedirects(response, reverse("goal-detail", args=[other_goal.pk]))
    session.refresh_from_db()
    assert session.goal == other_goal
    assert session.duration_minutes == 120
    assert tag_names(session) == ["new"]


def test_update_form_shows_current_tags_as_text(client):
    session = LearningSessionFactory()
    owner = session.goal.owner
    session.tags.set(
        [TagFactory(owner=owner, name="python"), TagFactory(owner=owner, name="django")]
    )
    client.force_login(owner)

    response = client.get(session_url("session-update", session))

    assertTemplateUsed(response, "learning/learningsession_form.html")
    assert response.context["form"]["tags_text"].value() == "django, python"


def test_update_cannot_move_session_to_other_users_goal(client):
    session = LearningSessionFactory()
    original_goal = session.goal
    client.force_login(original_goal.owner)

    response = client.post(
        session_url("session-update", session), session_data(GoalFactory())
    )

    assert response.status_code == 200
    assert "goal" in response.context["form"].errors
    session.refresh_from_db()
    assert session.goal == original_goal


# /sessions/<pk>/delete/


def test_delete_get_shows_confirmation_and_keeps_session(client):
    session = LearningSessionFactory(goal=GoalFactory(title="Learn Django"))
    client.force_login(session.goal.owner)

    response = client.get(session_url("session-delete", session))

    assertTemplateUsed(response, "learning/learningsession_confirm_delete.html")
    assertContains(response, "Learn Django")
    assertContains(response, "csrfmiddlewaretoken")
    assert LearningSession.objects.filter(pk=session.pk).exists()


def test_delete_removes_session(client):
    session = LearningSessionFactory()
    client.force_login(session.goal.owner)

    response = client.post(session_url("session-delete", session))

    assertRedirects(response, reverse("goal-detail", args=[session.goal.pk]))
    assert not LearningSession.objects.filter(pk=session.pk).exists()


# Another user's session


@pytest.mark.parametrize(
    "url_name, method",
    [
        ("session-update", "get"),
        ("session-update", "post"),
        ("session-delete", "get"),
        ("session-delete", "post"),
    ],
)
def test_other_user_gets_404_on_session_pages(client, url_name, method):
    session = LearningSessionFactory(duration_minutes=30)
    bob = UserFactory()
    client.force_login(bob)

    response = getattr(client, method)(
        session_url(url_name, session),
        session_data(GoalFactory(owner=bob), duration_minutes=999),
    )

    assert response.status_code == 404
    session.refresh_from_db()
    assert session.duration_minutes == 30


def test_other_user_cannot_delete_session(client):
    session = LearningSessionFactory()
    client.force_login(UserFactory())

    client.post(session_url("session-delete", session))

    assert LearningSession.objects.filter(pk=session.pk).exists()


# Goal detail


def test_goal_detail_shows_its_sessions_newest_first(client):
    goal = GoalFactory()
    LearningSessionFactory(goal=goal, date=date(2026, 9, 1), notes="Older session")
    LearningSessionFactory(goal=goal, date=date(2026, 9, 20), notes="Newer session")
    LearningSessionFactory(
        goal=GoalFactory(owner=goal.owner), notes="Other goal session"
    )
    client.force_login(goal.owner)

    content = client.get(reverse("goal-detail", args=[goal.pk])).content.decode()

    assert content.index("Newer session") < content.index("Older session")
    assert "Other goal session" not in content


@pytest.mark.parametrize(
    "durations, expected",
    [([60, 30], "1.5 h"), ([60], "1 h"), ([100], "1.7 h"), ([], "0 h")],
)
def test_goal_detail_shows_total_hours(client, durations, expected):
    goal = GoalFactory()
    for minutes in durations:
        LearningSessionFactory(goal=goal, duration_minutes=minutes)
    client.force_login(goal.owner)

    response = client.get(reverse("goal-detail", args=[goal.pk]))

    assertContains(response, f"Total: {expected}")


def test_goal_detail_has_add_session_link(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.get(reverse("goal-detail", args=[goal.pk]))

    assertContains(response, f'href="{session_url("session-create")}?goal={goal.pk}"')
