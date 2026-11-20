from django.utils import timezone
from rest_framework import serializers
from .models import FoodWasteLog


class FoodWasteLogSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    unit_display = serializers.CharField(source="get_unit_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = FoodWasteLog
        fields = [
            "id",
            "owner",
            "food_name",
            "quantity",
            "unit",
            "unit_display",
            "wasted_on",
            "reason",
            "reason_display",
            "estimated_loss",
            "created_at",
        ]
        read_only_fields = ["id", "owner", "created_at"]

    def validate_wasted_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Tanggal terbuang tidak boleh di masa depan.")
        return value