from django.contrib import admin

from core.admin import ReadOnlyAdminMixin

from .models import Mission
from .models import MissionAgeReward
from .models import MissionAssignment
from .models import MissionCompletion


class MissionAgeRewardInline(admin.TabularInline):
    model = MissionAgeReward
    extra = 0
    fields = ["age_group", "star_value", "astral_light_value", "is_active"]


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    inlines = [MissionAgeRewardInline]
    list_display = [
        "title",
        "cadence",
        "status",
    ]
    list_filter = ["cadence", "status", "created_at"]
    search_fields = ["title", "created_by__display_name"]


@admin.register(MissionAgeReward)
class MissionAgeRewardAdmin(admin.ModelAdmin):
    list_display = [
        "mission",
        "age_group",
        "star_value",
        "astral_light_value",
        "is_active",
    ]
    list_filter = ["age_group", "is_active", "created_at"]
    search_fields = ["mission__title"]


@admin.register(MissionAssignment)
class MissionAssignmentAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        "mission",
        "forger",
        "assigned_by",
        "starts_on",
        "ends_on",
        "status",
    ]
    list_filter = ["status", "starts_on", "created_at"]
    search_fields = [
        "mission__title",
        "forger__display_name",
        "assigned_by__display_name",
    ]


@admin.register(MissionCompletion)
class MissionCompletionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        "assignment",
        "recorded_by",
        "completed_on",
        "status",
    ]
    list_filter = ["status", "completed_on", "created_at"]
    search_fields = [
        "assignment__mission__title",
        "assignment__forger__display_name",
        "recorded_by__display_name",
    ]
