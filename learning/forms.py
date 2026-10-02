from django import forms

from learning.models import Goal


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["title", "description", "status"]
