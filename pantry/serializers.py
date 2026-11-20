from rest_framework import serializers

from .models import PantryItem


class PantryItemSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(read_only=True)

    class Meta:
        model = PantryItem
        fields = (
            'id', 'name', 'category', 'quantity', 'unit', 'location',
            'expires_on', 'stored_on', 'image_url', 'barcode', 'status', 'status_label',
        )
        read_only_fields = fields
