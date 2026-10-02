import pytest
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertNotContains,
    assertRedirects,
    assertTemplateUsed,
)

from accounts.tests.factories import UserFactory
from tags.tests.factories import TagFactory

pytestmark = pytest.mark.django_db


def make_user_with_profile(name, cohort, tag_names, **user_kwargs):
    user = UserFactory(**user_kwargs)
    profile = user.profile
    profile.name = name
    profile.cohort = cohort
    profile.save()
    profile.focus_areas.set(
        [TagFactory(owner=user, name=tag_name) for tag_name in tag_names]
    )
    return user


def focus_area_names(user):
    user.profile.refresh_from_db()
    return sorted(user.profile.focus_areas.values_list("name", flat=True))


def edit_profile(client, name="Alice Example", cohort="Cohort 42", focus_areas=""):
    return client.post(
        reverse("profile-edit"),
        {"name": name, "cohort": cohort, "focus_areas_text": focus_areas},
    )


# /profile/


def test_profile_page_requires_login(client):
    response = client.get(reverse("profile"))

    assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")


def test_profile_page_shows_own_name_cohort_and_focus_areas(client):
    alice = make_user_with_profile("Alice Example", "Cohort 42", ["docker", "python"])
    client.force_login(alice)

    response = client.get(reverse("profile"))

    assertTemplateUsed(response, "accounts/profile_detail.html")
    assertContains(response, "Alice Example")
    assertContains(response, "Cohort 42")
    assertContains(response, "docker")
    assertContains(response, "python")


def test_profile_page_does_not_show_other_users_data(client):
    alice = make_user_with_profile("Alice Example", "Cohort 42", ["docker"])
    make_user_with_profile("Bob Other", "Cohort 7", ["kubernetes"], username="bob")
    client.force_login(alice)

    response = client.get(reverse("profile"))

    assertNotContains(response, "Bob Other")
    assertNotContains(response, "Cohort 7")
    assertNotContains(response, "kubernetes")
    assertNotContains(response, "bob")


# No URL takes a profile / user id


def test_profile_url_with_id_returns_404(client):
    alice = UserFactory()
    client.force_login(UserFactory())

    # Hardcoded on purpose: these URLs must not exist, so reverse() can't build them.
    for path in [
        f"/profile/{alice.pk}/",
        f"/profile/{alice.profile.pk}/",
        f"/profile/{alice.pk}/edit/",
        f"/profile/edit/{alice.pk}/",
    ]:
        assert client.get(path).status_code == 404, path


def test_editing_own_profile_does_not_change_other_users_profile(client):
    alice = make_user_with_profile("Alice Example", "Cohort 42", ["docker"])
    bob = UserFactory()
    client.force_login(bob)

    edit_profile(client, name="Bob Builder", cohort="Cohort 7", focus_areas="rust")

    alice.profile.refresh_from_db()
    assert alice.profile.name == "Alice Example"
    assert alice.profile.cohort == "Cohort 42"
    assert focus_area_names(alice) == ["docker"]
    bob.profile.refresh_from_db()
    assert bob.profile.name == "Bob Builder"


# /profile/edit/


def test_profile_edit_requires_login(client):
    response = client.get(reverse("profile-edit"))

    assertRedirects(response, f"{reverse('login')}?next={reverse('profile-edit')}")


def test_profile_edit_form_prefills_focus_areas_as_text(client):
    alice = make_user_with_profile("Alice Example", "Cohort 42", ["python", "docker"])
    client.force_login(alice)

    response = client.get(reverse("profile-edit"))

    assertTemplateUsed(response, "accounts/profile_form.html")
    assertContains(response, 'value="docker, python"')
    assertContains(response, "csrfmiddlewaretoken")


def test_profile_edit_saves_name_cohort_and_focus_areas(client):
    alice = UserFactory()
    client.force_login(alice)

    response = edit_profile(
        client,
        name="Alice Example",
        cohort="Cohort 42",
        focus_areas="Docker, python , docker",
    )

    assertRedirects(response, reverse("profile"))
    alice.profile.refresh_from_db()
    assert alice.profile.name == "Alice Example"
    assert alice.profile.cohort == "Cohort 42"
    assert focus_area_names(alice) == ["docker", "python"]
    assert all(tag.owner == alice for tag in alice.profile.focus_areas.all())


def test_profile_edit_with_empty_focus_areas_clears_them(client):
    alice = make_user_with_profile("Alice Example", "Cohort 42", ["docker"])
    client.force_login(alice)

    edit_profile(client, focus_areas="")

    assert focus_area_names(alice) == []


def test_profile_edit_creates_own_tag_even_if_other_user_has_same_name(client):
    bob = make_user_with_profile("Bob Other", "Cohort 7", ["docker"])
    bob_tag = bob.profile.focus_areas.get()
    alice = UserFactory()
    client.force_login(alice)

    edit_profile(client, focus_areas="docker")

    alice_tag = alice.profile.focus_areas.get()
    assert alice_tag.owner == alice
    assert alice_tag.pk != bob_tag.pk
    assert focus_area_names(bob) == ["docker"]
