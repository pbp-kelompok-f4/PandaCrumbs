from django.urls import path
from . import views

app_name = "authentication"

urlpatterns = [
    path("login/", views.login_api, name="login_api"),
    path("register/", views.register_api, name="register_api"),
    path("logout/", views.logout_api, name="logout_api"),
]