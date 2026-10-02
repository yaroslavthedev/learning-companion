from django import forms

from learning.models import Goal, LearningSession
from tags.models import Tag


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["title", "description", "status"]


class LearningSessionForm(forms.ModelForm):
    tags_text = forms.CharField(
        label="Tags",
        required=False,
        help_text="Comma-separated, e.g. docker, python",
    )

    class Meta:
        model = LearningSession
        fields = ["goal", "date", "duration_minutes", "notes"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["goal"].queryset = Goal.objects.for_user(user)
        if self.instance.pk:
            self.initial["tags_text"] = ", ".join(
                tag.name for tag in self.instance.tags.all()
            )

    def save(self, commit=True):
        session = super().save(commit=commit)
        tags = Tag.objects.from_csv(self.user, self.cleaned_data["tags_text"])
        session.tags.set(tags)
        return session
