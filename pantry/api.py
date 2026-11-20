from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import PantryItem
from .serializers import PantryItemSerializer


class PantryItemViewSet(ReadOnlyModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = PantryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PantryItem.objects.filter(owner=self.request.user)
