from django.contrib import admin
from .models import ChallengePlan, Completion

admin.site.register(ChallengePlan)


@admin.register(Completion)
class CompletionAdmin(admin.ModelAdmin):
    list_display = ["user", "kind", "food", "completed_on", "points"]
    list_filter = ["kind", "completed_on"]
    search_fields = ["user__username", "food"]
    readonly_fields = ["created_at"]
