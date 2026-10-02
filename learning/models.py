from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone


class GoalQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(owner=user)

    def with_status(self, status):
        """Filter by status; an unknown or empty value leaves the queryset as is."""
        if status in Goal.Status.values:
            return self.filter(status=status)
        return self


class Goal(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GoalQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("goal-detail", args=[self.pk])

    def total_hours(self):
        """Sum of this goal's session durations, in hours (0 without sessions)."""
        minutes = self.sessions.aggregate(total=Sum("duration_minutes"))["total"]
        return (minutes or 0) / 60


class LearningSessionQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(goal__owner=user)


class LearningSession(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="sessions")
    date = models.DateField(default=timezone.localdate)
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    notes = models.TextField(blank=True)
    tags = models.ManyToManyField("tags.Tag", blank=True, related_name="sessions")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LearningSessionQuerySet.as_manager()

    class Meta:
        ordering = ["-date", "-created_at", "-pk"]

    def __str__(self):
        return f"{self.goal} · {self.date} · {self.duration_minutes} min"
