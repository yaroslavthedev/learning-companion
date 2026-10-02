from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Meta(AbstractUser.Meta):
        ordering = ["username"]

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    name = models.CharField(max_length=100, blank=True)
    cohort = models.CharField(max_length=100, blank=True)
    focus_areas = models.ManyToManyField("tags.Tag", blank=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return self.user.username
