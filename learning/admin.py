from django.contrib import admin

from learning.models import Goal, LearningSession


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
