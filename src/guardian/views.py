from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from forge.services import assign_mission_to_forger
from forge.services import complete_mission_assignment
from forge.services import get_astral_light_total
from forge.services import get_star_balance
from forge.services import redeem_reward
from forge.services import reject_reward_redemption
from forge.services import request_reward_redemption
from forgers.models import ForgerProfile
from guardian.decorators import guardian_required
from guardian.forms import MissionAssignmentForm
from guardian.forms import RewardRedemptionForm
from missions.models import Mission
from missions.models import MissionAssignment
from missions.models import MissionCompletion
from rewards.models import RewardRedemption


@login_required
@guardian_required
def dashboard(request):
    forgers = list(ForgerProfile.objects.select_related("user"))
    active_assignments = list(
        MissionAssignment.objects.filter(
            status=MissionAssignment.Status.ACTIVE,
        ).select_related("forger", "mission", "assigned_by")
    )
    redemptions = list(_get_redemptions())
    pending_redemption_count = len(_get_pending_redemptions(redemptions))

    forger_cards = []

    for forger in forgers:
        forger_redemptions = [
            redemption for redemption in redemptions if redemption.forger_id == forger.id
        ]
        pending_redemptions = _get_pending_redemptions(forger_redemptions)
        forger_cards.append(
            {
                "forger": forger,
                "star_balance": get_star_balance(forger),
                "astral_light_total": get_astral_light_total(forger),
                "active_assignment_count": sum(
                    1
                    for assignment in active_assignments
                    if assignment.forger_id == forger.id
                ),
                "pending_redemption_count": len(pending_redemptions),
            }
        )

    return render(
        request,
        "guardian/dashboard.html",
        {
            "forger_cards": forger_cards,
            "active_assignment_count": len(active_assignments),
            "pending_redemption_count": pending_redemption_count,
            "request_forger": request.forger_profile,
            "uri_path": request.path,
        },
    )


@login_required
@guardian_required
def missions(request):
    active_assignments = list(
        MissionAssignment.objects.filter(
            status=MissionAssignment.Status.ACTIVE,
        ).select_related("forger", "mission", "assigned_by")
    )

    return render(
        request,
        "guardian/missions.html",
        {
            "forger_cards": _build_mission_cards(active_assignments),
            "active_assignment_count": len(active_assignments),
            "uri_path": request.path,
        },
    )


@login_required
@guardian_required
def rewards(request):
    redemptions = list(_get_redemptions())

    return render(
        request,
        "guardian/rewards.html",
        {
            "forger_cards": _build_reward_cards(redemptions),
            "pending_redemption_count": len(
                [
                    redemption
                    for redemption in redemptions
                    if redemption.status
                    in {
                        RewardRedemption.Status.REQUESTED,
                        RewardRedemption.Status.REDEEMED,
                    }
                ]
            ),
            "uri_path": request.path,
        },
    )


@login_required
@guardian_required
def assign_mission(request):
    form = MissionAssignmentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            assign_mission_to_forger(
                mission=form.cleaned_data["mission"],
                forger=form.cleaned_data["forger"],
                assigned_by=request.forger_profile,
                starts_on=form.cleaned_data["starts_on"],
                ends_on=form.cleaned_data["ends_on"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Mision asignada correctamente.")
            return redirect("guardian:missions")

    return render(
        request,
        "guardian/assign_mission.html",
        {
            "form": form,
            "uri_path": request.path,
        },
    )


@login_required
@guardian_required
def redeem_reward_view(request):
    form = RewardRedemptionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                redemption = request_reward_redemption(
                    reward=form.cleaned_data["reward"],
                    forger=form.cleaned_data["forger"],
                    requested_by=request.forger_profile,
                    notes=form.cleaned_data["notes"],
                )
                redeem_reward(
                    redemption=redemption,
                    approved_by=request.forger_profile,
                    fulfilled=form.cleaned_data["fulfilled"],
                    notes=form.cleaned_data["notes"],
                )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Recompensa canjeada correctamente.")
            return redirect("guardian:rewards")

    return render(
        request,
        "guardian/redeem_reward.html",
        {
            "form": form,
            "uri_path": request.path,
        },
    )


@login_required
@guardian_required
@require_POST
def complete_assignment(request, assignment_id):
    assignment = get_object_or_404(MissionAssignment, pk=assignment_id)

    try:
        complete_mission_assignment(
            assignment=assignment,
            recorded_by=request.forger_profile,
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, "Mision completada correctamente.")

    return redirect("guardian:missions")


@login_required
@guardian_required
@require_POST
def redeem_redemption(request, redemption_id):
    redemption = get_object_or_404(RewardRedemption, pk=redemption_id)

    try:
        redeem_reward(
            redemption=redemption,
            approved_by=request.forger_profile,
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, "Recompensa canjeada correctamente.")

    return redirect("guardian:rewards")


@login_required
@guardian_required
@require_POST
def reject_redemption(request, redemption_id):
    redemption = get_object_or_404(RewardRedemption, pk=redemption_id)

    try:
        reject_reward_redemption(
            redemption=redemption,
            approved_by=request.forger_profile,
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, "Recompensa rechazada.")

    return redirect("guardian:rewards")


@login_required
@guardian_required
@require_POST
def fulfill_redemption(request, redemption_id):
    redemption = get_object_or_404(RewardRedemption, pk=redemption_id)

    if redemption.status != RewardRedemption.Status.REDEEMED:
        messages.error(request, "Solo las recompensas canjeadas pueden entregarse.")
        return redirect("guardian:rewards")

    redemption.status = RewardRedemption.Status.FULFILLED
    redemption.fulfilled_at = timezone.now()
    redemption.save(update_fields=["status", "fulfilled_at", "updated_at"])
    messages.success(request, "Recompensa marcada como entregada.")

    return redirect("guardian:rewards")


def _is_assignment_completed_for_period(assignment, today):
    completions = MissionCompletion.objects.filter(assignment=assignment)

    if assignment.mission.cadence == assignment.mission.Cadence.ONE_TIME:
        return completions.exists()

    if assignment.mission.cadence == assignment.mission.Cadence.DAILY:
        return completions.filter(completed_on=today).exists()

    if assignment.mission.cadence == assignment.mission.Cadence.WEEKLY:
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return completions.filter(completed_on__range=(week_start, week_end)).exists()

    return False


def _get_redemptions():
    return RewardRedemption.objects.select_related(
        "forger",
        "reward",
        "requested_by",
        "approved_by",
    ).order_by("-requested_at", "-id")


def _get_pending_redemptions(redemptions):
    return [
        redemption
        for redemption in redemptions
        if redemption.status
        in {
            RewardRedemption.Status.REQUESTED,
            RewardRedemption.Status.REDEEMED,
        }
    ]


def _build_mission_cards(active_assignments):
    today = timezone.localdate()
    forgers = list(ForgerProfile.objects.select_related("user"))
    assignment_rows = [
        {
            "assignment": assignment,
            "is_completed_for_period": _is_assignment_completed_for_period(
                assignment,
                today,
            ),
        }
        for assignment in active_assignments
    ]

    mission_cards = []

    for forger in forgers:
        forger_assignment_rows = [
            row for row in assignment_rows if row["assignment"].forger_id == forger.id
        ]
        mission_cards.append(
            {
                "forger": forger,
                "active_assignment_count": len(forger_assignment_rows),
                "assignment_groups": _group_assignment_rows_by_cadence(
                    forger_assignment_rows
                ),
            }
        )

    return mission_cards


def _build_reward_cards(redemptions):
    forgers = list(ForgerProfile.objects.select_related("user"))

    reward_cards = []

    for forger in forgers:
        forger_redemptions = [
            redemption for redemption in redemptions if redemption.forger_id == forger.id
        ]
        reward_cards.append(
            {
                "forger": forger,
                "pending_redemptions": _get_pending_redemptions(forger_redemptions),
                "recent_redemptions": forger_redemptions[:10],
            }
        )

    return reward_cards


def _group_assignment_rows_by_cadence(assignment_rows):
    cadence_groups = [
        (Mission.Cadence.DAILY, "Diarias"),
        (Mission.Cadence.WEEKLY, "Semanales"),
        (Mission.Cadence.ONE_TIME, "Unicas"),
    ]

    return [
        {
            "cadence": cadence,
            "label": label,
            "assignments": [
                row
                for row in assignment_rows
                if row["assignment"].mission.cadence == cadence
            ],
        }
        for cadence, label in cadence_groups
    ]
