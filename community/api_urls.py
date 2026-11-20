from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.offer_list_create, name="api_offer_list_create"),
    path("<int:pk>/", api_views.offer_detail, name="api_offer_detail"),
    path("<int:pk>/claim/", api_views.claim_offer, name="api_offer_claim"),
    path("<int:pk>/claims/", api_views.offer_claims_list, name="api_offer_claims_list"),
]