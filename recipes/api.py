from rest_framework.renderers import JSONRenderer
from django.db.models import Exists, OuterRef, Q
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Bookmark, Recipe
from .serializers import RecipeSerializer


class RecipeViewSet(ReadOnlyModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = RecipeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params
        tab = params.get('tab', 'all')
        if tab in ('mine', 'saved') and not user.is_authenticated:
            raise NotAuthenticated()
        saved = Bookmark.objects.filter(user=user) if user.is_authenticated else Bookmark.objects.none()
        recipes = Recipe.objects.select_related('author')
        if tab == 'mine':
            recipes = recipes.filter(author=user)
        elif tab == 'saved':
            recipes = recipes.filter(bookmark__user=user)
        query = params.get('q', '').strip()[:120]
        if query:
            recipes = recipes.filter(Q(title__icontains=query) | Q(ingredients__icontains=query))
        ingredients = list(dict.fromkeys(
            value.strip()[:40] for value in params.getlist('ingredient') if value.strip()
        ))[:12]
        for ingredient in ingredients:
            recipes = recipes.filter(ingredients__icontains=ingredient)
        if params.get('quick') == '1':
            recipes = recipes.filter(minutes__lt=30)
        return recipes.annotate(is_saved=Exists(saved.filter(recipe_id=OuterRef('pk'))))
