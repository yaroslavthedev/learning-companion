from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import Profile, User

admin.site.register(User, UserAdmin)


class ProfileAdminForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["user", "name", "cohort", "focus_areas"]

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        focus_areas = cleaned_data.get("focus_areas")
        if user and focus_areas and any(t.owner_id != user.pk for t in focus_areas):
            self.add_error("focus_areas", f"Focus areas must belong to {user}.")
        return cleaned_data


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm
    list_display = ["user", "name", "cohort"]
    search_fields = ["user__username", "name", "cohort"]
    autocomplete_fields = ["focus_areas"]
