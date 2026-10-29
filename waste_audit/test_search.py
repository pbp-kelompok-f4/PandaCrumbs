from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import FoodWasteLog


class AuditSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create_user(username="search-owner")
        cls.other = users.objects.create_user(username="search-other")
        cls.today = timezone.localdate()
        cls.chicken = cls.make_entry("Ayam goreng", "5000", "spoiled")
        cls.soup = cls.make_entry(
            "Sup ayam", "7000", "excess", cls.today - timedelta(days=10)
        )
        cls.tomato = cls.make_entry("Tomat", "2000", "spoiled")
        cls.tofu = cls.make_entry("Tahu", None, "other")
        cls.secret = cls.make_entry(
            "Ayam rahasia", "999999", "spoiled", owner=cls.other
        )

    @classmethod
    def make_entry(cls, name, loss, reason, date=None, owner=None):
        return FoodWasteLog.objects.create(
            owner=owner or cls.owner, food_name=name,
            quantity=Decimal("1"), unit="pcs", wasted_on=date or cls.today,
            reason=reason,
            estimated_loss=Decimal(loss) if loss is not None else None,
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def index(self, params=None, ajax=False):
        headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"} if ajax else {}
        return self.client.get(reverse("waste_audit:index"), params or {}, **headers)

    def test_name_search_is_case_insensitive_and_owner_scoped(self):
        response = self.index({"q": "  AYAM  "})
        self.assertEqual(response.status_code, 200)
        self.assertSetEqual(set(response.context["entries"]), {self.chicken, self.soup})
        summary = response.context["summary"]
        self.assertEqual(summary["total_entries"], 2)
        self.assertEqual(summary["estimated_loss"], Decimal("12000"))
        self.assertNotContains(response, self.secret.food_name)
        self.assertContains(response, 'id="id_q"')
        self.assertContains(response, "Hasil filter")

    def test_name_search_combines_with_period_and_reason(self):
        response = self.index({
            "q": "ayam", "start_date": self.today.isoformat(),
            "end_date": self.today.isoformat(), "reason": "spoiled",
        })
        self.assertEqual(list(response.context["entries"]), [self.chicken])
        self.assertEqual(response.context["summary"]["estimated_loss"], Decimal("5000"))
        self.assertEqual(response.context["top_foods"], [
            {"food_name": "Ayam goreng", "count": 1}
        ])

    def test_no_name_matches_shows_filtered_empty_state(self):
        response = self.index({"q": "pizza"})
        self.assertFalse(response.context["entries"])
        self.assertEqual(response.context["summary"]["total_entries"], 0)
        self.assertFalse(response.context["top_foods"])
        self.assertContains(response, "Belum ada catatan yang cocok.")
        self.assertNotContains(response, "Mulai dari satu catatan.")
        self.assertContains(response, 'data-audit-reset href="/waste-audit/"')

    def test_empty_and_whitespace_queries_keep_all_owned_records(self):
        for query in ("", "   "):
            with self.subTest(query=query):
                response = self.index({"q": query})
                self.assertEqual(response.context["summary"]["total_entries"], 4)
                self.assertEqual(response.context["filter_form"].cleaned_data["q"], "")
                self.assertContains(response, "Semua catatan")
                self.assertNotContains(response, self.secret.food_name)

    def test_overlong_query_is_rejected_without_exposing_records(self):
        for ajax in (False, True):
            with self.subTest(ajax=ajax):
                response = self.index({"q": "a" * 121}, ajax=ajax)
                self.assertEqual(response.status_code, 200)
                if ajax:
                    html = response.json()["html"]
                else:
                    self.assertIn("q", response.context["filter_form"].errors)
                    self.assertFalse(response.context["entries"])
                    html = response.content.decode()
                self.assertIn("Periksa filter yang dipilih", html)
                self.assertNotIn(self.secret.food_name, html)

    def test_ajax_search_returns_updated_list_totals_and_ranking(self):
        response = self.index({"q": "goreng"}, ajax=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        html = response.json()["html"]
        self.assertIn("Ayam goreng", html)
        self.assertIn("Rp5.000", html)
        self.assertIn("Hasil filter", html)
        self.assertNotIn("Sup ayam", html)
        self.assertNotIn(self.secret.food_name, html)

    def test_unused_pantry_location_parameter_does_not_crash_audit(self):
        response = self.index({"location": "Kulkas"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["total_entries"], 4)

    def test_query_is_escaped_when_rendered_back_into_search_input(self):
        query = '<img src=x onerror="alert(1)">'
        response = self.index({"q": query})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, query)
        self.assertContains(response, "&lt;img")
        self.assertEqual(response.context["summary"]["total_entries"], 0)

    def test_search_never_exposes_a_matching_foreign_record(self):
        response = self.index({"q": "rahasia"})
        self.assertFalse(response.context["entries"])
        self.assertEqual(response.context["summary"]["total_entries"], 0)
        self.assertNotContains(response, self.secret.food_name)

    def test_ayam_does_not_match_bayam_or_longer_words(self):
        self.make_entry("Bayam", "3000", "spoiled")
        self.make_entry("Ayamnya", "4000", "spoiled")
        response = self.index({"q": "ayam"})
        self.assertSetEqual(set(response.context["entries"]), {self.chicken, self.soup})
        self.assertEqual(response.context["summary"]["estimated_loss"], Decimal("12000"))
        html = self.index({"q": "ayam"}, ajax=True).json()["html"]
        self.assertNotIn("Bayam", html)
        self.assertNotIn("Ayamnya", html)

    def test_goreng_matches_mi_and_ayam_but_not_penggorengan(self):
        noodles = self.make_entry("Mi goreng", "6000", "excess")
        self.make_entry("Hasil penggorengan", "3000", "other")
        response = self.index({"q": "goreng"})
        self.assertSetEqual(set(response.context["entries"]), {self.chicken, noodles})

    def test_multiple_words_must_all_match_in_any_order(self):
        self.make_entry("Bayam goreng", "3000", "other")
        for query in ("ayam goreng", "  GORENG   ayam  "):
            with self.subTest(query=query):
                response = self.index({"q": query})
                self.assertEqual(list(response.context["entries"]), [self.chicken])
        self.assertFalse(self.index({"q": "ayam rebus"}).context["entries"])

    def test_punctuation_separates_words_but_digits_do_not(self):
        punctuated = self.make_entry("Ayam-suwir (sisa)", "6000", "other")
        self.make_entry("Ayam2", "3000", "other")
        response = self.index({"q": "ayam"})
        self.assertSetEqual(set(response.context["entries"]), {self.chicken, self.soup, punctuated})

    def test_regex_symbols_in_query_are_literal(self):
        for query in ("ayam|tomat", ".*", "(", "[ayam]"):
            with self.subTest(query=query):
                response = self.index({"q": query})
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.context["entries"])

