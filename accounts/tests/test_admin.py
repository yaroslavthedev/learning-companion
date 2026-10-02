import pytest
from django.apps import apps
from django.contrib import admin
from django.urls import reverse

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
