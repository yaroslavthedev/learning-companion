from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from learning.forms import GoalForm, LearningSessionForm
from learning.models import Goal, LearningSession


class OwnGoalMixin(LoginRequiredMixin):
    """Only the current user's goals exist for these views: others give 404."""

    model = Goal

    def get_queryset(self):
        return Goal.objects.for_user(self.request.user)


class GoalListView(OwnGoalMixin, ListView):
    def get_active_status(self):
        """The ?status= value if it's a real status, else "" (= All)."""
        status = self.request.GET.get("status")
        return status if status in Goal.Status.values else ""

    def get_queryset(self):
        return super().get_queryset().with_status(self.get_active_status())

    def get_context_data(self, **kwargs):
        active = self.get_active_status()
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
    def get_context_data(self, **kwargs):
        return super().get_context_data(
            sessions=self.object.sessions.prefetch_related("tags"), **kwargs
        )


class GoalCreateView(OwnGoalMixin, CreateView):
    form_class = GoalForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class GoalUpdateView(OwnGoalMixin, UpdateView):
    form_class = GoalForm


class GoalDeleteView(OwnGoalMixin, DeleteView):
    success_url = reverse_lazy("goal-list")


class OwnSessionMixin(LoginRequiredMixin):
    """Only sessions of the current user's goals exist here: others give 404."""

    model = LearningSession

    def get_queryset(self):
        return (
            LearningSession.objects.for_user(self.request.user)
            .select_related("goal")
            .prefetch_related("tags")
        )

    def get_success_url(self):
        return self.object.goal.get_absolute_url()


class SessionFormMixin(OwnSessionMixin):
    form_class = LearningSessionForm

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"user": self.request.user}


class SessionListView(OwnSessionMixin, ListView):
    pass


class SessionCreateView(SessionFormMixin, CreateView):
    def get_initial(self):
        """?goal=<pk> pre-selects that goal, but only one of the user's own."""
        initial = super().get_initial()
        goal_id = self.request.GET.get("goal", "")
        own_goals = Goal.objects.for_user(self.request.user)
        if goal_id.isdigit() and own_goals.filter(pk=goal_id).exists():
            initial["goal"] = int(goal_id)
        return initial


class SessionUpdateView(SessionFormMixin, UpdateView):
    pass


class SessionDeleteView(OwnSessionMixin, DeleteView):
    pass
