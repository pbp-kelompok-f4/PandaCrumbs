from rest_framework import serializers
from .models import ChallengePlan, Completion


class ChallengePlanSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    completed_days = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = ChallengePlan
        fields = [
            "id",
            "user",
            "title",
            "kind",
            "kind_display",
            "target_days",
            "category",
            "category_display",
            "food",
            "starts_on",
            "ends_on",
            "completed_days",
            "progress_percent",
        ]
        read_only_fields = ["id", "user"]

    def get_completed_days(self, obj):
        return obj.completions.count()

    def get_progress_percent(self, obj):
        if not obj.target_days:
            return 0
        return min(100, round((obj.completions.count() / obj.target_days) * 100))

    def validate(self, attrs):
        starts_on = attrs.get("starts_on", getattr(self.instance, "starts_on", None))
        ends_on = attrs.get("ends_on", getattr(self.instance, "ends_on", None))
        if starts_on and ends_on and ends_on < starts_on:
            raise serializers.ValidationError(
                {"ends_on": "Tanggal selesai harus sama atau setelah tanggal mulai."}
            )
        return attrs


class CompletionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    plan_title = serializers.ReadOnlyField(source="plan.title")

    class Meta:
        model = Completion
        fields = [
            "id",
            "user",
            "kind",
            "kind_display",
            "plan",
            "plan_title",
            "food",
            "completed_on",
            "points",
            "created_at",
        ]
        read_only_fields = ["id", "user", "points", "created_at"]