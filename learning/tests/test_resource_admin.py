import pytest
from django.contrib import admin
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from learning.models import Resource
from learning.tests.factories import GoalFactory, ResourceFactory

pytestmark = pytest.mark.django_db


def test_resource_registered_in_admin():
    assert admin.site.is_registered(Resource)


def test_resource_admin_changelist_loads(admin_client):
    ResourceFactory(title="Django docs", goal=GoalFactory(title="Learn Django"))

    response = admin_client.get(reverse("admin:learning_resource_changelist"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Django docs" in content
    assert "Learn Django" in content


def test_resource_admin_changelist_query_count_does_not_grow(admin_client):
    url = reverse("admin:learning_resource_changelist")

    def count_queries():
        with CaptureQueriesContext(connection) as queries:
            admin_client.get(url)
        return len(queries)

    ResourceFactory()
    one = count_queries()
    ResourceFactory.create_batch(3)

    assert count_queries() == one


def test_resource_admin_goal_uses_autocomplete_not_a_full_picker(admin_client):
    GoalFactory(title="Someone else's goal")

    response = admin_client.get(reverse("admin:learning_resource_add"))

    content = response.content.decode()
    assert "admin-autocomplete" in content
    assert "Someone else&#x27;s goal" not in content
