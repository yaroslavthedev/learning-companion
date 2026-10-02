import datetime

import pytest

from accounts.tests.factories import UserFactory
from learning.tests.factories import GoalFactory, LearningSessionFactory
from tags.tests.factories import TagFactory

pytestmark = pytest.mark.django_db

# Saturday of ISO week 2026-W40 (Mon 2026-09-28 .. Sun 2026-10-04)
TODAY = datetime.date(2026, 10, 3)


def session(owner, minutes, date=TODAY, tags=()):
    learning_session = LearningSessionFactory(
        goal=GoalFactory(owner=owner), duration_minutes=minutes, date=date
    )
    learning_session.tags.add(*tags)
    return learning_session


# Goals per status


def test_goals_per_status_lists_all_statuses_with_zero():
    from dashboard.services import goals_per_status

    rows = goals_per_status(UserFactory())

    assert [(row["label"], row["count"]) for row in rows] == [
        ("Planned", 0),
        ("In progress", 0),
        ("Done", 0),
    ]


def test_goals_per_status_counts_each_status():
    from dashboard.services import goals_per_status

    user = UserFactory()
    GoalFactory.create_batch(2, owner=user, status="planned")
    GoalFactory(owner=user, status="done")

    rows = goals_per_status(user)

    assert [(row["label"], row["count"]) for row in rows] == [
        ("Planned", 2),
        ("In progress", 0),
        ("Done", 1),
    ]


def test_goals_per_status_ignores_other_users_goals():
    from dashboard.services import goals_per_status

    user = UserFactory()
    GoalFactory(owner=user, status="planned")
    GoalFactory.create_batch(3, owner=UserFactory(), status="planned")

    rows = goals_per_status(user)

    assert rows[0]["count"] == 1


def test_percent_is_relative_to_max_value():
    from dashboard.services import goals_per_status

    user = UserFactory()
    GoalFactory.create_batch(2, owner=user, status="planned")
    GoalFactory(owner=user, status="in_progress")

    rows = goals_per_status(user)

    assert [row["percent"] for row in rows] == [100, 50, 0]


def test_percent_is_zero_when_all_values_are_zero():
    from dashboard.services import goals_per_status

    rows = goals_per_status(UserFactory())

    assert [row["percent"] for row in rows] == [0, 0, 0]


def test_goals_per_status_runs_one_query(django_assert_num_queries):
    from dashboard.services import goals_per_status

    user = UserFactory()
    GoalFactory(owner=user, status="planned")
    GoalFactory(owner=user, status="done")

    with django_assert_num_queries(1):
        goals_per_status(user)


# Hours per tag


def test_hours_per_tag_sums_sessions_per_tag():
    from dashboard.services import hours_per_tag

    user = UserFactory()
    docker = TagFactory(owner=user, name="docker")
    session(user, 60, tags=[docker])
    session(user, 30, tags=[docker])

    rows = hours_per_tag(user)

    assert [(row["name"], row["hours"]) for row in rows] == [("docker", 1.5)]


def test_hours_per_tag_counts_session_for_each_of_its_tags():
    from dashboard.services import hours_per_tag

    user = UserFactory()
    docker = TagFactory(owner=user, name="docker")
    python = TagFactory(owner=user, name="python")
    session(user, 60, tags=[docker, python])

    rows = hours_per_tag(user)

    assert sorted((row["name"], row["hours"]) for row in rows) == [
        ("docker", 1.0),
        ("python", 1.0),
    ]


def test_hours_per_tag_sorted_by_hours_descending():
    from dashboard.services import hours_per_tag

    user = UserFactory()
    css = TagFactory(owner=user, name="css")
    django = TagFactory(owner=user, name="django")
    sql = TagFactory(owner=user, name="sql")
    session(user, 30, tags=[css])
    session(user, 120, tags=[django])
    session(user, 60, tags=[sql])

    rows = hours_per_tag(user)

    assert [row["name"] for row in rows] == ["django", "sql", "css"]
    assert [row["percent"] for row in rows] == [100, 50, 25]


def test_hours_per_tag_skips_untagged_sessions():
    from dashboard.services import hours_per_tag

    user = UserFactory()
    session(user, 60)

    assert hours_per_tag(user) == []


def test_hours_per_tag_ignores_other_users_sessions():
    from dashboard.services import hours_per_tag

    user = UserFactory()
    other = UserFactory()
    session(user, 30, tags=[TagFactory(owner=user, name="docker")])
    session(other, 600, tags=[TagFactory(owner=other, name="docker")])
    session(other, 60, tags=[TagFactory(owner=other, name="kubernetes")])

    rows = hours_per_tag(user)

    assert [(row["name"], row["hours"]) for row in rows] == [("docker", 0.5)]


def test_hours_per_tag_runs_one_query(django_assert_num_queries):
    from dashboard.services import hours_per_tag

    user = UserFactory()
    docker = TagFactory(owner=user, name="docker")
    python = TagFactory(owner=user, name="python")
    session(user, 60, tags=[docker, python])
    session(user, 30, tags=[docker])

    with django_assert_num_queries(1):
        hours_per_tag(user)


# Hours per week


def test_hours_per_week_returns_8_weeks_with_zeros_oldest_first():
    from dashboard.services import hours_per_week

    rows = hours_per_week(UserFactory(), today=TODAY)

    assert [row["label"] for row in rows] == [
        "2026-W33",
        "2026-W34",
        "2026-W35",
        "2026-W36",
        "2026-W37",
        "2026-W38",
        "2026-W39",
        "2026-W40",
    ]
    assert rows[0]["week_start"] == datetime.date(2026, 8, 10)
    assert rows[-1]["week_start"] == datetime.date(2026, 9, 28)
    assert [row["hours"] for row in rows] == [0] * 8


def test_hours_per_week_sunday_and_monday_fall_into_different_weeks():
    from dashboard.services import hours_per_week

    user = UserFactory()
    session(user, 60, date=datetime.date(2026, 9, 27))  # Sunday, W39
    session(user, 30, date=datetime.date(2026, 9, 28))  # Monday, W40
    session(user, 30, date=datetime.date(2026, 10, 4))  # Sunday, W40

    hours = {row["label"]: row["hours"] for row in hours_per_week(user, today=TODAY)}

    assert hours["2026-W39"] == 1.0
    assert hours["2026-W40"] == 1.0
    assert hours["2026-W38"] == 0


def test_hours_per_week_ignores_sessions_older_than_8_weeks():
    from dashboard.services import hours_per_week

    user = UserFactory()
    session(user, 60, date=datetime.date(2026, 8, 9))  # Sunday, W32
    session(user, 30, date=datetime.date(2026, 8, 10))  # Monday, W33

    rows = hours_per_week(user, today=TODAY)

    assert sum(row["hours"] for row in rows) == 0.5
    assert rows[0]["hours"] == 0.5


def test_hours_per_week_ignores_sessions_after_current_week():
    from dashboard.services import hours_per_week

    user = UserFactory()
    session(user, 60, date=datetime.date(2026, 10, 5))  # Monday, W41

    rows = hours_per_week(user, today=TODAY)

    assert [row["hours"] for row in rows] == [0] * 8


def test_hours_per_week_ignores_other_users_sessions():
    from dashboard.services import hours_per_week

    user = UserFactory()
    session(user, 30)
    session(UserFactory(), 600)

    rows = hours_per_week(user, today=TODAY)

    assert rows[-1]["hours"] == 0.5
    assert rows[-1]["percent"] == 100


def test_hours_per_week_runs_one_query(django_assert_num_queries):
    from dashboard.services import hours_per_week

    user = UserFactory()
    session(user, 60, date=datetime.date(2026, 9, 1))
    session(user, 30, date=datetime.date(2026, 9, 28))

    with django_assert_num_queries(1):
        hours_per_week(user, today=TODAY)
