from django.urls import path

from learning.views import (
    GoalCreateView,
    GoalDeleteView,
    GoalDetailView,
    GoalListView,
    GoalUpdateView,
)

urlpatterns = [
    path("goals/", GoalListView.as_view(), name="goal-list"),
    path("goals/new/", GoalCreateView.as_view(), name="goal-create"),
    path("goals/<int:pk>/", GoalDetailView.as_view(), name="goal-detail"),
    path("goals/<int:pk>/edit/", GoalUpdateView.as_view(), name="goal-update"),
    path("goals/<int:pk>/delete/", GoalDeleteView.as_view(), name="goal-delete"),
]
