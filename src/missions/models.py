from django.db import models
from django.db.models import Q
from django.utils import timezone


class Mission(models.Model):
    class Cadence(models.TextChoices):
        ONE_TIME = "one_time", "One time"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    created_by = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.PROTECT,
        related_name="created_missions",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    cadence = models.CharField(
        max_length=16,
        choices=Cadence.choices,
        default=Cadence.ONE_TIME,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title", "id"]

    def __str__(self):
        return self.title


class MissionAgeReward(models.Model):
    class AgeGroup(models.TextChoices):
        CHILD = "child", "Child"
        TEEN = "teen", "Teen"
        ADULT = "adult", "Adult"

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name="age_rewards",
    )
    age_group = models.CharField(max_length=16, choices=AgeGroup.choices)
    star_value = models.PositiveSmallIntegerField(default=1)
    astral_light_value = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["mission", "age_group"],
                name="unique_mission_age_reward",
            ),
            models.CheckConstraint(
                condition=Q(star_value__gte=0),
                name="mission_age_reward_star_value_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(astral_light_value__gte=0),
                name="mission_age_reward_astral_light_value_non_negative",
            ),
        ]
        ordering = ["mission__title", "age_group", "id"]

    def __str__(self):
        return f"{self.mission} reward for {self.get_age_group_display()}"


class MissionAssignment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    forger = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.CASCADE,
        related_name="mission_assignments",
    )
    assigned_by = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.PROTECT,
        related_name="assigned_missions",
        blank=True,
        null=True,
    )
    starts_on = models.DateField(default=timezone.localdate)
    ends_on = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["mission", "forger"],
                condition=Q(status="active"),
                name="unique_active_mission_assignment_per_forger",
            ),
        ]
        ordering = ["forger__display_name", "mission__title", "id"]

    def __str__(self):
        return f"{self.mission} assigned to {self.forger}"


class MissionCompletion(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    assignment = models.ForeignKey(
        MissionAssignment,
        on_delete=models.CASCADE,
        related_name="completions",
    )
    recorded_by = models.ForeignKey(
        "forgers.ForgerProfile",
        on_delete=models.PROTECT,
        related_name="recorded_mission_completions",
    )
    completed_at = models.DateTimeField(default=timezone.now)
    completed_on = models.DateField(editable=False)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.APPROVED,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "completed_on"],
                name="unique_mission_assignment_completion_per_day",
            ),
        ]
        ordering = ["-completed_at", "-id"]

    def __str__(self):
        return f"{self.assignment.forger} completed {self.assignment.mission}"

    def save(self, *args, **kwargs):
        if self.completed_at and not self.completed_on:
            self.completed_on = timezone.localdate(self.completed_at)
        super().save(*args, **kwargs)
