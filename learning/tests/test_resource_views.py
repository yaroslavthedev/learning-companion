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
from learning.models import Resource
from learning.tests.factories import GoalFactory, ResourceFactory

pytestmark = pytest.mark.django_db


def create_url(goal):
    return reverse("resource-create", args=[goal.pk])


def delete_url(resource):
    return reverse("resource-delete", args=[resource.pk])


def goal_url(goal):
    return reverse("goal-detail", args=[goal.pk])


def resource_data(**overrides):
    return {
        "title": "Django docs",
        "url": "https://docs.djangoproject.com/",
        "kind": "doc",
    } | overrides


# Login required


def test_create_redirects_anonymous_to_login(client):
    url = create_url(GoalFactory())

    response = client.post(url, resource_data())

    assertRedirects(response, f"{reverse('login')}?next={url}")
    assert not Resource.objects.exists()


def test_delete_redirects_anonymous_to_login(client):
    url = delete_url(ResourceFactory())

    response = client.get(url)

    assertRedirects(response, f"{reverse('login')}?next={url}")


# Add form on goal detail


def test_goal_detail_shows_add_resource_form(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.get(goal_url(goal))

    assertContains(response, f'action="{create_url(goal)}"')
    assertContains(response, 'name="title"')
    assertContains(response, 'name="url"')
    assertContains(response, 'name="kind"')
    assertContains(response, "csrfmiddlewaretoken")


# POST /goals/<pk>/resources/


def test_create_attaches_resource_to_goal_and_redirects_to_goal(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.post(create_url(goal), resource_data())

    assertRedirects(response, goal_url(goal))
    resource = Resource.objects.get()
    assert resource.goal == goal
    assert resource.title == "Django docs"
    assert resource.url == "https://docs.djangoproject.com/"
    assert resource.kind == "doc"


@pytest.mark.parametrize(
    "url", ["http://example.com", "https://example.com/watch?v=abc&t=10"]
)
def test_create_accepts_http_and_https(client, url):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.post(create_url(goal), resource_data(url=url))

    assertRedirects(response, goal_url(goal))
    assert Resource.objects.get().url == url


def test_create_get_not_allowed(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.get(create_url(goal))

    assert response.status_code == 405


def test_create_with_empty_title_shows_error_on_goal_page(client):
    goal = GoalFactory(title="Learn Django")
    client.force_login(goal.owner)

    response = client.post(create_url(goal), resource_data(title=""))

    assert response.status_code == 200
    assertTemplateUsed(response, "learning/goal_detail.html")
    assertContains(response, "Learn Django")
    assertFormError(
        response.context["resource_form"], "title", "This field is required."
    )
    assert not Resource.objects.exists()


def test_create_with_invalid_url_shows_error_on_goal_page(client):
    goal = GoalFactory(title="Learn Django")
    client.force_login(goal.owner)

    response = client.post(create_url(goal), resource_data(url="not a url"))

    assert response.status_code == 200
    assertTemplateUsed(response, "learning/goal_detail.html")
    assertContains(response, "Learn Django")
    assertContains(response, "Enter a valid URL.")
    assertFormError(response.context["resource_form"], "url", "Enter a valid URL.")
    assert not Resource.objects.exists()


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "ftp://example.com/file",
        "data:text/html,<script>alert(1)</script>",
    ],
)
def test_create_rejects_non_http_scheme(client, url):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.post(create_url(goal), resource_data(url=url))

    assert response.status_code == 200
    assertFormError(response.context["resource_form"], "url", "Enter a valid URL.")
    assert not Resource.objects.exists()


# Resources on goal detail


def test_goal_detail_shows_resource_groups_with_kind_badges(client):
    goal = GoalFactory()
    ResourceFactory(goal=goal, kind="article", title="ORM guide")
    ResourceFactory(goal=goal, kind="video", title="DjangoCon talk")
    ResourceFactory(goal=goal, kind="repo", title="django/django")
    ResourceFactory(goal=goal, kind="doc", title="Django docs")
    client.force_login(goal.owner)

    response = client.get(goal_url(goal))

    content = response.content.decode()
    headings = ["Articles", "Videos", "Repos", "Docs"]
    positions = [content.index(f"<h3>{heading}</h3>") for heading in headings]
    assert positions == sorted(positions)
    for badge in ["Article", "Video", "Repo", "Doc"]:
        assertContains(response, f"<mark>{badge}</mark>", html=True)
    for title in ["ORM guide", "DjangoCon talk", "django/django", "Django docs"]:
        assertContains(response, title)


def test_goal_detail_hides_empty_groups(client):
    goal = GoalFactory()
    ResourceFactory(goal=goal, kind="video")
    client.force_login(goal.owner)

    response = client.get(goal_url(goal))

    assertContains(response, "<h3>Videos</h3>", html=True)
    for heading in ["Articles", "Repos", "Docs"]:
        assertNotContains(response, f"<h3>{heading}</h3>", html=True)


def test_goal_detail_without_resources_shows_empty_message(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    response = client.get(goal_url(goal))

    assertContains(response, "No resources yet.")


def test_resource_link_opens_in_new_tab_with_noopener(client):
    resource = ResourceFactory(title="Django docs", url="https://docs.example.com/")
    client.force_login(resource.goal.owner)

    response = client.get(goal_url(resource.goal))

    assertContains(
        response,
        '<a href="https://docs.example.com/" target="_blank"'
        ' rel="noopener noreferrer">Django docs</a>',
        html=True,
    )


def test_goal_detail_shows_only_this_goals_resources(client):
    goal = GoalFactory()
    ResourceFactory(goal=goal, title="Mine on this goal")
    ResourceFactory(goal=GoalFactory(owner=goal.owner), title="Mine on another goal")
    ResourceFactory(title="Someone else's")
    client.force_login(goal.owner)

    response = client.get(goal_url(goal))

    assertContains(response, "Mine on this goal")
    assertNotContains(response, "Mine on another goal")
    assertNotContains(response, "Someone else")


def test_goal_detail_has_delete_link_for_each_resource(client):
    resource = ResourceFactory()
    client.force_login(resource.goal.owner)

    response = client.get(goal_url(resource.goal))

    assertContains(response, f'href="{delete_url(resource)}"')


def test_resource_title_is_html_escaped(client):
    resource = ResourceFactory(title="<script>alert(1)</script>")
    client.force_login(resource.goal.owner)

    response = client.get(goal_url(resource.goal))

    assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
    assertNotContains(response, "<script>alert(1)</script>")


def test_goal_detail_query_count_does_not_grow_with_resources(client):
    goal = GoalFactory()
    client.force_login(goal.owner)

    def count_queries():
        with CaptureQueriesContext(connection) as queries:
            client.get(goal_url(goal))
        return len(queries)

    ResourceFactory(goal=goal, kind="article")
    one = count_queries()
    for kind in ["article", "video", "repo", "doc"]:
        ResourceFactory.create_batch(2, goal=goal, kind=kind)

    assert count_queries() == one


# /resources/<pk>/delete/


def test_delete_get_shows_confirmation_and_keeps_resource(client):
    resource = ResourceFactory(title="Django docs")
    client.force_login(resource.goal.owner)

    response = client.get(delete_url(resource))

    assertTemplateUsed(response, "learning/resource_confirm_delete.html")
    assertContains(response, "Django docs")
    assertContains(response, "csrfmiddlewaretoken")
    assert Resource.objects.filter(pk=resource.pk).exists()


def test_delete_removes_resource_and_redirects_to_goal(client):
    resource = ResourceFactory()
    client.force_login(resource.goal.owner)

    response = client.post(delete_url(resource))

    assertRedirects(response, goal_url(resource.goal))
    assert not Resource.objects.filter(pk=resource.pk).exists()


# Another user's goal / resource


def test_other_user_gets_404_when_adding_resource_to_foreign_goal(client):
    alices_goal = GoalFactory()
    client.force_login(UserFactory())

    response = client.post(create_url(alices_goal), resource_data())

    assert response.status_code == 404
    assert not Resource.objects.exists()


@pytest.mark.parametrize("method", ["get", "post"])
def test_other_user_gets_404_on_resource_delete(client, method):
    resource = ResourceFactory()
    client.force_login(UserFactory())

    response = getattr(client, method)(delete_url(resource))

    assert response.status_code == 404
    assert Resource.objects.filter(pk=resource.pk).exists()
