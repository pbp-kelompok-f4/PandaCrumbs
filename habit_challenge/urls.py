from django.urls import path
from . import views

app_name = "habit_challenge"
urlpatterns = [
    path("", views.index, name="index"),
    path("plans/add/", views.plan_edit, name="plan_add"),
    path("plans/<int:pk>/edit/", views.plan_edit, name="plan_edit"),
    path("plans/<int:pk>/delete/", views.plan_delete, name="plan_delete"),
    path("<str:kind>/complete/", views.complete, name="complete"),
    path("<str:kind>/cook/", views.cook_form, name="cook_form"),
    path("<str:kind>/cook/save/", views.cook, name="cook"),
]
