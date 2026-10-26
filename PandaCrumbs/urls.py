from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from ui_sso.views import PandaLogoutView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
    path("pantry/", include("pantry.urls")),
    path("recipes/", include("recipes.urls")),
    path("waste-audit/", include("waste_audit.urls")),
    path("habit-challenge/", include("habit_challenge.urls")),
    path("accounts/sso/ui/", include("ui_sso.urls")),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("accounts/logout/", PandaLogoutView.as_view(), name="logout"),
]
