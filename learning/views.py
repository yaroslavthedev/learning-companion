from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from learning.forms import GoalForm, LearningSessionForm, ResourceForm
from learning.models import Goal, LearningSession, Resource


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


def goal_detail_context(goal, resource_form=None):
    """What goal_detail.html shows; the resource create view reuses it on errors."""
    return {
        "goal": goal,
        "sessions": goal.sessions.prefetch_related("tags"),
        "resource_groups": goal.resources_by_kind(),
        "resource_form": resource_form or ResourceForm(),
    }


class GoalDetailView(OwnGoalMixin, DetailView):
    def get_context_data(self, **kwargs):
        return super().get_context_data(**goal_detail_context(self.object), **kwargs)


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


class ResourceCreateView(LoginRequiredMixin, CreateView):
    """POST-only form on goal detail; errors re-render the goal page."""

    form_class = ResourceForm
    template_name = "learning/goal_detail.html"
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.goal = get_object_or_404(
            Goal.objects.for_user(request.user), pk=kwargs["goal_pk"]
        )
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.goal = self.goal
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context | goal_detail_context(self.goal, resource_form=context["form"])

    def get_success_url(self):
        return self.goal.get_absolute_url()


class ResourceDeleteView(LoginRequiredMixin, DeleteView):
    model = Resource

    def get_queryset(self):
        return Resource.objects.for_user(self.request.user).select_related("goal")

    def get_success_url(self):
        return self.object.goal.get_absolute_url()
