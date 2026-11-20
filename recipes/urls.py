from .api import RecipeViewSet
from django.urls import path
from . import views

app_name = "recipes"
urlpatterns = [
    path("api/", RecipeViewSet.as_view({"get": "list"}), name="api-list"),
    path("api/<int:pk>/", RecipeViewSet.as_view({"get": "retrieve"}), name="api-detail"),
    path("", views.index, name="index"),
    path("add/", views.edit, name="add"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path("<int:pk>/bookmark/", views.bookmark, name="bookmark"),
]
