from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import Profile, User
from tags.models import Tag


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User


class ProfileForm(forms.ModelForm):
    focus_areas_text = forms.CharField(
        label="Focus areas",
        required=False,
        help_text="Comma-separated, e.g. docker, python",
    )

    class Meta:
        model = Profile
        fields = ["name", "cohort"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["focus_areas_text"] = ", ".join(
            tag.name for tag in self.instance.focus_areas.all()
        )

    def save(self, commit=True):
        profile = super().save(commit=commit)
        tags = Tag.objects.from_csv(profile.user, self.cleaned_data["focus_areas_text"])
        profile.focus_areas.set(tags)
        return profile
