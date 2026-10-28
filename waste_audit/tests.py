from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import FoodWasteLog


class FoodWasteAuditTests(TestCase):
    """Exercise private CRUD, filtered reports, and failures that affect trust."""

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            "audit-owner", password="testing-password-123"
        )
        self.other = get_user_model().objects.create_user(
            "audit-other", password="testing-password-123"
        )
        self.today = timezone.localdate()
        self.entry = self.make_entry(
            food_name="Nasi", quantity="1.25", unit="porsi", estimated_loss="8500.50"
        )
        self.secret = self.make_entry(
            owner=self.other,
            food_name="Makanan Rahasia Akun Lain",
            estimated_loss="987654.32",
        )
        self.data = {
            "food_name": "Susu",
            "quantity": "0.50",
            "unit": "liter",
            "wasted_on": self.today.isoformat(),
            "reason": "expired",
            "estimated_loss": "12500.75",
        }
        self.client.force_login(self.owner)

    def make_entry(self, **changes):
        values = {
            "owner": self.owner,
            "food_name": "Roti",
            "quantity": Decimal("2.00"),
            "unit": "pcs",
            "wasted_on": self.today,
            "reason": "spoiled",
            "estimated_loss": None,
        }
        values.update(changes)
        return FoodWasteLog.objects.create(**values)

    def index(self, params=None, ajax=False):
        headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"} if ajax else {}
        return self.client.get(reverse("waste_audit:index"), params or {}, **headers)

    def test_all_audit_pages_require_login(self):
        self.client.logout()
        routes = [
            reverse("waste_audit:index"),
            reverse("waste_audit:add"),
            reverse("waste_audit:edit", args=[self.entry.pk]),
            reverse("waste_audit:delete", args=[self.entry.pk]),
        ]
        for url in routes:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
                self.assertEqual(self.client.post(url, self.data).status_code, 302)
        self.assertEqual(self.index(ajax=True).status_code, 302)
        self.assertEqual(FoodWasteLog.objects.count(), 2)

    def test_history_and_summary_are_private(self):
        response = self.index()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["entries"]), [self.entry])
        summary = response.context["summary"]
        self.assertEqual(summary["total_entries"], 1)
        self.assertEqual(summary["valued_entries"], 1)
        self.assertEqual(summary["estimated_loss"], Decimal("8500.50"))
        self.assertEqual(summary["top_reason"], self.entry.get_reason_display())
        self.assertEqual(summary["top_reason_count"], 1)
        self.assertNotContains(response, self.secret.food_name)
        self.assertEqual(
            list(response.context["top_foods"]), [{"food_name": "Nasi", "count": 1}]
        )

    def test_other_account_gets_its_own_summary(self):
        self.client.force_login(self.other)
        response = self.index()
        self.assertEqual(list(response.context["entries"]), [self.secret])
        self.assertEqual(
            response.context["summary"]["estimated_loss"], Decimal("987654.32")
        )
        self.assertNotContains(response, ">Nasi<")

    def test_create_preserves_decimal_values_and_ignores_forged_owner(self):
        response = self.client.post(
            reverse("waste_audit:add"), {**self.data, "owner": self.other.pk}
        )
        self.assertRedirects(response, reverse("waste_audit:index"))
        added = FoodWasteLog.objects.get(food_name="Susu")
        self.assertEqual(added.owner, self.owner)
        self.assertEqual(added.quantity, Decimal("0.50"))
        self.assertEqual(added.estimated_loss, Decimal("12500.75"))
        self.assertEqual(added.unit, "liter")
        self.assertEqual(added.wasted_on, self.today)
        self.assertEqual(str(added), "Susu")

    def test_update_keeps_ownership_and_changes_report(self):
        response = self.client.post(
            reverse("waste_audit:edit", args=[self.entry.pk]),
            {**self.data, "owner": self.other.pk},
        )
        self.assertRedirects(response, reverse("waste_audit:index"))
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.owner, self.owner)
        self.assertEqual(self.entry.food_name, "Susu")
        self.assertEqual(self.entry.quantity, Decimal("0.50"))
        self.assertEqual(
            self.index().context["summary"]["estimated_loss"], Decimal("12500.75")
        )

    def test_delete_get_is_confirmation_only_and_post_deletes(self):
        url = reverse("waste_audit:delete", args=[self.entry.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(FoodWasteLog.objects.filter(pk=self.entry.pk).exists())
        self.assertRedirects(self.client.post(url), reverse("waste_audit:index"))
        self.assertFalse(FoodWasteLog.objects.filter(pk=self.entry.pk).exists())
        self.assertTrue(FoodWasteLog.objects.filter(pk=self.secret.pk).exists())
        self.assertEqual(self.index().context["summary"]["total_entries"], 0)

    def test_foreign_records_cannot_be_read_changed_or_deleted(self):
        for route in ("edit", "delete"):
            url = reverse("waste_audit:" + route, args=[self.secret.pk])
            with self.subTest(route=route):
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(url, self.data).status_code, 404)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.food_name, "Makanan Rahasia Akun Lain")
        self.assertEqual(self.secret.estimated_loss, Decimal("987654.32"))

    def test_forged_owner_query_does_not_change_history_scope(self):
        response = self.index({"owner": self.other.pk})
        self.assertEqual(list(response.context["entries"]), [self.entry])
        self.assertNotContains(response, self.secret.food_name)

    def test_missing_record_is_404(self):
        missing_pk = max(self.entry.pk, self.secret.pk) + 100
        for route in ("edit", "delete"):
            self.assertEqual(
                self.client.get(reverse("waste_audit:" + route, args=[missing_pk])).status_code,
                404,
            )

    def test_create_rejects_invalid_input_without_saving(self):
        invalid_cases = [
            ("food_name", ""),
            ("quantity", "0"),
            ("quantity", "-0.5"),
            ("quantity", "not a number"),
            ("quantity", "1.234"),
            ("estimated_loss", "-1"),
            ("estimated_loss", "invalid"),
            ("wasted_on", (self.today + timedelta(days=1)).isoformat()),
            ("wasted_on", "not a date"),
            ("unit", "unsupported"),
            ("reason", "unsupported"),
        ]
        for field, value in invalid_cases:
            with self.subTest(field=field, value=value):
                response = self.client.post(
                    reverse("waste_audit:add"), {**self.data, field: value}
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(FoodWasteLog.objects.count(), 2)

    def test_invalid_update_does_not_change_existing_record(self):
        response = self.client.post(
            reverse("waste_audit:edit", args=[self.entry.pk]),
            {**self.data, "estimated_loss": "-1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("estimated_loss", response.context["form"].errors)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.food_name, "Nasi")
        self.assertEqual(self.entry.estimated_loss, Decimal("8500.50"))

    def test_empty_loss_and_zero_loss_remain_distinct(self):
        for name, cost, expected in (
            ("Tanpa harga", "", None),
            ("Tanpa kerugian", "0", Decimal("0.00")),
        ):
            with self.subTest(cost=cost):
                response = self.client.post(
                    reverse("waste_audit:add"),
                    {**self.data, "food_name": name, "estimated_loss": cost},
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(FoodWasteLog.objects.get(food_name=name).estimated_loss, expected)
        summary = self.index().context["summary"]
        self.assertEqual(summary["total_entries"], 3)
        self.assertEqual(summary["valued_entries"], 2)
        self.assertEqual(summary["estimated_loss"], Decimal("8500.50"))

    def test_no_known_losses_summary_is_unknown_not_zero(self):
        self.entry.estimated_loss = None
        self.entry.save()
        summary = self.index().context["summary"]
        self.assertEqual(summary["total_entries"], 1)
        self.assertEqual(summary["valued_entries"], 0)
        self.assertIsNone(summary["estimated_loss"])

    def test_zero_is_a_known_loss_in_summary(self):
        self.entry.estimated_loss = Decimal("0.00")
        self.entry.save()
        summary = self.index().context["summary"]
        self.assertEqual(summary["valued_entries"], 1)
        self.assertEqual(summary["estimated_loss"], Decimal("0.00"))

    def test_date_filters_are_inclusive(self):
        start = self.today - timedelta(days=3)
        end = self.today - timedelta(days=1)
        first = self.make_entry(food_name="Awal", wasted_on=start, estimated_loss="100")
        last = self.make_entry(food_name="Akhir", wasted_on=end, estimated_loss="200")
        self.make_entry(food_name="Sebelum", wasted_on=start - timedelta(days=1), estimated_loss="900")
        response = self.index({"start_date": start.isoformat(), "end_date": end.isoformat()})
        self.assertSetEqual(set(response.context["entries"]), {first, last})
        summary = response.context["summary"]
        self.assertEqual(summary["total_entries"], 2)
        self.assertEqual(summary["estimated_loss"], Decimal("300.00"))

    def test_one_sided_date_filters(self):
        yesterday = self.today - timedelta(days=1)
        older = self.make_entry(wasted_on=yesterday)
        for params, expected in (
            ({"start_date": self.today.isoformat()}, {self.entry}),
            ({"end_date": yesterday.isoformat()}, {older}),
        ):
            with self.subTest(params=params):
                self.assertSetEqual(set(self.index(params).context["entries"]), expected)

    def test_reason_and_period_filter_update_all_summary_values(self):
        yesterday = self.today - timedelta(days=1)
        expected = self.make_entry(
            food_name="Yoghurt", reason="expired", wasted_on=yesterday, estimated_loss="7000"
        )
        self.make_entry(reason="expired", wasted_on=self.today - timedelta(days=5), estimated_loss="9999")
        response = self.index({"reason": "expired", "start_date": yesterday.isoformat()})
        self.assertEqual(list(response.context["entries"]), [expected])
        summary = response.context["summary"]
        self.assertEqual(summary["total_entries"], 1)
        self.assertEqual(summary["valued_entries"], 1)
        self.assertEqual(summary["estimated_loss"], Decimal("7000.00"))
        self.assertEqual(summary["top_reason"], expected.get_reason_display())
        self.assertEqual(summary["top_reason_count"], 1)
        self.assertEqual(list(response.context["top_foods"]), [{"food_name": "Yoghurt", "count": 1}])

    def test_no_matches_have_empty_report(self):
        response = self.index({"reason": "excess"})
        self.assertFalse(response.context["entries"])
        summary = response.context["summary"]
        self.assertEqual(summary["total_entries"], 0)
        self.assertEqual(summary["valued_entries"], 0)
        self.assertIsNone(summary["estimated_loss"])
        self.assertEqual(summary["top_reason_count"], 0)
        self.assertFalse(response.context["top_foods"])

    def test_invalid_filters_fail_closed_with_errors(self):
        for params in (
            {"start_date": "invalid"},
            {"end_date": "2026-02-30"},
            {"reason": "invalid"},
            {"start_date": self.today.isoformat(), "end_date": (self.today - timedelta(days=1)).isoformat()},
        ):
            with self.subTest(params=params):
                response = self.index(params)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.context["filters_valid"])
                self.assertTrue(response.context["filter_form"].errors)
                self.assertFalse(response.context["entries"])
                self.assertEqual(response.context["summary"]["total_entries"], 0)
                self.assertIsNone(response.context["summary"]["estimated_loss"])
                ajax = self.index(params, ajax=True)
                self.assertEqual(ajax.status_code, 200)
                self.assertIn("html", ajax.json())
                self.assertNotIn(self.secret.food_name, ajax.json()["html"])

    def test_food_frequency_counts_occurrences_across_units(self):
        self.make_entry(food_name="Nasi", quantity="100", unit="gram", estimated_loss="1000")
        self.make_entry(food_name="Nasi", quantity="0.50", unit="kg", estimated_loss=None)
        self.make_entry(food_name="Susu", quantity="1", unit="liter", reason="expired", estimated_loss="2000")
        response = self.index()
        self.assertEqual(list(response.context["top_foods"])[0], {"food_name": "Nasi", "count": 3})
        summary = response.context["summary"]
        self.assertEqual(summary["total_entries"], 4)
        self.assertEqual(summary["estimated_loss"], Decimal("11500.50"))
        self.assertEqual(summary["top_reason_count"], 3)

    def test_ajax_returns_filtered_private_report_and_escaped_names(self):
        malicious = '<script>alert("audit")</script>'
        self.make_entry(food_name=malicious, reason="expired", estimated_loss="12345")
        response = self.index({"reason": "expired"}, ajax=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        html = response.json()["html"]
        self.assertNotIn(malicious, html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn(self.secret.food_name, html)
        self.assertNotIn(">Nasi<", html)
        self.assertIn("12.345", html)
        self.assertNotIn("987.654", html)

    def test_csrf_protects_all_mutations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for url in (
            reverse("waste_audit:add"),
            reverse("waste_audit:edit", args=[self.entry.pk]),
            reverse("waste_audit:delete", args=[self.entry.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(client.post(url, self.data).status_code, 403)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.food_name, "Nasi")
        self.assertEqual(FoodWasteLog.objects.count(), 2)

    def test_forms_use_audit_product_context_and_hide_owner(self):
        for url in (
            reverse("waste_audit:add"),
            reverse("waste_audit:edit", args=[self.entry.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["product_context"], "audit")
                self.assertNotIn("owner", response.context["form"].fields)

    def test_database_rejects_nonpositive_quantity(self):
        for value in (Decimal("0"), Decimal("-1")):
            with self.subTest(value=value):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.make_entry(quantity=value)

    def test_database_rejects_negative_loss_but_allows_unknown(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_entry(estimated_loss=Decimal("-0.01"))
        unknown = self.make_entry(estimated_loss=None)
        self.assertIsNone(unknown.estimated_loss)
