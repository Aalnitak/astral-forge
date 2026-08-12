from django.db import models
from django.db.models import Q
from django.utils import timezone


class Reward(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    created_by = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.PROTECT,
        related_name="created_rewards",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    star_cost = models.PositiveSmallIntegerField()
    requires_approval = models.BooleanField(default=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(star_cost__gt=0),
                name="reward_star_cost_positive",
            ),
        ]
        ordering = ["title", "id"]

    def __str__(self):
        return self.title


class RewardRedemption(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELED = "canceled", "Canceled"

    reward = models.ForeignKey(
        Reward,
        on_delete=models.PROTECT,
        related_name="redemptions",
    )
    forger = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.CASCADE,
        related_name="reward_redemptions",
    )
    requested_by = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.PROTECT,
        related_name="requested_reward_redemptions",
    )
    approved_by = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.PROTECT,
        related_name="approved_reward_redemptions",
        blank=True,
        null=True,
    )
    forge_event = models.OneToOneField(
        "forge.ForgeEvent",
        on_delete=models.PROTECT,
        related_name="reward_redemption",
        blank=True,
        null=True,
    )
    star_cost = models.PositiveSmallIntegerField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.REQUESTED,
    )
    requested_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(blank=True, null=True)
    fulfilled_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(star_cost__gt=0),
                name="reward_redemption_star_cost_positive",
            ),
        ]
        ordering = ["-requested_at", "-id"]

    def __str__(self):
        return f"{self.forger} requested {self.reward}"

    def save(self, *args, **kwargs):
        if self.reward_id and not self.star_cost:
            self.star_cost = self.reward.star_cost
        super().save(*args, **kwargs)
