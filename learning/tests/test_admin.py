import pytest
from django.contrib import admin
from django.urls import reverse

from learning.models import Goal
from learning.tests.factories import GoalFactory

pytestmark = pytest.mark.django_db


def test_goal_registered_in_admin():
    assert admin.site.is_registered(Goal)


def test_goal_admin_changelist_loads(admin_client):
    GoalFactory(title="Learn Django")

    response = admin_client.get(reverse("admin:learning_goal_changelist"))

    assert response.status_code == 200
    assert "Learn Django" in response.content.decode()
