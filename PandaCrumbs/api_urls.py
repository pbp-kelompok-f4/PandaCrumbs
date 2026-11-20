from rest_framework.routers import SimpleRouter

from pantry.api import PantryItemViewSet
from recipes.api import RecipeViewSet


router = SimpleRouter()
router.register('pantry', PantryItemViewSet, basename='pantry')
router.register('recipes', RecipeViewSet, basename='recipe')

app_name = 'api'
urlpatterns = router.urls
