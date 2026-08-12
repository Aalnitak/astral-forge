from django.contrib import admin

from core.admin import ReadOnlyAdminMixin

from .models import AstralLightLedgerEntry
from .models import ForgeEvent
from .models import StarLedgerEntry


class StarLedgerEntryInline(admin.TabularInline):
    model = StarLedgerEntry
    extra = 0
    fields = ["forger", "entry_type", "amount", "created_at"]
    readonly_fields = ["forger", "entry_type", "amount", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AstralLightLedgerEntryInline(admin.TabularInline):
    model = AstralLightLedgerEntry
    extra = 0
    fields = ["forger", "entry_type", "amount", "created_at"]
    readonly_fields = ["forger", "entry_type", "amount", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ForgeEvent)
class ForgeEventAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    inlines = [StarLedgerEntryInline, AstralLightLedgerEntryInline]
    list_display = ["forger", "event_type", "mission_completion", "occurred_at"]
    list_filter = ["event_type", "occurred_at", "created_at"]
    search_fields = [
        "forger__display_name",
        "mission_completion__assignment__mission__title",
        "notes",
    ]


@admin.register(StarLedgerEntry)
class StarLedgerEntryAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["forger", "entry_type", "amount", "forge_event", "created_at"]
    list_filter = ["entry_type", "created_at"]
    search_fields = ["forger__display_name", "forge_event__notes"]


@admin.register(AstralLightLedgerEntry)
class AstralLightLedgerEntryAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["forger", "entry_type", "amount", "forge_event", "created_at"]
    list_filter = ["entry_type", "created_at"]
    search_fields = ["forger__display_name", "forge_event__notes"]
