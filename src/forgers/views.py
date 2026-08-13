from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from forge.services import complete_mission_assignment
from forge.services import get_astral_light_total
from forge.services import get_star_balance
from forge.services import is_assignment_completed_for_period
from forge.services import request_reward_redemption
from families.models import FamilyMembership
from forgers.models import ForgerProfile
from missions.models import Mission
from missions.models import MissionAssignment
from rewards.models import Reward
from rewards.models import RewardRedemption


def _get_request_forger(request):
    try:
        return request.user.forger_profile
    except ForgerProfile.DoesNotExist:
        return None


@login_required
def me(request):
    request_forger = _get_request_forger(request)

    if request_forger is None:
        messages.error(request, "Tu usuario necesita un perfil de forjador.")
        return redirect("home")

    return redirect("forgers:profile", username=request_forger.user.username)


@login_required
def profile(request, username):
    request_forger = _get_request_forger(request)

    if request_forger is None:
        messages.error(request, "Tu usuario necesita un perfil de forjador.")
        return redirect("home")

    forger = get_object_or_404(
        ForgerProfile.objects.select_related("user"),
        user__username=username,
    )

    if not _can_view_forger(request_forger, forger):
        messages.error(request, "No puedes ver este perfil.")
        return redirect("forgers:me")

    assignments = list(
        MissionAssignment.objects.filter(
            forger=forger,
            status=MissionAssignment.Status.ACTIVE,
        ).select_related("mission", "assigned_by")
    )
    today = timezone.localdate()
    assignment_rows = [
        _build_assignment_row(assignment, today)
        for assignment in assignments
    ]
    recent_redemptions = RewardRedemption.objects.filter(forger=forger).select_related(
        "reward",
    )[:5]
    family_members = _get_family_members(forger)

    return render(
        request,
        "forgers/dashboard.html",
        {
            "forger": forger,
            "star_balance": get_star_balance(forger),
            "astral_light_total": get_astral_light_total(forger),
            "assignment_groups": _group_assignment_rows_by_cadence(assignment_rows),
            "active_assignment_count": len(assignments),
            "recent_redemptions": recent_redemptions,
            "family_members": family_members,
            "is_current_forger": forger.id == request_forger.id,
            "uri_path": request.path,
        },
    )


@login_required
@require_POST
def complete_assignment(request, assignment_id):
    forger = _get_request_forger(request)

    if forger is None:
        if request.htmx:
            return render(
                request,
                "partials/toast.html",
                {
                    "message": "Tu usuario necesita un perfil de forjador.",
                    "variant": "alert-error",
                },
            )
        messages.error(request, "Tu usuario necesita un perfil de forjador.")
        return redirect("home")

    assignment = get_object_or_404(
        MissionAssignment.objects.select_related("mission", "forger", "assigned_by"),
        pk=assignment_id,
        forger=forger,
    )

    try:
        complete_mission_assignment(
            assignment=assignment,
            recorded_by=forger,
        )
    except ValidationError as exc:
        message = " ".join(exc.messages)
        toast_variant = "alert-error"
    else:
        message = "Mision completada correctamente."
        toast_variant = "alert-success"

    if request.htmx:
        assignment.refresh_from_db()
        return render(
            request,
            "forgers/partials/mission_completion_response.html",
            {
                "row": _build_assignment_row(assignment),
                "forger": forger,
                "star_balance": get_star_balance(forger),
                "astral_light_total": get_astral_light_total(forger),
                "active_assignment_count": MissionAssignment.objects.filter(
                    forger=forger,
                    status=MissionAssignment.Status.ACTIVE,
                ).count(),
                "toast_message": message,
                "toast_variant": toast_variant,
            },
        )

    if toast_variant == "alert-error":
        messages.error(request, message)
    else:
        messages.success(request, message)

    return redirect("forgers:profile", username=forger.user.username)


@login_required
def rewards(request):
    forger = _get_request_forger(request)

    if forger is None:
        messages.error(request, "Tu usuario necesita un perfil de forjador.")
        return redirect("home")

    star_balance = get_star_balance(forger)
    active_rewards = Reward.objects.filter(status=Reward.Status.ACTIVE).order_by(
        "star_cost",
        "title",
        "id",
    )
    redemptions = RewardRedemption.objects.filter(forger=forger).select_related(
        "reward",
    )

    return render(
        request,
        "forgers/rewards.html",
        {
            "forger": forger,
            "star_balance": star_balance,
            "reward_cards": [
                _build_reward_card(reward, star_balance)
                for reward in active_rewards
            ],
            "redemptions": redemptions,
            "uri_path": request.path,
        },
    )


@login_required
@require_POST
def request_reward(request, reward_id):
    forger = _get_request_forger(request)

    if forger is None:
        if request.htmx:
            return render(
                request,
                "partials/toast.html",
                {
                    "message": "Tu usuario necesita un perfil de forjador.",
                    "variant": "alert-error",
                },
            )
        messages.error(request, "Tu usuario necesita un perfil de forjador.")
        return redirect("home")

    reward = get_object_or_404(Reward, pk=reward_id)
    star_balance = get_star_balance(forger)

    if star_balance < reward.star_cost:
        message = "No tienes suficientes estrellas para esta recompensa."
        if request.htmx:
            return _render_reward_request_response(
                request=request,
                reward=reward,
                forger=forger,
                star_balance=star_balance,
                message=message,
                toast_variant="alert-error",
            )
        messages.error(request, message)
        return redirect("forgers:rewards")

    try:
        request_reward_redemption(
            reward=reward,
            forger=forger,
            requested_by=forger,
        )
    except ValidationError as exc:
        message = " ".join(exc.messages)
        toast_variant = "alert-error"
    else:
        message = "Recompensa solicitada correctamente."
        toast_variant = "alert-success"

    if request.htmx:
        return _render_reward_request_response(
            request=request,
            reward=reward,
            forger=forger,
            star_balance=get_star_balance(forger),
            message=message,
            toast_variant=toast_variant,
        )

    if toast_variant == "alert-error":
        messages.error(request, message)
    else:
        messages.success(request, message)

    return redirect("forgers:rewards")


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


def _build_assignment_row(assignment, today=None):
    today = today or timezone.localdate()
    return {
        "assignment": assignment,
        "is_completed_for_period": is_assignment_completed_for_period(
            assignment,
            today,
        ),
    }


def _build_reward_card(reward, star_balance):
    return {
        "reward": reward,
        "can_request": star_balance >= reward.star_cost,
        "missing_stars": max(reward.star_cost - star_balance, 0),
    }


def _render_reward_request_response(
    request,
    reward,
    forger,
    star_balance,
    message,
    toast_variant,
):
    redemptions = RewardRedemption.objects.filter(forger=forger).select_related(
        "reward",
    )
    return render(
        request,
        "forgers/partials/reward_request_response.html",
        {
            "card": _build_reward_card(reward, star_balance),
            "redemptions": redemptions,
            "toast_message": message,
            "toast_variant": toast_variant,
        },
    )


def _get_family_members(forger):
    family_ids = list(
        FamilyMembership.objects.filter(
            forger=forger,
            status=FamilyMembership.Status.ACTIVE,
        ).values_list("family_id", flat=True)
    )

    if family_ids:
        members = ForgerProfile.objects.filter(
            family_memberships__family_id__in=family_ids,
            family_memberships__status=FamilyMembership.Status.ACTIVE,
        )
    else:
        members = ForgerProfile.objects.all()

    return [
        {
            "forger": member,
            "star_balance": get_star_balance(member),
            "astral_light_total": get_astral_light_total(member),
            "is_current": member.id == forger.id,
        }
        for member in members.select_related("user").distinct().order_by(
            "display_name",
            "id",
        )
    ]


def _can_view_forger(request_forger, target_forger):
    if request_forger.id == target_forger.id:
        return True

    request_family_ids = set(
        FamilyMembership.objects.filter(
            forger=request_forger,
            status=FamilyMembership.Status.ACTIVE,
        ).values_list("family_id", flat=True)
    )

    if not request_family_ids:
        return True

    return FamilyMembership.objects.filter(
        forger=target_forger,
        family_id__in=request_family_ids,
        status=FamilyMembership.Status.ACTIVE,
    ).exists()
