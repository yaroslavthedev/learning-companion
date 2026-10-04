from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from dashboard.services import goals_per_status, hours_per_tag, hours_per_week


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        statuses = goals_per_status(user)
        context["has_data"] = any(row["count"] for row in statuses)
        if context["has_data"]:
            context["goals_per_status"] = statuses
            context["hours_per_tag"] = hours_per_tag(user)
            context["hours_per_week"] = hours_per_week(user)
        return context
