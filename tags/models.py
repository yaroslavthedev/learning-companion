from django.conf import settings
from django.db import models


class TagManager(models.Manager):
    def from_csv(self, owner, text: str) -> list["Tag"]:
        """Turn "Docker, python , docker" into the owner's tags (created if needed)."""
        names = dict.fromkeys(
            name for name in (part.strip().lower() for part in text.split(",")) if name
        )
        return [self.get_or_create(owner=owner, name=name)[0] for name in names]


class Tag(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tags"
    )
    name = models.CharField(max_length=50)

    objects = TagManager()

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"], name="unique_tag_per_owner"
            )
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super().save(*args, **kwargs)
