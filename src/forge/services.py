from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from forge.models import AstralLightLedgerEntry
from forge.models import ForgeEvent
from forge.models import StarLedgerEntry
from families.models import Family
from families.models import FamilyMembership
from forgers.models import ForgerProfile
from missions.models import Mission
from missions.models import MissionAgeReward
from missions.models import MissionAssignment
from missions.models import MissionCompletion
from rewards.models import Reward
from rewards.models import RewardRedemption


def get_star_balance(forger):
    return (
        StarLedgerEntry.objects.filter(forger=forger).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )


def get_astral_light_total(forger):
    return (
        AstralLightLedgerEntry.objects.filter(forger=forger).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )


def is_assignment_completed_for_period(assignment, today=None):
    today = today or timezone.localdate()
    completions = MissionCompletion.objects.filter(assignment=assignment)

    if assignment.mission.cadence == Mission.Cadence.ONE_TIME:
        return completions.exists()

    if assignment.mission.cadence == Mission.Cadence.DAILY:
        return completions.filter(completed_on=today).exists()

    if assignment.mission.cadence == Mission.Cadence.WEEKLY:
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return completions.filter(completed_on__range=(week_start, week_end)).exists()

    return False


@transaction.atomic
def get_or_create_app_family(created_by, name="Familia"):
    family = Family.objects.order_by("id").first()

    if family:
        return family

    return Family.objects.create(
        name=name,
        created_by=created_by,
    )


@transaction.atomic
def create_family_forger(
    username,
    password,
    display_name,
    age_group="",
    is_guardian=False,
    created_by=None,
):
    user = get_user_model().objects.create_user(
        username=username,
        password=password,
    )
    forger = ForgerProfile.objects.create(
        user=user,
        display_name=display_name,
        age_group=age_group,
        is_guardian=is_guardian,
    )
    family = get_or_create_app_family(created_by=created_by or forger)
    FamilyMembership.objects.create(
        family=family,
        forger=forger,
        role=(
            FamilyMembership.Role.GUARDIAN
            if is_guardian
            else FamilyMembership.Role.MEMBER
        ),
    )

    return forger


@transaction.atomic
def delete_family_forger(forger, deleted_by):
    if deleted_by and forger.pk == deleted_by.pk:
        raise ValidationError("You cannot delete your own guardian profile.")

    replacement_forger = deleted_by
    user = forger.user

    Mission.objects.filter(created_by=forger).update(created_by=None)
    Reward.objects.filter(created_by=forger).update(created_by=None)
    MissionAssignment.objects.filter(assigned_by=forger).update(assigned_by=None)
    RewardRedemption.objects.filter(approved_by=forger).update(approved_by=None)

    if replacement_forger:
        Family.objects.filter(created_by=forger).update(created_by=replacement_forger)
        MissionCompletion.objects.filter(recorded_by=forger).exclude(
            assignment__forger=forger
        ).update(recorded_by=replacement_forger)
        RewardRedemption.objects.filter(requested_by=forger).exclude(
            forger=forger
        ).update(requested_by=replacement_forger)

    StarLedgerEntry.objects.filter(forger=forger).delete()
    AstralLightLedgerEntry.objects.filter(forger=forger).delete()
    RewardRedemption.objects.filter(forger=forger).delete()
    ForgeEvent.objects.filter(forger=forger).delete()
    MissionAssignment.objects.filter(forger=forger).delete()
    FamilyMembership.objects.filter(forger=forger).delete()
    user.delete()


@transaction.atomic
def assign_mission_to_forger(
    mission,
    forger,
    assigned_by,
    starts_on=None,
    ends_on=None,
):
    mission = Mission.objects.select_for_update().get(pk=mission.pk)
    starts_on = starts_on or timezone.localdate()

    _validate_mission_can_be_assigned(
        mission=mission,
        forger=forger,
        assigned_by=assigned_by,
        starts_on=starts_on,
        ends_on=ends_on,
    )

    return MissionAssignment.objects.create(
        mission=mission,
        forger=forger,
        assigned_by=assigned_by,
        starts_on=starts_on,
        ends_on=ends_on,
    )


@transaction.atomic
def complete_mission_assignment(
    assignment,
    recorded_by,
    completed_at=None,
    notes="",
):
    completed_at = completed_at or timezone.now()
    completed_on = timezone.localdate(completed_at)
    assignment = (
        MissionAssignment.objects.select_for_update()
        .select_related("forger", "mission")
        .get(pk=assignment.pk)
    )

    _validate_assignment_can_be_completed(assignment, completed_on)
    age_reward = _get_active_age_reward(assignment)
    _validate_assignment_cadence(assignment, completed_on)

    completion = MissionCompletion.objects.create(
        assignment=assignment,
        recorded_by=recorded_by,
        completed_at=completed_at,
        notes=notes,
    )
    forge_event = ForgeEvent.objects.create(
        forger=assignment.forger,
        event_type=ForgeEvent.EventType.MISSION_COMPLETED,
        mission_completion=completion,
        occurred_at=completed_at,
    )

    if age_reward.star_value:
        StarLedgerEntry.objects.create(
            forger=assignment.forger,
            forge_event=forge_event,
            entry_type=StarLedgerEntry.EntryType.EARNED,
            amount=age_reward.star_value,
        )

    if age_reward.astral_light_value:
        AstralLightLedgerEntry.objects.create(
            forger=assignment.forger,
            forge_event=forge_event,
            entry_type=AstralLightLedgerEntry.EntryType.EARNED,
            amount=age_reward.astral_light_value,
        )

    return completion


@transaction.atomic
def request_reward_redemption(reward, forger, requested_by, notes=""):
    reward = Reward.objects.select_for_update().get(pk=reward.pk)

    if reward.status != Reward.Status.ACTIVE:
        raise ValidationError("This reward is not active.")

    return RewardRedemption.objects.create(
        reward=reward,
        forger=forger,
        requested_by=requested_by,
        star_cost=reward.star_cost,
        notes=notes,
    )


@transaction.atomic
def redeem_reward(redemption, approved_by=None, fulfilled=False, notes=""):
    redemption = (
        RewardRedemption.objects.select_for_update()
        .select_related("forger", "reward")
        .get(pk=redemption.pk)
    )

    if redemption.forge_event_id:
        raise ValidationError("This reward redemption has already spent stars.")

    if redemption.status != RewardRedemption.Status.REQUESTED:
        raise ValidationError("This reward redemption cannot be redeemed.")

    if get_star_balance(redemption.forger) < redemption.star_cost:
        raise ValidationError("This forger does not have enough stars.")

    occurred_at = timezone.now()
    forge_event = ForgeEvent.objects.create(
        forger=redemption.forger,
        event_type=ForgeEvent.EventType.REWARD_REDEEMED,
        occurred_at=occurred_at,
        notes=notes,
    )
    StarLedgerEntry.objects.create(
        forger=redemption.forger,
        forge_event=forge_event,
        entry_type=StarLedgerEntry.EntryType.SPENT,
        amount=-redemption.star_cost,
    )

    redemption.forge_event = forge_event
    redemption.approved_by = approved_by or redemption.approved_by
    redemption.resolved_at = redemption.resolved_at or occurred_at
    redemption.status = (
        RewardRedemption.Status.FULFILLED
        if fulfilled
        else RewardRedemption.Status.REDEEMED
    )
    if fulfilled:
        redemption.fulfilled_at = redemption.fulfilled_at or occurred_at
    redemption.save(
        update_fields=[
            "forge_event",
            "approved_by",
            "resolved_at",
            "status",
            "fulfilled_at",
            "updated_at",
        ]
    )

    return redemption


@transaction.atomic
def reject_reward_redemption(redemption, approved_by=None, notes=""):
    redemption = RewardRedemption.objects.select_for_update().get(pk=redemption.pk)

    if redemption.status != RewardRedemption.Status.REQUESTED:
        raise ValidationError("This reward redemption cannot be rejected.")

    redemption.approved_by = approved_by or redemption.approved_by
    redemption.resolved_at = redemption.resolved_at or timezone.now()
    if notes:
        redemption.notes = notes
    redemption.status = RewardRedemption.Status.REJECTED
    redemption.save(
        update_fields=[
            "approved_by",
            "resolved_at",
            "notes",
            "status",
            "updated_at",
        ]
    )

    return redemption


def _validate_assignment_can_be_completed(assignment, completed_on):
    if assignment.status != MissionAssignment.Status.ACTIVE:
        raise ValidationError("This mission assignment is not active.")

    if assignment.mission.status != Mission.Status.ACTIVE:
        raise ValidationError("This mission is not active.")

    if completed_on < assignment.starts_on:
        raise ValidationError("This mission assignment has not started yet.")

    if assignment.ends_on and completed_on > assignment.ends_on:
        raise ValidationError("This mission assignment has ended.")


def _validate_mission_can_be_assigned(mission, forger, assigned_by, starts_on, ends_on):
    if mission.status != Mission.Status.ACTIVE:
        raise ValidationError("This mission is not active.")

    if not assigned_by or not assigned_by.is_guardian:
        raise ValidationError("Only guardians can assign missions.")

    if not forger.age_group:
        raise ValidationError("This forger does not have an age group.")

    if ends_on and ends_on < starts_on:
        raise ValidationError("The assignment end date cannot be before start date.")

    if MissionAssignment.objects.filter(
        mission=mission,
        forger=forger,
        status=MissionAssignment.Status.ACTIVE,
    ).exists():
        raise ValidationError("This forger already has this mission assigned.")

    if not MissionAgeReward.objects.filter(
        mission=mission,
        age_group=forger.age_group,
        is_active=True,
    ).exists():
        raise ValidationError(
            "This mission is not available for this forger's age group."
        )


def _validate_assignment_cadence(assignment, completed_on):
    if assignment.mission.cadence == Mission.Cadence.ONE_TIME:
        if MissionCompletion.objects.filter(assignment=assignment).exists():
            raise ValidationError("This one-time mission is already completed.")
        return

    if assignment.mission.cadence == Mission.Cadence.DAILY:
        if MissionCompletion.objects.filter(
            assignment=assignment,
            completed_on=completed_on,
        ).exists():
            raise ValidationError(
                "This daily mission assignment is already completed today."
            )
        return

    if assignment.mission.cadence == Mission.Cadence.WEEKLY:
        week_start = completed_on - timedelta(days=completed_on.weekday())
        week_end = week_start + timedelta(days=6)

        if MissionCompletion.objects.filter(
            assignment=assignment,
            completed_on__range=(week_start, week_end),
        ).exists():
            raise ValidationError(
                "This weekly mission assignment is already completed this week."
            )
        return

    raise ValidationError("This mission cadence is not supported.")


def _get_active_age_reward(assignment):
    age_group = assignment.forger.age_group

    if not age_group:
        raise ValidationError("This forger does not have an age group.")

    try:
        return MissionAgeReward.objects.get(
            mission=assignment.mission,
            age_group=age_group,
            is_active=True,
        )
    except MissionAgeReward.DoesNotExist as exc:
        raise ValidationError(
            "This mission is not available for this forger's age group."
        ) from exc
