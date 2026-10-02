from datetime import timedelta

import pytest
from django.utils import timezone

from accounts.tests.factories import UserFactory
from learning.models import Goal
from learning.tests.factories import GoalFactory

pytestmark = pytest.mark.django_db


def test_goal_str_is_title():
    assert str(GoalFactory(title="Learn Django")) == "Learn Django"


def test_new_goal_defaults_to_planned():
    goal = Goal.objects.create(owner=UserFactory(), title="Learn Django")

    assert goal.status == Goal.Status.PLANNED == "planned"


def test_status_choices():
    assert Goal.Status.choices == [
        ("planned", "Planned"),
        ("in_progress", "In progress"),
        ("done", "Done"),
    ]


def test_goals_are_ordered_newest_first():
    older = GoalFactory()
    newer = GoalFactory()
    Goal.objects.filter(pk=older.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )

    assert list(Goal.objects.all()) == [newer, older]


def test_for_user_returns_only_own_goals():
    alice, bob = UserFactory(), UserFactory()
    own = GoalFactory(owner=alice)
    GoalFactory(owner=bob)

    assert list(Goal.objects.for_user(alice)) == [own]


def test_with_status_filters():
    done = GoalFactory(status="done")
    GoalFactory(status="planned")
    GoalFactory(status="in_progress")

    assert list(Goal.objects.with_status("done")) == [done]


@pytest.mark.parametrize("value", ["bogus", "", None])
def test_with_status_unknown_value_returns_all(value):
    GoalFactory(status="done")
    GoalFactory(status="planned")

    assert Goal.objects.with_status(value).count() == 2
