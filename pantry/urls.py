from .api import PantryItemViewSet
from django.urls import path
from . import views

app_name = "pantry"
urlpatterns = [
    path("api/", PantryItemViewSet.as_view({"get": "list"}), name="api-list"),
    path("api/<int:pk>/", PantryItemViewSet.as_view({"get": "retrieve"}), name="api-detail"),
    path("", views.index, name="index"),
    path("add/", views.edit, name="add"),
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/consume/", views.consume, name="consume"),
    path("<int:pk>/delete/", views.delete, name="delete"),
]
