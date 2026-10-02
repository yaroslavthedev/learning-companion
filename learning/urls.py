from django.urls import path

from learning.views import (
    GoalCreateView,
    GoalDeleteView,
    GoalDetailView,
    GoalListView,
    GoalUpdateView,
    ResourceCreateView,
    ResourceDeleteView,
    SessionCreateView,
    SessionDeleteView,
    SessionListView,
    SessionUpdateView,
)

urlpatterns = [
    path("goals/", GoalListView.as_view(), name="goal-list"),
    path("goals/new/", GoalCreateView.as_view(), name="goal-create"),
    path("goals/<int:pk>/", GoalDetailView.as_view(), name="goal-detail"),
    path("goals/<int:pk>/edit/", GoalUpdateView.as_view(), name="goal-update"),
    path("goals/<int:pk>/delete/", GoalDeleteView.as_view(), name="goal-delete"),
    path(
        "goals/<int:goal_pk>/resources/",
        ResourceCreateView.as_view(),
        name="resource-create",
    ),
    path(
        "resources/<int:pk>/delete/",
        ResourceDeleteView.as_view(),
        name="resource-delete",
    ),
    path("sessions/", SessionListView.as_view(), name="session-list"),
    path("sessions/new/", SessionCreateView.as_view(), name="session-create"),
    path("sessions/<int:pk>/edit/", SessionUpdateView.as_view(), name="session-update"),
    path(
        "sessions/<int:pk>/delete/", SessionDeleteView.as_view(), name="session-delete"
    ),
]
