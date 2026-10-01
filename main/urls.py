from django.urls import path
from . import views
app_name = "main"
urlpatterns = [
    path("", views.show_landing_page, name="show_landing_page"),
    path("accounts/register/", views.register, name="register"),
    path("api/products/", views.product_search, name="products"),
]
