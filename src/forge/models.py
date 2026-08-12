from django.db import models
from django.db.models import Q
from django.utils import timezone


class ForgeEvent(models.Model):
    class EventType(models.TextChoices):
        MISSION_COMPLETED = "mission_completed", "Mission completed"
        REWARD_REDEEMED = "reward_redeemed", "Reward redeemed"
        MANUAL_ADJUSTMENT = "manual_adjustment", "Manual adjustment"

    forger = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.CASCADE,
        related_name="forge_events",
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    mission_completion = models.OneToOneField(
        "missions.MissionCompletion",
        on_delete=models.PROTECT,
        related_name="forge_event",
        blank=True,
        null=True,
    )
    occurred_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]

    def __str__(self):
        return f"{self.forger} - {self.get_event_type_display()}"


class StarLedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        EARNED = "earned", "Earned"
        SPENT = "spent", "Spent"
        ADJUSTMENT = "adjustment", "Adjustment"

    forger = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.CASCADE,
        related_name="star_ledger_entries",
    )
    forge_event = models.ForeignKey(
        ForgeEvent,
        on_delete=models.PROTECT,
        related_name="star_entries",
    )
    entry_type = models.CharField(max_length=16, choices=EntryType.choices)
    amount = models.SmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(amount=0),
                name="star_ledger_amount_not_zero",
            ),
        ]
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.forger} {self.amount:+d} stars"


class AstralLightLedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        EARNED = "earned", "Earned"
        ADJUSTMENT = "adjustment", "Adjustment"

    forger = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.CASCADE,
        related_name="astral_light_ledger_entries",
    )
    forge_event = models.ForeignKey(
        ForgeEvent,
        on_delete=models.PROTECT,
        related_name="astral_light_entries",
    )
    entry_type = models.CharField(max_length=16, choices=EntryType.choices)
    amount = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="astral_light_ledger_amount_positive",
            ),
        ]
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.forger} +{self.amount} Astral Light"
