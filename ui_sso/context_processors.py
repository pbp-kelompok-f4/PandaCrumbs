from django.conf import settings


def sso_options(request):
    return {"sso_ui_enabled": settings.SSO_UI_ENABLED}
