import re

import pytest
from django.apps import apps
from django.contrib import admin
from django.urls import reverse

from accounts.tests.factories import UserFactory
from tags.tests.factories import TagFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("model_label", ["accounts.Profile", "tags.Tag"])
def test_model_is_registered_in_admin(model_label):
    assert admin.site.is_registered(apps.get_model(model_label))


@pytest.mark.parametrize(
    "url_name", ["admin:accounts_profile_changelist", "admin:tags_tag_changelist"]
)
def test_admin_changelist_loads(admin_client, url_name):
    TagFactory(name="docker")

    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200


def _profile_post_data(profile, focus_areas):
    return {
        "user": profile.user.pk,
        "name": "Ada",
        "cohort": "",
        "focus_areas": [tag.pk for tag in focus_areas],
    }


def test_profile_admin_rejects_focus_area_of_another_user(admin_client):
    profile = UserFactory().profile
    own_tag = TagFactory(owner=profile.user)
    profile.focus_areas.set([own_tag])
    foreign_tag = TagFactory()

    response = admin_client.post(
        reverse("admin:accounts_profile_change", args=[profile.pk]),
        _profile_post_data(profile, [own_tag, foreign_tag]),
    )

    assert response.status_code == 200, "expected the form to re-render with errors"
    assert "focus_areas" in response.context["adminform"].form.errors
    profile.refresh_from_db()
    assert profile.name == ""
    assert list(profile.focus_areas.all()) == [own_tag]


def test_profile_admin_saves_own_focus_areas(admin_client):
    profile = UserFactory().profile
    own_tags = TagFactory.create_batch(2, owner=profile.user)

    response = admin_client.post(
        reverse("admin:accounts_profile_change", args=[profile.pk]),
        _profile_post_data(profile, own_tags),
    )

    assert response.status_code == 302
    profile.refresh_from_db()
    assert profile.name == "Ada"
    assert set(profile.focus_areas.all()) == set(own_tags)


def test_profile_admin_focus_areas_use_autocomplete(admin_client):
    profile = UserFactory().profile
    TagFactory(name="someone-elses-tag")

    response = admin_client.get(
        reverse("admin:accounts_profile_change", args=[profile.pk])
    )

    content = response.content.decode()
    select = re.search(r'<select[^>]*\bname="focus_areas"[^>]*>', content)
    assert select, "no <select name='focus_areas'> in the page"
    assert "admin-autocomplete" in select.group(0)
    assert "someone-elses-tag" not in content
