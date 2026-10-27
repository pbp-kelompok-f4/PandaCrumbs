from django.urls import path
from . import views

app_name = "community"

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.offer_create, name="add"),
    path("<int:pk>/", views.offer_detail, name="detail"),
    path("<int:pk>/edit/", views.offer_edit, name="edit"),
    path("<int:pk>/delete/", views.offer_delete, name="delete"),
    path("<int:pk>/claim/", views.claim_food, name="claim"),
]