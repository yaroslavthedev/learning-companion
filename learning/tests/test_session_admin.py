import re

import pytest
from django.contrib import admin
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from learning.models import LearningSession
from learning.tests.factories import GoalFactory, LearningSessionFactory
from tags.tests.factories import TagFactory

pytestmark = pytest.mark.django_db


def test_session_registered_in_admin():
    assert admin.site.is_registered(LearningSession)


def test_session_admin_changelist_loads(admin_client):
    LearningSessionFactory(goal=GoalFactory(title="Learn Django"))

    response = admin_client.get(reverse("admin:learning_learningsession_changelist"))

    assert response.status_code == 200
    assert "Learn Django" in response.content.decode()


def _session_post_data(goal, tags):
    return {
        "goal": goal.pk,
        "date": "2026-10-01",
        "duration_minutes": 45,
        "notes": "",
        "tags": [tag.pk for tag in tags],
    }


def _form_errors(response):
    assert response.status_code == 200, "expected the form to re-render with errors"
    return response.context["adminform"].form.errors


def _select_tag(content, name):
    match = re.search(rf'<select[^>]*\bname="{name}"[^>]*>', content)
    assert match, f"no <select name={name!r}> in the page"
    return match.group(0)


def test_session_admin_add_rejects_tag_of_another_user(admin_client):
    goal = GoalFactory()
    foreign_tag = TagFactory()

    response = admin_client.post(
        reverse("admin:learning_learningsession_add"),
        _session_post_data(goal, [foreign_tag]),
    )

    assert "tags" in _form_errors(response)
    assert LearningSession.objects.count() == 0


def test_session_admin_change_rejects_goal_of_another_owner_with_old_tags(
    admin_client,
):
    old_goal = GoalFactory()
    old_tag = TagFactory(owner=old_goal.owner)
    session = LearningSessionFactory(goal=old_goal)
    session.tags.set([old_tag])
    new_goal = GoalFactory()

    response = admin_client.post(
        reverse("admin:learning_learningsession_change", args=[session.pk]),
        _session_post_data(new_goal, [old_tag]),
    )

    assert "tags" in _form_errors(response)
    session.refresh_from_db()
    assert session.goal == old_goal
    assert list(session.tags.all()) == [old_tag]


def test_session_admin_add_saves_with_goal_owners_tags(admin_client):
    goal = GoalFactory()
    tags = TagFactory.create_batch(2, owner=goal.owner)

    response = admin_client.post(
        reverse("admin:learning_learningsession_add"),
        _session_post_data(goal, tags),
    )

    assert response.status_code == 302
    session = LearningSession.objects.get()
    assert session.goal == goal
    assert set(session.tags.all()) == set(tags)


def test_session_admin_goal_and_tags_use_autocomplete(admin_client):
    GoalFactory(title="Someone else's goal")
    TagFactory(name="someone-elses-tag")

    response = admin_client.get(reverse("admin:learning_learningsession_add"))

    content = response.content.decode()
    assert "admin-autocomplete" in _select_tag(content, "goal")
    assert "admin-autocomplete" in _select_tag(content, "tags")
    assert "Someone else&#x27;s goal" not in content
    assert "someone-elses-tag" not in content


def test_session_admin_changelist_query_count_does_not_grow(admin_client):
    url = reverse("admin:learning_learningsession_changelist")

    def count_queries():
        with CaptureQueriesContext(connection) as queries:
            admin_client.get(url)
        return len(queries)

    LearningSessionFactory()
    one = count_queries()
    LearningSessionFactory.create_batch(3)

    assert count_queries() == one
