from django.contrib import admin

from tags.models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "owner"]
    list_filter = ["owner"]
    search_fields = ["name", "owner__username"]
