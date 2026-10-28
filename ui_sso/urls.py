from django.urls import path
from . import views

app_name = "ui_sso"
urlpatterns = [
    path("login/", views.start, name="login"),
    path("callback/", views.callback, name="callback"),
]
