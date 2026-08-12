from django.contrib import admin

from core.admin import ReadOnlyAdminMixin

from .models import Reward
from .models import RewardRedemption


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "star_cost",
        "requires_approval",
        "status",
        "created_by",
    ]
    list_filter = ["requires_approval", "status", "created_at"]
    search_fields = ["title", "description", "created_by__display_name"]


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        "reward",
        "forger",
        "star_cost",
        "status",
        "requested_by",
        "approved_by",
        "requested_at",
    ]
    list_filter = ["status", "requested_at", "resolved_at", "fulfilled_at"]
    search_fields = [
        "reward__title",
        "forger__display_name",
        "requested_by__display_name",
        "approved_by__display_name",
    ]
