import pytest
from django.contrib import admin
from django.urls import reverse

from learning.models import LearningSession
from learning.tests.factories import GoalFactory
from learning.tests.session_factories import LearningSessionFactory

pytestmark = pytest.mark.django_db


def test_session_registered_in_admin():
    assert admin.site.is_registered(LearningSession)


def test_session_admin_changelist_loads(admin_client):
    LearningSessionFactory(goal=GoalFactory(title="Learn Django"))

    response = admin_client.get(reverse("admin:learning_learningsession_changelist"))

    assert response.status_code == 200
    assert "Learn Django" in response.content.decode()
