import pytest
from django.core.exceptions import ValidationError

from accounts.tests.factories import UserFactory
from learning.models import Resource
from learning.tests.factories import GoalFactory, ResourceFactory

pytestmark = pytest.mark.django_db


def test_resource_kind_defaults_to_article():
    resource = Resource.objects.create(
        goal=GoalFactory(), title="Docs", url="https://example.com"
    )

    assert resource.kind == Resource.Kind.ARTICLE


def test_resource_kinds_are_article_video_repo_doc():
    assert Resource.Kind.values == ["article", "video", "repo", "doc"]


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "ftp://example.com/file", "example.com"]
)
def test_resource_model_rejects_non_http_url(url):
    resource = ResourceFactory.build(goal=GoalFactory(), url=url)

    with pytest.raises(ValidationError) as error:
        resource.full_clean()

    assert "url" in error.value.message_dict


def test_resource_model_accepts_long_https_url():
    url = "https://example.com/watch?v=" + "x" * 450
    resource = ResourceFactory.build(goal=GoalFactory(), url=url)

    resource.full_clean()


def test_resource_for_user_returns_only_own_resources():
    alice = UserFactory()
    own = ResourceFactory(goal=GoalFactory(owner=alice))
    ResourceFactory()

    assert list(Resource.objects.for_user(alice)) == [own]


def test_deleting_goal_deletes_its_resources():
    resource = ResourceFactory()

    resource.goal.delete()

    assert not Resource.objects.filter(pk=resource.pk).exists()


def test_resources_by_kind_groups_in_kind_order_and_skips_empty():
    goal = GoalFactory()
    ResourceFactory(goal=goal, kind="doc", title="Django docs")
    ResourceFactory(goal=goal, kind="article", title="Old article")
    ResourceFactory(goal=goal, kind="video", title="Talk")
    ResourceFactory(goal=goal, kind="article", title="New article")
    ResourceFactory(kind="repo", title="Other goal repo")

    groups = goal.resources_by_kind()

    assert [
        (heading, [resource.title for resource in resources])
        for heading, resources in groups
    ] == [
        ("Articles", ["New article", "Old article"]),
        ("Videos", ["Talk"]),
        ("Docs", ["Django docs"]),
    ]


def test_resources_by_kind_without_resources_is_empty():
    assert GoalFactory().resources_by_kind() == []
