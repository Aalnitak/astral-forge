from django.contrib import admin

from .models import ForgerProfile


@admin.register(ForgerProfile)
class ForgerProfileAdmin(admin.ModelAdmin):
    list_display = ["display_name", "user", "age_group", "created_at"]
    list_filter = ["age_group", "created_at"]
    search_fields = ["display_name", "user__username", "user__email"]
