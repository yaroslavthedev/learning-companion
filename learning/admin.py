from django.contrib import admin
from django.db import models

from learning.models import Goal, LearningSession, Resource


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "status", "created_at", "updated_at"]
    list_filter = ["status", "owner"]
    search_fields = ["title", "owner__username"]


@admin.register(LearningSession)
class LearningSessionAdmin(admin.ModelAdmin):
    list_display = ["goal", "date", "duration_minutes", "created_at"]
    list_filter = ["date", "goal__owner"]
    search_fields = ["goal__title", "notes", "goal__owner__username"]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "goal", "created_at"]
    list_filter = ["kind", "goal__owner"]
    list_select_related = ["goal__owner"]
    search_fields = ["title", "url", "goal__title", "goal__owner__username"]
    autocomplete_fields = ["goal"]
    formfield_overrides = {models.URLField: {"assume_scheme": "https"}}
