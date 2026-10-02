import logging
import re

import pytest
from django.urls import reverse
from openai import RateLimitError
from pytest_django.asserts import (
    assertContains,
    assertNotContains,
    assertRedirects,
    assertTemplateUsed,
)

from accounts.tests.factories import UserFactory
from learning.tests.conftest import (
    auth_error,
    connection_error,
    openai_status_error,
    timeout_error,
)
from learning.tests.factories import (
    GoalFactory,
    LearningSessionFactory,
    ResourceFactory,
)

pytestmark = pytest.mark.django_db

AI_ACTIONS = ["goal-summary", "goal-next-steps"]
NOT_CONFIGURED = "AI is not configured"
UNAVAILABLE = "AI service is not available right now"
UNREADABLE = "Could not read the suggestions"


def action_url(name, goal):
    return reverse(name, args=[goal.pk])


def goal_url(goal):
    return reverse("goal-detail", args=[goal.pk])


def post_form(html, action):
    """The <form method="post"> whose action is `action`, or None."""
    pattern = rf'<form method="post" action="{re.escape(action)}">(.*?)</form>'
    match = re.search(pattern, html, re.DOTALL)
    return match.group(1) if match else None


# Buttons on goal detail


def test_goal_detail_shows_both_ai_buttons_as_post_forms_with_csrf(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.get(goal_url(goal))

    html = response.content.decode()
    for name, label in [
        ("goal-summary", "Generate summary"),
        ("goal-next-steps", "Suggest next steps"),
    ]:
        form = post_form(html, action_url(name, goal))
        assert form is not None, f"no POST form for {name}"
        assert "csrfmiddlewaretoken" in form
        assert label in form


def test_goal_detail_makes_no_openai_call(client, fake_openai):
    goal = GoalFactory()
    client.force_login(goal.owner)

    client.get(goal_url(goal))

    assert not fake_openai.called


# Access: login, ownership, POST only


@pytest.mark.parametrize("name", AI_ACTIONS)
def test_anonymous_is_redirected_and_no_openai_call(client, fake_openai, name):
    url = action_url(name, GoalFactory())

    response = client.post(url)

    assertRedirects(response, f"{reverse('login')}?next={url}")
    assert not fake_openai.called


@pytest.mark.parametrize("name", AI_ACTIONS)
def test_other_user_gets_404_and_no_openai_call(client, fake_openai, name):
    goal_of_a = GoalFactory()
    client.force_login(UserFactory())

    response = client.post(action_url(name, goal_of_a))

    assert response.status_code == 404
    assert not fake_openai.called


@pytest.mark.parametrize("name", AI_ACTIONS)
def test_missing_goal_gets_404_and_no_openai_call(client, fake_openai, name):
    client.force_login(UserFactory())

    response = client.post(reverse(name, args=[999999]))

    assert response.status_code == 404
    assert not fake_openai.called


@pytest.mark.parametrize("name", AI_ACTIONS)
def test_get_not_allowed(client, fake_openai, name):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.get(action_url(name, goal))

    assert response.status_code == 405
    assert not fake_openai.called


# Summary


def test_summary_shows_ai_text_on_goal_page(client, fake_openai):
    goal = GoalFactory(title="Learn the Django ORM")
    LearningSessionFactory(goal=goal, notes="Practised annotate")
    ResourceFactory(goal=goal, title="Django ORM cookbook")
    fake_openai.reply("You are making steady progress.")
    client.force_login(goal.owner)

    response = client.post(action_url("goal-summary", goal))

    assert response.status_code == 200
    assertTemplateUsed(response, "learning/goal_detail.html")
    assertContains(response, "You are making steady progress.")
    assertContains(response, "Learn the Django ORM")
    assertContains(response, "Practised annotate")
    assertContains(response, "Django ORM cookbook")


def test_summary_sends_this_goal_to_openai(client, fake_openai):
    goal = GoalFactory(title="Learn the Django ORM")
    GoalFactory(owner=goal.owner, title="OWN-OTHER-GOAL")
    GoalFactory(title="FOREIGN-GOAL")
    client.force_login(goal.owner)

    client.post(action_url("goal-summary", goal))

    sent = fake_openai.sent_text()
    assert "Learn the Django ORM" in sent
    assert "OWN-OTHER-GOAL" not in sent
    assert "FOREIGN-GOAL" not in sent


def test_summary_works_for_goal_without_sessions(client, fake_openai):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.post(action_url("goal-summary", goal))

    assert response.status_code == 200
    assertContains(response, "Fake AI reply.")
    assert "No sessions logged yet." in fake_openai.sent_text()


def test_summary_output_is_escaped(client, fake_openai):
    goal = GoalFactory()
    fake_openai.reply("<script>alert(1)</script>")
    client.force_login(goal.owner)

    response = client.post(action_url("goal-summary", goal))

    assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
    assertNotContains(response, "<script>alert(1)")


# Next steps


def test_next_steps_shows_items_as_list(client, fake_openai):
    goal = GoalFactory()
    fake_openai.reply('["Read the docs", "Build a demo", "Write tests", "Extra"]')
    client.force_login(goal.owner)

    response = client.post(action_url("goal-next-steps", goal))

    assert response.status_code == 200
    assertTemplateUsed(response, "learning/goal_detail.html")
    assertContains(response, "<li>Read the docs</li>", html=True)
    assertContains(response, "<li>Build a demo</li>", html=True)
    assertContains(response, "<li>Write tests</li>", html=True)
    assertNotContains(response, "Extra")


def test_next_steps_works_for_goal_without_sessions(client, fake_openai):
    goal = GoalFactory()
    fake_openai.reply("1. Read the docs\n2. Build a demo")
    client.force_login(goal.owner)

    response = client.post(action_url("goal-next-steps", goal))

    assertContains(response, "<li>Build a demo</li>", html=True)
    assert "No sessions logged yet." in fake_openai.sent_text()


def test_next_steps_output_is_escaped(client, fake_openai):
    goal = GoalFactory()
    fake_openai.reply('["<script>alert(1)</script>", "Build a demo"]')
    client.force_login(goal.owner)

    response = client.post(action_url("goal-next-steps", goal))

    assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
    assertNotContains(response, "<script>alert(1)")


def test_next_steps_unparseable_reply_shows_friendly_message(client, fake_openai):
    goal = GoalFactory()
    fake_openai.reply("   ")
    client.force_login(goal.owner)

    response = client.post(action_url("goal-next-steps", goal))

    assert response.status_code == 200
    assertContains(response, UNREADABLE)


# Errors: friendly message, no 500, no key


@pytest.mark.parametrize("name", AI_ACTIONS)
def test_missing_api_key_shows_friendly_message_without_call(
    client, fake_openai, settings, name
):
    settings.OPENAI_API_KEY = ""
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.post(action_url(name, goal))

    assert response.status_code == 200
    assertTemplateUsed(response, "learning/goal_detail.html")
    assertContains(response, NOT_CONFIGURED)
    assert not fake_openai.called


@pytest.mark.parametrize("name", AI_ACTIONS)
@pytest.mark.parametrize(
    "make_error",
    [
        connection_error,
        timeout_error,
        auth_error,
        lambda: openai_status_error(RateLimitError, "Rate limit reached", 429),
    ],
    ids=["connection", "timeout", "auth", "rate-limit"],
)
def test_openai_error_shows_friendly_message(client, fake_openai, name, make_error):
    goal = GoalFactory()
    fake_openai.fail(make_error())
    client.force_login(goal.owner)

    response = client.post(action_url(name, goal))

    assert response.status_code == 200
    assertTemplateUsed(response, "learning/goal_detail.html")
    assertContains(response, UNAVAILABLE)


@pytest.mark.parametrize("name", AI_ACTIONS)
def test_error_page_never_contains_api_key(client, fake_openai, settings, caplog, name):
    settings.OPENAI_API_KEY = "test-key-leak"
    fake_openai.fail(auth_error("Incorrect API key provided: test-key-leak"))
    goal = GoalFactory()
    client.force_login(goal.owner)

    with caplog.at_level(logging.DEBUG):
        response = client.post(action_url(name, goal))

    assertContains(response, UNAVAILABLE)
    assertNotContains(response, "test-key-leak")
    assert "test-key-leak" not in caplog.text
