from django.db import models


class Family(models.Model):
    name = models.CharField(max_length=120)
    created_by = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.PROTECT,
        related_name="created_families",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "families"
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class FamilyMembership(models.Model):
    class Role(models.TextChoices):
        GUARDIAN = "guardian", "Guardian"
        MEMBER = "member", "Member"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INVITED = "invited", "Invited"
        REMOVED = "removed", "Removed"

    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    forger = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.CASCADE,
        related_name="family_memberships",
    )
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["family", "forger"],
                name="unique_family_forger_membership",
            ),
        ]
        ordering = ["family__name", "forger__display_name", "id"]

    def __str__(self):
        return f"{self.forger} in {self.family}"
