from django.contrib import admin

from learning.models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "status", "created_at", "updated_at"]
    list_filter = ["status", "owner"]
    search_fields = ["title", "owner__username"]
