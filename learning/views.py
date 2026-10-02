from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from learning.forms import GoalForm
from learning.models import Goal


class OwnGoalMixin(LoginRequiredMixin):
    """Only the current user's goals exist for these views: others give 404."""

    model = Goal

    def get_queryset(self):
        return Goal.objects.for_user(self.request.user)


class GoalListView(OwnGoalMixin, ListView):
    def get_queryset(self):
        return super().get_queryset().with_status(self.request.GET.get("status"))

    def get_context_data(self, **kwargs):
        active = self.request.GET.get("status")
        if active not in Goal.Status.values:
            active = ""
        list_url = reverse("goal-list")
        filters = [("", "All", list_url)] + [
            (value, label, f"{list_url}?status={value}")
            for value, label in Goal.Status.choices
        ]
        return super().get_context_data(
            status_filters=[
                {"label": label, "url": url, "active": value == active}
                for value, label, url in filters
            ],
            **kwargs,
        )


class GoalDetailView(OwnGoalMixin, DetailView):
    pass


class GoalCreateView(OwnGoalMixin, CreateView):
    form_class = GoalForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("goal-detail", args=[self.object.pk])


class GoalUpdateView(OwnGoalMixin, UpdateView):
    form_class = GoalForm

    def get_success_url(self):
        return reverse("goal-detail", args=[self.object.pk])


class GoalDeleteView(OwnGoalMixin, DeleteView):
    success_url = reverse_lazy("goal-list")
