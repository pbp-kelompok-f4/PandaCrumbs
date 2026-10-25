import time
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit
from xml.sax.saxutils import escape

import requests
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .client import CASSession
from .models import UIIdentity
from .views import FLOW_KEY


@override_settings(
    SSO_UI_ENABLED=True,
    SSO_UI_SERVER_URL="https://sso.ui.ac.id/cas2/",
)
class SSOTests(TestCase):
    def begin(self, target="/waste-audit/"):
        response = self.client.post(reverse("ui_sso:login"), {"next": target})
        self.assertEqual(response.status_code, 302)
        return self.client.session[FLOW_KEY]

    def finish(self, subject="fayiz.ui", body=None):
        flow = self.client.session[FLOW_KEY]
        if body is None:
            body = (
                '<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">'
                "<cas:authenticationSuccess><cas:user>" + escape(subject) +
                "</cas:user><cas:attributes><cas:is_staff>true</cas:is_staff>"
                "</cas:attributes></cas:authenticationSuccess></cas:serviceResponse>"
            ).encode()
        response = Mock(status_code=200, content=body)
        with patch("requests.Session.request", return_value=response) as transport:
            result = self.client.get(reverse("ui_sso:callback"), {
                "state": flow["state"], "ticket": "ST-test-ticket",
            })
        return result, transport

    def test_login_displays_both_methods(self):
        response = self.client.get(reverse("login"), {"next": "/waste-audit/"})
        self.assertContains(response, "Masuk dengan SSO UI")
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'value="/waste-audit/"')

    @override_settings(SSO_UI_ENABLED=False)
    def test_disabled_sso_keeps_password_login_available(self):
        self.assertNotContains(self.client.get(reverse("login")), "Masuk dengan SSO UI")
        self.assertEqual(self.client.post(reverse("ui_sso:login")).status_code, 404)
        self.assertEqual(self.client.get(reverse("ui_sso:callback")).status_code, 404)

    def test_start_requires_post_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.get(reverse("ui_sso:login")).status_code, 405)
        self.assertEqual(client.post(reverse("ui_sso:login")).status_code, 403)
        client.get(reverse("login"))
        response = client.post(reverse("ui_sso:login"), {
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertEqual(response.status_code, 302)

    def test_start_redirects_to_ui_with_session_bound_service(self):
        flow = self.begin()
        self.assertEqual(urlsplit(flow["service"]).path, reverse("ui_sso:callback"))
        self.assertEqual(parse_qs(urlsplit(flow["service"]).query)["state"], [flow["state"]])
        response = self.client.post(reverse("ui_sso:login"))
        parsed = urlsplit(response.url)
        self.assertEqual((parsed.scheme, parsed.netloc, parsed.path),
                         ("https", "sso.ui.ac.id", "/cas2/login"))
        self.assertEqual(parse_qs(parsed.query)["service"], [self.client.session[FLOW_KEY]["service"]])
        self.assertNotEqual(flow["state"], self.client.session[FLOW_KEY]["state"])

    def test_external_next_is_rejected(self):
        for target in ["https://evil.example/", "//evil.example/", "javascript:alert(1)", "///evil.example/"]:
            with self.subTest(target=target):
                self.assertEqual(self.begin(target)["next"], "/pantry/")

    def test_success_verifies_ticket_and_logs_into_django(self):
        flow = self.begin()
        result, transport = self.finish()
        self.assertRedirects(result, "/waste-audit/", fetch_redirect_response=False)
        identity = UIIdentity.objects.get(subject="fayiz.ui")
        self.assertEqual(int(self.client.session["_auth_user_id"]), identity.user_id)
        self.assertFalse(identity.user.has_usable_password())
        self.assertFalse(identity.user.is_staff)
        self.assertFalse(identity.user.is_superuser)
        self.assertNotIn(FLOW_KEY, self.client.session)
        self.assertEqual(transport.call_args.args[:2], ("GET", "https://sso.ui.ac.id/cas2/serviceValidate"))
        self.assertEqual(transport.call_args.kwargs["params"],
                         {"ticket": "ST-test-ticket", "service": flow["service"]})
        self.assertEqual(transport.call_args.kwargs["timeout"], (3.05, 8))
        self.assertTrue(transport.call_args.kwargs["verify"])
        self.assertFalse(transport.call_args.kwargs["allow_redirects"])
        self.assertIn("no-store", result["Cache-Control"])
        self.assertEqual(result["Referrer-Policy"], "no-referrer")
        self.assertEqual(self.client.get("/waste-audit/").status_code, 200)

    def test_repeated_login_reuses_identity(self):
        self.begin()
        self.finish()
        user_id = self.client.session["_auth_user_id"]
        self.client.post(reverse("logout"))
        self.begin()
        self.finish()
        self.assertEqual(self.client.session["_auth_user_id"], user_id)
        self.assertEqual(UIIdentity.objects.count(), 1)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_same_name_local_account_is_not_claimed(self):
        local = get_user_model().objects.create_user("fayiz.ui", password="local-password")
        self.begin()
        self.finish()
        self.assertNotEqual(int(self.client.session["_auth_user_id"]), local.pk)
        self.assertTrue(get_user_model().objects.get(pk=local.pk).check_password("local-password"))
        self.assertEqual(get_user_model().objects.count(), 2)

    def test_two_ui_identities_remain_separate(self):
        self.begin()
        self.finish("first.ui")
        first_id = self.client.session["_auth_user_id"]
        self.client.logout()
        self.begin()
        self.finish("second.ui")
        self.assertNotEqual(first_id, self.client.session["_auth_user_id"])

    def test_inactive_identity_cannot_login(self):
        user = get_user_model().objects.create_user("disabled", is_active=False)
        UIIdentity.objects.create(subject="disabled.ui", user=user)
        self.begin()
        result, _ = self.finish("disabled.ui")
        self.assertTrue(result.url.startswith(reverse("login")))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unsolicited_or_wrong_state_does_not_contact_cas(self):
        with patch("requests.Session.request") as transport:
            result = self.client.get(reverse("ui_sso:callback"), {"ticket": "ST-forged", "state": "wrong"})
            self.assertTrue(result.url.startswith(reverse("login")))
            self.begin()
            self.client.get(reverse("ui_sso:callback"), {"ticket": "ST-forged", "state": "wrong"})
            transport.assert_not_called()
        self.assertFalse(UIIdentity.objects.exists())

    def test_expired_flow_is_rejected(self):
        self.begin()
        session = self.client.session
        session[FLOW_KEY] = {**session[FLOW_KEY], "created": time.time() - 601}
        session.save()
        result, transport = self.finish()
        transport.assert_not_called()
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(result.url.startswith(reverse("login")))

    def test_missing_ticket_returns_clean_login_url(self):
        flow = self.begin()
        result = self.client.get(reverse("ui_sso:callback"), {"state": flow["state"]})
        self.assertTrue(result.url.startswith(reverse("login")))
        self.assertNotIn("ticket", result.url)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_ticket_replay_is_rejected(self):
        flow = self.begin()
        self.finish()
        self.client.post(reverse("logout"))
        with patch("requests.Session.request") as transport:
            self.client.get(reverse("ui_sso:callback"), {"state": flow["state"], "ticket": "ST-test-ticket"})
            transport.assert_not_called()
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_invalid_ticket_and_malformed_cas_response_do_not_create_users(self):
        for body in [
            b'<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas"><cas:authenticationFailure code="INVALID_TICKET"/></cas:serviceResponse>',
            b"<html>Service unavailable</html>",
            b"not xml",
            b'<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas"/>',
        ]:
            with self.subTest(body=body):
                self.begin()
                result, _ = self.finish(body=body)
                self.assertTrue(result.url.startswith(reverse("login")))
                self.assertNotIn("_auth_user_id", self.client.session)
        self.assertFalse(get_user_model().objects.exists())

    def test_timeout_preserves_normal_login(self):
        flow = self.begin()
        with patch("requests.Session.request", side_effect=requests.Timeout):
            response = self.client.get(reverse("ui_sso:callback"), {"state": flow["state"], "ticket": "ST-timeout"}, follow=True)
        self.assertContains(response, "gunakan login biasa")
        self.assertContains(response, 'name="password"')
        self.assertFalse(UIIdentity.objects.exists())

    def test_verification_error_log_omits_ticket_and_callback(self):
        flow = self.begin()
        error = requests.HTTPError("private-ticket-and-url", response=Mock(status_code=400))
        with patch("requests.Session.request", side_effect=error):
            with self.assertLogs("ui_sso.views", level="WARNING") as logs:
                self.client.get(reverse("ui_sso:callback"), {
                    "state": flow["state"], "ticket": "ST-secret-ticket",
                })
        output = " ".join(logs.output)
        self.assertIn("HTTP status=400", output)
        for private in ["ST-secret-ticket", "private-ticket-and-url", flow["state"], flow["service"]]:
            self.assertNotIn(private, output)

    def test_existing_login_is_not_switched_by_sso_callback(self):
        flow = self.begin()
        local = get_user_model().objects.create_user("local", password="test-password")
        self.client.force_login(local)
        with patch("requests.Session.request") as transport:
            self.client.get(reverse("ui_sso:callback"), {"state": flow["state"], "ticket": "ST-other"})
            transport.assert_not_called()
        self.assertEqual(int(self.client.session["_auth_user_id"]), local.pk)

    def test_password_login_and_logout_still_work(self):
        get_user_model().objects.create_user("local", password="test-password")
        self.assertRedirects(
            self.client.post(reverse("login"), {"username": "local", "password": "test-password", "next": "/waste-audit/"}),
            "/waste-audit/", fetch_redirect_response=False,
        )
        self.assertEqual(self.client.get("/waste-audit/").status_code, 200)
        self.assertRedirects(self.client.post(reverse("logout")), "/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/waste-audit/").status_code, 302)

    def test_sso_user_cannot_read_or_modify_another_users_audit(self):
        from waste_audit.models import FoodWasteLog
        from django.utils import timezone
        owner = get_user_model().objects.create_user("other")
        log = FoodWasteLog.objects.create(
            owner=owner, food_name="Catatan rahasia", quantity=1, unit="pcs",
            wasted_on=timezone.localdate(), reason="expired", estimated_loss=1000,
        )
        self.begin()
        self.finish()
        self.assertNotContains(self.client.get("/waste-audit/"), "Catatan rahasia")
        for route in ["edit", "delete"]:
            url = f"/waste-audit/{log.pk}/{route}/"
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, {}).status_code, 404)


class CASHTTPTests(TestCase):
    def test_verification_identifies_the_application_to_ui_gateway(self):
        response = Mock(status_code=200)
        with patch("requests.Session.send", return_value=response) as send:
            with CASSession() as session:
                session.get("https://sso.ui.ac.id/cas2/serviceValidate")
        prepared = send.call_args.args[0]
        self.assertEqual(prepared.headers["User-Agent"], "PandaCrumbs/0.2 (UI SSO CAS client)")
        self.assertTrue(send.call_args.kwargs["verify"])

    def test_bad_http_status_or_redirect_fails_closed(self):
        for status in [302, 500]:
            response = Mock(status_code=status)
            if status == 500:
                response.raise_for_status.side_effect = requests.HTTPError
            with patch("requests.Session.request", return_value=response):
                with CASSession() as session, self.assertRaises(requests.HTTPError):
                    session.get("https://sso.ui.ac.id/cas2/serviceValidate")
