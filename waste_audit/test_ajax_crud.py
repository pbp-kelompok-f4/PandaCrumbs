from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import FoodWasteLog


class AuditAjaxCrudTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(username="ajax-owner")
        self.other = users.objects.create_user(username="ajax-other")
        self.entry = FoodWasteLog.objects.create(
            owner=self.owner, food_name="Bayam", quantity=Decimal("100"),
            unit="gram", wasted_on=timezone.localdate(), reason="spoiled",
            estimated_loss=Decimal("3000"),
        )
        self.secret = FoodWasteLog.objects.create(
            owner=self.other, food_name="Private food", quantity=Decimal("1"),
            unit="pcs", wasted_on=timezone.localdate(), reason="other",
            estimated_loss=Decimal("9000"),
        )
        self.payload = {
            "food_name": "Roti AJAX", "quantity": "2.50", "unit": "pcs",
            "wasted_on": timezone.localdate().isoformat(),
            "reason": "expired", "estimated_loss": "4500.75",
        }
        self.client.force_login(self.owner)

    def get(self, route, pk=None, **params):
        url = reverse("waste_audit:" + route, args=[pk] if pk else [])
        return self.client.get(url, params, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def post(self, route, pk=None, data=None):
        url = reverse("waste_audit:" + route, args=[pk] if pk else [])
        return self.client.post(
            url, self.payload if data is None else data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_add_and_edit_return_reusable_forms_with_explicit_actions(self):
        for route, pk in [("add", None), ("edit", self.entry.pk)]:
            with self.subTest(route=route):
                response = self.get(route, pk)
                self.assertEqual(response.status_code, 200)
                html = response.json()["html"]
                self.assertIn("data-audit-mutation", html)
                self.assertIn('name="csrfmiddlewaretoken"', html)
                self.assertIn(
                    reverse("waste_audit:" + route, args=[pk] if pk else []),
                    html,
                )
                self.assertIn("data-audit-product-search", html)
                self.assertIn('id="audit-reason"', html)
                self.assertIn('for="audit-reason"', html)
                self.assertNotIn('id="id_reason"', html)
                self.assertNotIn("<!doctype", html.lower())
                self.assertNotIn(self.secret.food_name, html)

    def test_confirmation_get_keeps_record_and_has_explicit_post_action(self):
        response = self.get("delete", self.entry.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data-audit-mutation", response.json()["html"])
        self.assertIn(reverse("waste_audit:delete", args=[self.entry.pk]), response.json()["html"])
        self.assertTrue(FoodWasteLog.objects.filter(pk=self.entry.pk).exists())

    def test_create_json_preserves_decimals_and_ignores_forged_owner(self):
        response = self.post("add", data={**self.payload, "owner": self.other.pk})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["ok"])
        entry = FoodWasteLog.objects.get(pk=response.json()["entry_id"])
        self.assertEqual(entry.owner, self.owner)
        self.assertEqual(entry.quantity, Decimal("2.50"))
        self.assertEqual(entry.estimated_loss, Decimal("4500.75"))
        self.assertEqual(response.json()["index_url"], reverse("waste_audit:index"))
        # AJAX feedback must not be shown again as a stale Django message.
        page = self.client.get(reverse("waste_audit:index"))
        self.assertEqual(list(page.context["messages"]), [])

    def test_edit_json_updates_owned_record_and_summary(self):
        response = self.post("edit", self.entry.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.food_name, self.payload["food_name"])
        self.assertEqual(self.entry.owner, self.owner)
        page = self.client.get(reverse("waste_audit:index"))
        self.assertEqual(page.context["summary"]["estimated_loss"], Decimal("4500.75"))

    def test_invalid_create_returns_422_with_values_errors_and_escaped_text(self):
        response = self.post(
            "add",
            data={**self.payload, "food_name": "<script>milk</script>", "quantity": "0"},
        )
        self.assertEqual(response.status_code, 422)
        html = response.json()["html"]
        self.assertIn("audit-field-invalid", html)
        self.assertIn("&lt;script&gt;milk&lt;/script&gt;", html)
        self.assertNotIn("<script>milk</script>", html)
        self.assertEqual(FoodWasteLog.objects.count(), 2)

    def test_invalid_edit_returns_422_without_changing_record(self):
        response = self.post(
            "edit", self.entry.pk, {**self.payload, "estimated_loss": "-1"},
        )
        self.assertEqual(response.status_code, 422)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.food_name, "Bayam")
        self.assertEqual(self.entry.estimated_loss, Decimal("3000"))

    def test_delete_returns_json_and_preserves_other_owner(self):
        response = self.post("delete", self.entry.pk, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertFalse(FoodWasteLog.objects.filter(pk=self.entry.pk).exists())
        self.assertTrue(FoodWasteLog.objects.filter(pk=self.secret.pk).exists())
        self.assertEqual(self.post("delete", self.entry.pk, {}).status_code, 404)

    def test_foreign_and_missing_records_remain_inaccessible_over_ajax(self):
        for pk in [self.secret.pk, self.secret.pk + 1000]:
            for route in ["edit", "delete"]:
                with self.subTest(pk=pk, route=route):
                    self.assertEqual(self.get(route, pk).status_code, 404)
                    self.assertEqual(self.post(route, pk).status_code, 404)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.food_name, "Private food")

    def test_ajax_requires_login_for_read_and_write(self):
        self.client.logout()
        for route, pk in [
            ("add", None), ("edit", self.entry.pk), ("delete", self.entry.pk),
        ]:
            with self.subTest(route=route):
                self.assertEqual(self.get(route, pk).status_code, 302)
                self.assertEqual(self.post(route, pk).status_code, 302)
        self.assertEqual(FoodWasteLog.objects.count(), 2)

    def test_ajax_mutations_still_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for route, pk in [
            ("add", None), ("edit", self.entry.pk), ("delete", self.entry.pk),
        ]:
            with self.subTest(route=route):
                url = reverse("waste_audit:" + route, args=[pk] if pk else [])
                response = client.post(url, self.payload, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
                self.assertEqual(response.status_code, 403)
        self.assertEqual(FoodWasteLog.objects.count(), 2)

    def test_partial_get_provides_csrf_cookie_for_a_valid_ajax_post(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        url = reverse("waste_audit:add")
        response = client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        token = client.cookies["csrftoken"].value
        response = client.post(
            url, self.payload, HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)

    def test_refresh_keeps_active_filters_and_private_totals(self):
        self.post("add")
        response = self.get("index", reason="expired")
        html = response.json()["html"]
        self.assertIn("Roti AJAX", html)
        self.assertNotIn("Bayam", html)
        self.assertNotIn("Private food", html)
        self.assertIn("Rp4.500,75", html)

    def test_partial_confirmation_escapes_food_name(self):
        self.entry.food_name = '<img src=x onerror="alert(1)">'
        self.entry.save()
        html = self.get("delete", self.entry.pk).json()["html"]
        self.assertNotIn(self.entry.food_name, html)
        self.assertIn("&lt;img", html)

    def test_plain_get_still_renders_full_form_pages(self):
        for route, pk in [("add", None), ("edit", self.entry.pk), ("delete", self.entry.pk)]:
            with self.subTest(route=route):
                url = reverse("waste_audit:" + route, args=[pk] if pk else [])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn("<!doctype html>", response.content.decode().lower())

