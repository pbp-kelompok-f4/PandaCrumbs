from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import PantryItem


class PantryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "owner", password="testing-password-123"
        )
        self.other = get_user_model().objects.create_user(
            "other", password="testing-password-123"
        )
        self.today = timezone.localdate()
        self.item = PantryItem.objects.create(
            owner=self.user,
            name="Mangga",
            category="Buah Segar",
            quantity=2,
            location="Kulkas",
            expires_on=self.today + timedelta(days=2),
        )
        self.data = dict(
            name="Susu",
            category="Susu",
            quantity=3,
            unit="pcs",
            location="Kulkas",
            expires_on=self.today.isoformat(),
            stored_on=self.today.isoformat(),
        )
        self.client.force_login(self.user)

    def test_anonymous_cannot_read_pantry(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("pantry:index")).status_code, 302)

    def test_owner_reads_only_their_items(self):
        PantryItem.objects.create(
            owner=self.other,
            name="Secret food",
            category="Protein",
            quantity=1,
            location="Kulkas",
            expires_on=self.today,
        )
        response = self.client.get(reverse("pantry:index"))
        self.assertContains(response, "Mangga")
        self.assertNotContains(response, "Secret food")

    def test_pantry_items_are_grouped_by_location_then_urgency(self):
        PantryItem.objects.create(
            owner=self.user,
            name="Bayam",
            category="Sayuran",
            quantity=1,
            location="Freezer",
            expires_on=self.today - timedelta(days=1),
        )
        PantryItem.objects.create(
            owner=self.user,
            name="Beras",
            category="Bahan Pokok",
            quantity=1,
            location="Rak Dapur",
            expires_on=self.today + timedelta(days=10),
        )
        response = self.client.get(reverse("pantry:index"))
        groups = response.context["location_groups"]
        self.assertEqual(
            [group["location"] for group in groups],
            ["Kulkas", "Freezer", "Rak Dapur"],
        )
        self.assertEqual(groups[0]["status_groups"][0]["status"], "soon")
        self.assertEqual(groups[1]["status_groups"][0]["status"], "expired")
        self.assertEqual(groups[2]["status_groups"][0]["status"], "safe")
        self.assertContains(response, "Hampir Basi")
        self.assertContains(response, "Bayam")
        self.assertContains(response, "Beras")

    def test_filter_status_buttons_target_the_get_filter_form(self):
        response = self.client.get(reverse("pantry:index"))
        self.assertContains(response, 'id="pantry-filter-form"')
        self.assertContains(response, 'data-status-filter')
        self.assertContains(response, 'form="pantry-filter-form"')

    def test_create_ignores_forged_owner(self):
        self.client.post(reverse("pantry:add"), {**self.data, "owner": self.other.pk})
        self.assertEqual(PantryItem.objects.get(name="Susu").owner, self.user)

    def test_update_and_delete(self):
        self.assertEqual(
            self.client.post(
                reverse("pantry:edit", args=[self.item.pk]), self.data
            ).status_code,
            302,
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Susu")
        self.assertEqual(
            self.client.get(reverse("pantry:delete", args=[self.item.pk])).status_code,
            200,
        )
        self.assertTrue(PantryItem.objects.filter(pk=self.item.pk).exists())
        self.client.post(reverse("pantry:delete", args=[self.item.pk]))
        self.assertFalse(PantryItem.objects.filter(pk=self.item.pk).exists())

    def test_cross_user_mutations_are_blocked(self):
        self.client.force_login(self.other)
        for route in ["edit", "delete", "consume"]:
            self.assertEqual(
                self.client.post(
                    reverse("pantry:" + route, args=[self.item.pk]), self.data
                ).status_code,
                404,
            )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 2)

    def test_status_boundaries(self):
        for days, expected in [(-1, "expired"), (0, "soon"), (3, "soon"), (4, "safe")]:
            self.item.expires_on = self.today + timedelta(days=days)
            self.assertEqual(self.item.status, expected)
            self.assertTrue(self.item.status_label)

    def test_ajax_filters(self):
        for params, expected in [
            ({"status": "soon"}, True),
            ({"status": "safe"}, False),
            ({"status": "expired"}, False),
            ({"q": "mang"}, True),
            ({"category": "Susu"}, False),
            ({"location": "Freezer"}, False),
        ]:
            response = self.client.get(
                reverse("pantry:index"), params, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual("Mangga" in response.json()["html"], expected)

    def test_consume_decrements_then_deletes_and_requires_post(self):
        url = reverse("pantry:consume", args=[self.item.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(
            self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code,
            200,
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)
        self.client.post(url)
        self.assertFalse(PantryItem.objects.filter(pk=self.item.pk).exists())
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_consume_all_deletes_item_via_ajax_and_regular_post(self):
        url = reverse("pantry:consume", args=[self.item.pk])
        response = self.client.post(
            url,
            {"consume_all": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "deleted": True})
        self.assertFalse(PantryItem.objects.filter(pk=self.item.pk).exists())

        second_item = PantryItem.objects.create(
            owner=self.user,
            name="Pisang",
            category="Buah Segar",
            quantity=3,
            location="Kulkas",
            expires_on=self.today + timedelta(days=5),
        )
        response = self.client.post(
            reverse("pantry:consume", args=[second_item.pk]),
            {"consume_all": "1"},
            follow=True,
        )
        self.assertContains(response, "Bahan ditandai habis dikonsumsi.")
        self.assertFalse(PantryItem.objects.filter(pk=second_item.pk).exists())

    def test_invalid_quantity_and_future_storage_date(self):
        for changes in [
            {"quantity": 0},
            {"quantity": -2},
            {"stored_on": (self.today + timedelta(days=1)).isoformat()},
        ]:
            response = self.client.post(reverse("pantry:add"), {**self.data, **changes})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        self.assertEqual(PantryItem.objects.count(), 1)

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(
            client.post(reverse("pantry:consume", args=[self.item.pk])).status_code, 403
        )

    def test_form_pages(self):
        for url in [reverse("pantry:add"), reverse("pantry:edit", args=[self.item.pk])]:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(str(self.item), "Mangga")

    def test_status_filter_matches_display_at_each_expiry_boundary(self):
        for days, status in [(-1, "expired"), (0, "soon"), (3, "soon"), (4, "safe")]:
            with self.subTest(days=days):
                self.item.expires_on = self.today + timedelta(days=days)
                self.item.save(update_fields=["expires_on"])
                self.assertEqual(self.item.status, status)
                for selected in ["expired", "soon", "safe", "unknown"]:
                    response = self.client.get(
                        reverse("pantry:index"),
                        {"status": selected},
                        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                    )
                    self.assertEqual(
                        "Mangga" in response.json()["html"],
                        selected in (status, "unknown"),
                    )

    def test_ajax_returns_the_same_cards_as_the_full_page(self):
        params = {"q": "Mangga", "status": "soon"}
        full = self.client.get(reverse("pantry:index"), params)
        ajax = self.client.get(
            reverse("pantry:index"), params, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        # CSRF tokens rotate per render; compare the rendered content after normalizing them.
        import re

        normalize = lambda html: re.sub(
            r'name="csrfmiddlewaretoken" value="[^"]+"',
            'name="csrfmiddlewaretoken"',
            html,
        )
        self.assertIn(normalize(ajax.json()["html"]), normalize(full.content.decode()))
