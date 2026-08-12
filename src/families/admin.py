from django.contrib import admin

from .models import Family
from .models import FamilyMembership


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ["name", "created_by", "created_at"]
    search_fields = ["name", "created_by__display_name"]


@admin.register(FamilyMembership)
class FamilyMembershipAdmin(admin.ModelAdmin):
    list_display = ["family", "forger", "role", "status", "joined_at"]
    list_filter = ["role", "status", "joined_at"]
    search_fields = ["family__name", "forger__display_name"]
