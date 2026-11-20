from django.templatetags.static import static
from rest_framework import serializers

from .models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    is_saved = serializers.BooleanField(read_only=True)
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, recipe):
        if recipe.image_url:
            return recipe.image_url
        if recipe.demo_image:
            return self.context['request'].build_absolute_uri(static('main/images/' + recipe.demo_image))
        return ''

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'author_name', 'title', 'ingredients', 'steps',
            'portions', 'minutes', 'image_url', 'created_at', 'is_saved',
        )
        read_only_fields = fields
