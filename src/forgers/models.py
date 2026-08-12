from django.conf import settings
from django.db import models


class ForgerProfile(models.Model):
    class AgeGroup(models.TextChoices):
        CHILD = "child", "Child"
        TEEN = "teen", "Teen"
        ADULT = "adult", "Adult"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="forger_profile",
    )
    display_name = models.CharField(max_length=80)
    age_group = models.CharField(
        max_length=16,
        choices=AgeGroup.choices,
        blank=True,
    )
    is_guardian = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name", "id"]

    def __str__(self):
        return self.display_name
