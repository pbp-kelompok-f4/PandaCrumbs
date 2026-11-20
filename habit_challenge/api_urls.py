from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.plan_list_create, name="api_habit_root"),
    path("plans/", api_views.plan_list_create, name="api_habit_plans"),
    path("plans/<int:pk>/", api_views.plan_detail, name="api_habit_plan_detail"),
    path("completions/", api_views.completion_list_create, name="api_habit_completions"),
]