from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.waste_log_list_create, name="api_waste_list_create"),
    path("summary/", api_views.waste_summary, name="api_waste_summary"),
    path("<int:pk>/", api_views.waste_log_detail, name="api_waste_detail"),
]