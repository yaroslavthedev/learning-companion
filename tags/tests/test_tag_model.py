import pytest
from django.db import IntegrityError, transaction

from accounts.tests.factories import UserFactory
from tags.models import Tag
from tags.tests.factories import TagFactory

pytestmark = pytest.mark.django_db


def tag_names(tags):
    return sorted(tag.name for tag in tags)


def test_tag_str_is_its_name():
    tag = TagFactory(name="docker")

    assert str(tag) == "docker"


def test_tag_name_is_stored_trimmed_and_lowercase():
    tag = TagFactory(name="  Docker ")

    tag.refresh_from_db()
    assert tag.name == "docker"


def test_two_users_can_have_same_tag_name():
    alice_tag = TagFactory(name="docker")
    bob_tag = TagFactory(name="docker")

    assert alice_tag.owner != bob_tag.owner
    assert alice_tag.name == bob_tag.name == "docker"


def test_same_owner_cannot_have_duplicate_tag():
    user = UserFactory()
    TagFactory(owner=user, name="docker")

    with pytest.raises(IntegrityError), transaction.atomic():
        TagFactory(owner=user, name="Docker")


def test_from_csv_trims_lowercases_and_dedupes():
    user = UserFactory()

    tags = Tag.objects.from_csv(user, "Docker, python , docker")

    assert tag_names(tags) == ["docker", "python"]
    assert all(tag.owner == user for tag in tags)
    assert Tag.objects.filter(owner=user).count() == 2


def test_from_csv_skips_empty_items():
    user = UserFactory()

    tags = Tag.objects.from_csv(user, "docker,, ,python,")

    assert tag_names(tags) == ["docker", "python"]


def test_from_csv_of_empty_text_returns_no_tags():
    user = UserFactory()

    assert list(Tag.objects.from_csv(user, "  ")) == []


def test_from_csv_reuses_existing_tag():
    user = UserFactory()
    existing = TagFactory(owner=user, name="docker")

    tags = Tag.objects.from_csv(user, "Docker")

    assert [tag.pk for tag in tags] == [existing.pk]
    assert Tag.objects.filter(owner=user).count() == 1


def test_from_csv_does_not_reuse_other_users_tag():
    user = UserFactory()
    other_tag = TagFactory(name="docker")

    tags = Tag.objects.from_csv(user, "docker")

    assert len(tags) == 1
    assert tags[0].pk != other_tag.pk
    assert tags[0].owner == user
