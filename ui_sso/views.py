import logging
import secrets
import time
from urllib.parse import urlencode
from uuid import uuid4
from xml.etree.ElementTree import ParseError

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LogoutView
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import redirect, resolve_url
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.text import slugify
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_GET, require_POST

from .client import CASSession, cas_client
from .models import UIIdentity

logger = logging.getLogger(__name__)

FLOW_KEY = "ui_sso_flow"
FLOW_MAX_AGE = 600


def safe_next(request, target):
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return resolve_url(settings.LOGIN_REDIRECT_URL)


def failed(request, message, target=None):
    messages.error(request, message)
    response = redirect(reverse("login") + "?" + urlencode({"next": safe_next(request, target)}))
    response["Referrer-Policy"] = "no-referrer"
    return response


@never_cache
@require_POST
def start(request):
    if not settings.SSO_UI_ENABLED:
        raise Http404
    target = safe_next(request, request.POST.get("next"))
    if request.user.is_authenticated:
        return redirect(target)
    state = secrets.token_urlsafe(32)
    service = request.build_absolute_uri(reverse("ui_sso:callback")) + "?" + urlencode({"state": state})
    request.session[FLOW_KEY] = {
        "state": state, "service": service, "next": target, "created": time.time(),
    }
    return redirect(cas_client(service).get_login_url())


def user_for_subject(subject):
    identity = UIIdentity.objects.select_related("user").filter(subject=subject).first()
    if identity:
        return identity.user
    try:
        with transaction.atomic():
            username = "ui_" + (slugify(subject)[:100] or "pengguna") + "_" + uuid4().hex[:12]
            user = get_user_model().objects.create_user(username=username, password=None)
            UIIdentity.objects.create(subject=subject, user=user)
            return user
    except IntegrityError:
        # A simultaneous callback may already have created this identity.
        return UIIdentity.objects.select_related("user").get(subject=subject).user


@never_cache
@require_GET
@sensitive_variables("ticket", "subject", "attributes")
def callback(request):
    if not settings.SSO_UI_ENABLED:
        raise Http404
    flow = request.session.pop(FLOW_KEY, None)
    if request.user.is_authenticated:
        return redirect(safe_next(request, flow.get("next") if flow else None))
    if (
        not flow
        or not constant_time_compare(request.GET.get("state", ""), flow["state"])
        or not 0 <= time.time() - flow["created"] <= FLOW_MAX_AGE
    ):
        return failed(request, "Sesi masuk SSO berakhir atau tidak cocok. Silakan coba lagi.")
    ticket = request.GET.get("ticket", "")
    if not ticket or len(ticket) > 4096:
        return failed(request, "SSO belum memberikan tiket login. Silakan coba lagi.", flow["next"])
    try:
        with CASSession() as session:
            subject, attributes, _ = cas_client(flow["service"], session).verify_ticket(ticket)
    except (requests.RequestException, ValueError, ParseError, AttributeError, IndexError, TypeError) as exc:
        # Never log tickets, callback URLs, profiles, or raw exception text.
        logger.warning(
            "SSO UI verification failed: %s; HTTP status=%s",
            type(exc).__name__, getattr(getattr(exc, "response", None), "status_code", None),
        )
        return failed(
            request, "SSO UI belum dapat memverifikasi login. Coba lagi atau gunakan login biasa.",
            flow["next"],
        )
    if not isinstance(subject, str) or not subject.strip() or len(subject) > 255:
        return failed(request, "Tiket SSO tidak valid atau sudah kedaluwarsa. Silakan coba lagi.", flow["next"])
    user = user_for_subject(subject)
    if not user.is_active:
        return failed(request, "Akun aplikasi ini tidak aktif.", flow["next"])
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, "Berhasil masuk dengan SSO UI.")
    response = redirect(safe_next(request, flow["next"]))
    response["Referrer-Policy"] = "no-referrer"
    return response


class PandaLogoutView(LogoutView):
    """End the local session before sending SSO users to UI's central logout."""

    def post(self, request, *args, **kwargs):
        # Existing SSO sessions also work: identity comes from the verified mapping.
        used_sso = request.user.is_authenticated and UIIdentity.objects.filter(
            user_id=request.user.pk,
        ).exists()
        response = super().post(request, *args, **kwargs)
        if not used_sso:
            return response
        try:
            logout_url = cas_client(None).get_logout_url()
        except ImproperlyConfigured:
            messages.warning(request, "Sudah keluar dari PandaCrumbs. Logout SSO UI belum tersedia; sesi UI mungkin masih aktif.")
            return response
        response = redirect(logout_url)
        response["Referrer-Policy"] = "no-referrer"
        return response
