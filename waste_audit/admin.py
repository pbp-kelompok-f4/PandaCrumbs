from django.contrib import admin

from .models import FoodWasteLog


@admin.register(FoodWasteLog)
class FoodWasteLogAdmin(admin.ModelAdmin):
    list_display = ["food_name", "owner", "quantity", "unit", "wasted_on", "reason", "estimated_loss"]
    list_filter = ["reason", "unit", "wasted_on"]
    search_fields = ["food_name", "owner__username"]
