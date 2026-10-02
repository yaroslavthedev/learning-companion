from django.conf import settings
from django.core.validators import MinValueValidator, URLValidator
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

    def resources_by_kind(self):
        """[(heading, resources), ...] in Resource.Kind order; empty kinds left out."""
        resources = list(self.resources.all())
        groups = []
        for kind, label in Resource.Kind.choices:
            of_kind = [resource for resource in resources if resource.kind == kind]
            if of_kind:
                groups.append((f"{label}s", of_kind))
        return groups


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


class ResourceQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(goal__owner=user)


class Resource(models.Model):
    class Kind(models.TextChoices):
        ARTICLE = "article", "Article"
        VIDEO = "video", "Video"
        REPO = "repo", "Repo"
        DOC = "doc", "Doc"

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="resources")
    url = models.URLField(
        "URL", max_length=500, validators=[URLValidator(schemes=["http", "https"])]
    )
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.ARTICLE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ResourceQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title
