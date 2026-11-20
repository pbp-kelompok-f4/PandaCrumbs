from rest_framework import serializers
from .models import FoodOffer, FoodClaim

class FoodOfferSerializer(serializers.ModelSerializer):
    donor = serializers.ReadOnlyField(source="donor.username")
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = FoodOffer
        fields = [
            "id",
            "donor",
            "title",
            "category",
            "description",
            "portions",
            "remaining_portions",
            "pickup_location",
            "contact_info",
            "pickup_deadline",
            "latitude",
            "longitude",
            "image_url",
            "status",
            "status_display",
            "is_expired",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "donor", "remaining_portions", "created_at", "updated_at"]

class FoodClaimSerializer(serializers.ModelSerializer):
    claimer = serializers.ReadOnlyField(source="claimer.username")
    offer_title = serializers.ReadOnlyField(source="offer.title")

    class Meta:
        model = FoodClaim
        fields = [
            "id",
            "offer",
            "offer_title",
            "claimer",
            "portions_claimed",
            "notes",
            "claimed_at",
        ]
        read_only_fields = ["id", "offer", "claimer", "claimed_at"]