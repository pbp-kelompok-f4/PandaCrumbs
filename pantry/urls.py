from django.urls import path
from . import views
app_name = "pantry"
urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.edit, name="add"),
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/consume/", views.consume, name="consume"),
    path("<int:pk>/delete/", views.delete, name="delete"),
]
