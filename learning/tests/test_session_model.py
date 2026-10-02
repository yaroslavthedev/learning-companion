from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from learning.models import Goal, LearningSession
from learning.tests.factories import GoalFactory, LearningSessionFactory

pytestmark = pytest.mark.django_db


def test_session_date_defaults_to_today():
    session = LearningSession.objects.create(goal=GoalFactory(), duration_minutes=30)

    assert session.date == timezone.localdate()


@pytest.mark.parametrize("minutes", [0, -5])
def test_session_duration_must_be_positive(minutes):
    session = LearningSessionFactory.build(goal=GoalFactory(), duration_minutes=minutes)

    with pytest.raises(ValidationError) as error:
        session.full_clean()

    assert "duration_minutes" in error.value.message_dict


def test_sessions_are_ordered_by_date_newest_first():
    today = timezone.localdate()
    older = LearningSessionFactory(date=today - timedelta(days=2))
    newest = LearningSessionFactory(date=today)
    middle = LearningSessionFactory(date=today - timedelta(days=1))

    assert list(LearningSession.objects.all()) == [newest, middle, older]


def test_for_user_returns_only_sessions_of_own_goals():
    own = LearningSessionFactory()
    LearningSessionFactory()

    assert list(LearningSession.objects.for_user(own.goal.owner)) == [own]


def test_deleting_goal_deletes_its_sessions():
    session = LearningSessionFactory()
    other = LearningSessionFactory()

    session.goal.delete()

    assert list(LearningSession.objects.all()) == [other]


@pytest.mark.parametrize("durations, expected", [([], 0), ([60, 30], 1.5)])
def test_goal_total_hours(durations, expected):
    goal = GoalFactory()
    for minutes in durations:
        LearningSessionFactory(goal=goal, duration_minutes=minutes)
    LearningSessionFactory(duration_minutes=600)  # another goal

    assert Goal.objects.get(pk=goal.pk).total_hours() == expected
