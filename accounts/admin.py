from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import Profile, User

admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "name", "cohort"]
    search_fields = ["user__username", "name", "cohort"]
    filter_horizontal = ["focus_areas"]
