import datetime
import logging

import pytest

from learning.services.ai import AIUnavailable, suggest_next_steps, summarize_goal
from learning.tests.conftest import auth_error, connection_error
from learning.tests.factories import (
    GoalFactory,
    LearningSessionFactory,
    ResourceFactory,
)
from tags.tests.factories import TagFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def goal():
    goal = GoalFactory(
        title="Learn the Django ORM",
        description="Querysets, joins and aggregation",
        status="in_progress",
    )
    session = LearningSessionFactory(
        goal=goal,
        date=datetime.date(2026, 9, 14),
        duration_minutes=45,
        notes="Practised select_related",
    )
    session.tags.add(TagFactory(owner=goal.owner, name="orm"))
    ResourceFactory(goal=goal, title="Django ORM cookbook", kind="doc")
    return goal


# Client configuration


def test_client_uses_key_model_and_30s_timeout(fake_openai, goal, settings):
    settings.OPENAI_API_KEY = "test-key"
    settings.OPENAI_MODEL = "test-model"

    summarize_goal(goal)

    fake_openai.openai_class.assert_called_once()
    client_kwargs = fake_openai.openai_class.call_args.kwargs
    assert client_kwargs["api_key"] == "test-key"
    assert client_kwargs["timeout"] == 30
    assert fake_openai.create.call_args.kwargs["model"] == "test-model"


# Summary


def test_summary_returns_reply_text(fake_openai, goal):
    fake_openai.reply("  You are making steady progress.  ")

    assert summarize_goal(goal) == "You are making steady progress."


def test_summary_prompt_contains_goal_sessions_and_resources(fake_openai, goal):
    summarize_goal(goal)

    sent = fake_openai.sent_text()
    for expected in [
        "Learn the Django ORM",
        "Querysets, joins and aggregation",
        "In progress",
        "2026-09-14",
        "45",
        "Practised select_related",
        "orm",
        "Django ORM cookbook",
        "Doc",
    ]:
        assert expected in sent, f"{expected!r} missing from the prompt"


def test_summary_prompt_excludes_other_goals_and_other_users(fake_openai, goal):
    own_other_goal = GoalFactory(owner=goal.owner, title="OWN-OTHER-GOAL")
    LearningSessionFactory(goal=own_other_goal, notes="OWN-OTHER-NOTE")
    ResourceFactory(goal=own_other_goal, title="OWN-OTHER-RESOURCE")
    foreign_goal = GoalFactory(title="FOREIGN-GOAL")
    LearningSessionFactory(goal=foreign_goal, notes="FOREIGN-NOTE")
    ResourceFactory(goal=foreign_goal, title="FOREIGN-RESOURCE")

    summarize_goal(goal)

    sent = fake_openai.sent_text()
    for leaked in ["OWN-OTHER", "FOREIGN"]:
        assert leaked not in sent


def test_summary_prompt_has_only_last_10_sessions(fake_openai):
    goal = GoalFactory()
    start = datetime.date(2026, 1, 1)
    for day in range(12):
        LearningSessionFactory(
            goal=goal,
            date=start + datetime.timedelta(days=day),
            notes=f"session-day-{day:02d}",
        )

    summarize_goal(goal)

    sent = fake_openai.sent_text()
    for day in range(2, 12):
        assert f"session-day-{day:02d}" in sent
    assert "session-day-00" not in sent
    assert "session-day-01" not in sent


def test_summary_prompt_says_no_sessions(fake_openai):
    summarize_goal(GoalFactory())

    assert "No sessions logged yet." in fake_openai.sent_text()


# Next steps: prompt


def test_next_steps_prompt_contains_goal_and_sessions_only(fake_openai, goal):
    fake_openai.reply('["Step one", "Step two"]')
    foreign_goal = GoalFactory(title="FOREIGN-GOAL")
    LearningSessionFactory(goal=foreign_goal, notes="FOREIGN-NOTE")

    suggest_next_steps(goal)

    sent = fake_openai.sent_text()
    for expected in [
        "Learn the Django ORM",
        "Querysets, joins and aggregation",
        "In progress",
        "2026-09-14",
        "Practised select_related",
        "orm",
    ]:
        assert expected in sent, f"{expected!r} missing from the prompt"
    assert "FOREIGN" not in sent


def test_next_steps_prompt_says_no_sessions(fake_openai):
    fake_openai.reply('["Step one", "Step two"]')

    suggest_next_steps(GoalFactory())

    assert "No sessions logged yet." in fake_openai.sent_text()


def test_next_steps_prompt_asks_for_json_array(fake_openai, goal):
    fake_openai.reply('["Step one", "Step two"]')

    suggest_next_steps(goal)

    assert "JSON array" in fake_openai.sent_text()


# Next steps: parsing the reply


@pytest.mark.parametrize(
    "reply",
    [
        '["Read the docs", "Build a demo", "Write tests"]',
        '```json\n["Read the docs", "Build a demo", "Write tests"]\n```',
        "1. Read the docs\n2. Build a demo\n3. Write tests",
        "1) Read the docs\n2) Build a demo\n3) Write tests",
        "- Read the docs\n- Build a demo\n- Write tests",
        "* Read the docs\n* Build a demo\n* Write tests",
        "• Read the docs\n• Build a demo\n• Write tests",
        "\n  1.  Read the docs  \n\n2. Build a demo\n   \n3. Write tests\n",
    ],
    ids=[
        "json",
        "json-fence",
        "numbered-dot",
        "numbered-paren",
        "dash",
        "star",
        "bullet",
        "blank-lines-and-spaces",
    ],
)
def test_next_steps_parses_reply_formats(fake_openai, goal, reply):
    fake_openai.reply(reply)

    assert suggest_next_steps(goal) == ["Read the docs", "Build a demo", "Write tests"]


def test_next_steps_keeps_two_items(fake_openai, goal):
    fake_openai.reply('["Read the docs", "Build a demo"]')

    assert suggest_next_steps(goal) == ["Read the docs", "Build a demo"]


@pytest.mark.parametrize(
    "reply",
    ['["A", "B", "C", "D", "E"]', "1. A\n2. B\n3. C\n4. D\n5. E"],
    ids=["json", "numbered"],
)
def test_next_steps_keeps_first_three_of_more(fake_openai, goal, reply):
    fake_openai.reply(reply)

    assert suggest_next_steps(goal) == ["A", "B", "C"]


def test_next_steps_keeps_a_single_item(fake_openai, goal):
    fake_openai.reply('["Read the docs"]')

    assert suggest_next_steps(goal) == ["Read the docs"]


@pytest.mark.parametrize("reply", ["", "   \n  ", "[]", '["", "  "]'])
def test_next_steps_without_items_raises_ai_unavailable(fake_openai, goal, reply):
    fake_openai.reply(reply)

    with pytest.raises(AIUnavailable):
        suggest_next_steps(goal)


# Errors


@pytest.mark.parametrize("call", [summarize_goal, suggest_next_steps])
def test_missing_api_key_raises_without_creating_client(
    fake_openai, goal, settings, call
):
    settings.OPENAI_API_KEY = ""

    with pytest.raises(AIUnavailable):
        call(goal)

    assert not fake_openai.called


@pytest.mark.parametrize("call", [summarize_goal, suggest_next_steps])
def test_openai_error_becomes_ai_unavailable(fake_openai, goal, call):
    fake_openai.fail(connection_error())

    with pytest.raises(AIUnavailable):
        call(goal)


def test_ai_unavailable_never_contains_the_key(fake_openai, goal, settings, caplog):
    settings.OPENAI_API_KEY = "test-key-leak"
    fake_openai.fail(auth_error("Incorrect API key provided: test-key-leak"))

    with caplog.at_level(logging.DEBUG), pytest.raises(AIUnavailable) as raised:
        summarize_goal(goal)

    assert "test-key-leak" not in str(raised.value)
    assert "test-key-leak" not in caplog.text
