from django import forms
from django.contrib import admin
from django.db import models

from learning.models import Goal, LearningSession, Resource


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "status", "created_at", "updated_at"]
    list_filter = ["status", "owner"]
    search_fields = ["title", "owner__username"]


class LearningSessionAdminForm(forms.ModelForm):
    class Meta:
        model = LearningSession
        fields = ["goal", "date", "duration_minutes", "notes", "tags"]

    def clean(self):
        cleaned_data = super().clean()
        goal = cleaned_data.get("goal")
        tags = cleaned_data.get("tags")
        if goal and tags and any(tag.owner_id != goal.owner_id for tag in tags):
            self.add_error(
                "tags", f"Tags must belong to {goal.owner}, the owner of the goal."
            )
        return cleaned_data


@admin.register(LearningSession)
class LearningSessionAdmin(admin.ModelAdmin):
    form = LearningSessionAdminForm
    list_display = ["goal", "date", "duration_minutes", "created_at"]
    list_filter = ["date", "goal__owner"]
    search_fields = ["goal__title", "notes", "goal__owner__username"]
    autocomplete_fields = ["goal", "tags"]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "goal", "created_at"]
    list_filter = ["kind", "goal__owner"]
    list_select_related = ["goal__owner"]
    search_fields = ["title", "url", "goal__title", "goal__owner__username"]
    autocomplete_fields = ["goal"]
    formfield_overrides = {models.URLField: {"assume_scheme": "https"}}
