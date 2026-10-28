from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from pantry.models import PantryItem
from .forms import ChallengePlanForm
from .models import ChallengePlan, Completion
from .services import progress_for


class HabitChallengeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("habit-user")
        cls.other = get_user_model().objects.create_user("other-user")

    def setUp(self):
        self.client.force_login(self.user)
        self.today = timezone.localdate()
        self.index = reverse("habit_challenge:index")

    def complete(self, kind="pantry", **data):
        return self.client.post(reverse("habit_challenge:complete", args=[kind]), {
            "food": "Nasi goreng", "confirmed": "on", **data,
        })

    def plan(self, **kwargs):
        return ChallengePlan.objects.create(**{
            "user": self.user, "title": "Habiskan stok", "kind": "pantry",
            "target_days": 3, "starts_on": self.today,
            "ends_on": self.today + timedelta(days=6), **kwargs,
        })

    def test_login_required_and_mutations_require_post(self):
        endpoint = reverse("habit_challenge:complete", args=["pantry"])
        self.assertEqual(self.client.get(endpoint).status_code, 405)
        self.client.logout()
        for url in [self.index, endpoint, reverse("habit_challenge:plan_add")]:
            self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(Completion.objects.count(), 0)

    def test_empty_dashboard_and_navigation(self):
        response = self.client.get(self.index)
        self.assertContains(response, 'aria-current="page">Habit Challenge')
        self.assertEqual(response.context["progress"]["total"], 0)
        self.assertEqual(response.context["progress"]["level"], 1)
        self.assertContains(response, "Tambah bahan ke pantry")
        self.assertContains(response, "Community segera hadir")

    def test_only_owned_unexpired_pantry_is_suggested(self):
        for user, name, days in [(self.user, "Bayam", 2), (self.other, "Rahasia", 2), (self.user, "Basi", -1)]:
            PantryItem.objects.create(owner=user, name=name, category="Sayuran", location="Kulkas", expires_on=self.today + timedelta(days=days))
        response = self.client.get(self.index)
        self.assertContains(response, "Bayam")
        self.assertNotContains(response, "Rahasia")
        self.assertNotContains(response, "Basi")

    def test_server_rewards_once_per_kind_per_day(self):
        for kind in ["pantry", "leftovers", "share"]:
            self.assertEqual(self.complete(kind, points=999, user=self.other.pk).status_code, 302)
            self.complete(kind)
        self.assertEqual(Completion.objects.filter(user=self.user).count(), 3)
        self.assertFalse(Completion.objects.filter(user=self.other).exists())
        self.assertEqual(progress_for(Completion.objects.all())["total"], 35)
        with patch("habit_challenge.views.timezone.localdate", return_value=self.today + timedelta(days=1)):
            self.complete()
        self.assertEqual(Completion.objects.count(), 4)

    def test_checkin_validation_csrf_and_unknown_kind(self):
        for data in [{"food": " "}, {"food": "x" * 121}, {"confirmed": ""}]:
            self.assertEqual(self.complete(**data).status_code, 400)
        self.assertEqual(self.complete("invalid").status_code, 404)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        self.assertEqual(csrf_client.post(reverse("habit_challenge:complete", args=["pantry"]), {"food": "Nasi", "confirmed": "on"}).status_code, 403)
        self.assertFalse(Completion.objects.exists())

    def test_database_guards_duplicates_and_invalid_rewards(self):
        self.complete()
        for kind, points in [("pantry", 10), ("share", 999), ("invalid", 10)]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Completion.objects.create(user=self.user, kind=kind, points=points, food="Nasi")

    def test_ajax_checkin_updates_dashboard_and_escapes_food(self):
        endpoint = reverse("habit_challenge:complete", args=["share"])
        response = self.client.post(endpoint, {"food": "<script>alert(1)</script>", "confirmed": "on"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertIn("15 poin total", response.json()["html"])
        self.assertIn("&lt;script&gt;", response.json()["html"])
        self.assertNotIn("<script>alert", response.json()["html"])
        invalid = self.client.post(endpoint, {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("food", invalid.json()["errors"])

    def test_confirmation_uses_saved_food_and_does_not_reward_duplicate(self):
        endpoint = reverse("habit_challenge:complete", args=["share"])
        headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        response = self.client.post(endpoint, {"food": "Sup sayur (2 porsi)", "confirmed": "on"}, **headers)
        self.assertEqual(response.json()["completion"], {
            "created": True, "food": "Sup sayur (2 porsi)", "points": 15,
            "action": "dibagikan", "reward": "setelah berbagi",
        })
        duplicate = self.client.post(endpoint, {"food": "Nama lain", "confirmed": "on"}, **headers)
        result = duplicate.json()["completion"]
        self.assertFalse(result["created"])
        self.assertEqual(result["points"], 0)
        self.assertEqual(result["food"], "Sup sayur (2 porsi)")
        self.assertEqual(Completion.objects.count(), 1)

    def test_cooking_confirmation_and_accessible_dialogs(self):
        response = self.client.post(reverse("habit_challenge:complete", args=["leftovers"]),
            {"food": "Nasi matang", "confirmed": "on"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.json()["completion"]["action"], "diolah")
        self.assertEqual(response.json()["completion"]["points"], 10)
        page = self.client.get(self.index)
        self.assertContains(page, 'id="habit-checkin-dialog"')
        self.assertContains(page, 'aria-labelledby="habit-success-title"')
        self.assertContains(page, 'aria-label="Tutup konfirmasi"')

    def test_progress_level_boundaries_and_streak_gap(self):
        for days in [0, 1, 2, 4]:
            Completion.objects.create(user=self.user, kind="pantry", points=10, food="Nasi", completed_on=self.today - timedelta(days=days))
        qs = Completion.objects.filter(user=self.user)
        self.assertEqual(progress_for(qs)["streak"], 3)
        self.assertEqual(progress_for(qs, self.today + timedelta(days=1))["streak"], 3)
        self.assertEqual(progress_for(qs, self.today + timedelta(days=2))["streak"], 0)
        self.complete("leftovers")
        result = progress_for(qs)
        self.assertEqual((result["total"], result["level"], result["earned"], result["target"]), (50, 2, 0, 100))
        for days in range(5, 12):
            Completion.objects.create(user=self.user, kind="pantry", points=10, food="Nasi", completed_on=self.today - timedelta(days=days))
        result = progress_for(qs)
        self.assertEqual((result["total"], result["level"], result["earned"], result["target"]), (120, 2, 70, 100))

    def test_other_accounts_cannot_see_history_or_points(self):
        Completion.objects.create(user=self.other, kind="share", points=15, food="Makanan privat")
        response = self.client.get(self.index)
        self.assertNotContains(response, "Makanan privat")
        self.assertEqual(response.context["progress"]["total"], 0)

    def test_plan_create_edit_checkin_delete_keeps_points(self):
        data = {"title": "Hemat bahan", "kind": "pantry", "target_days": 3,
                "starts_on": self.today, "ends_on": self.today + timedelta(days=6), "category": "en:dairies"}
        self.assertEqual(self.client.post(reverse("habit_challenge:plan_add"), data).status_code, 302)
        plan = ChallengePlan.objects.get()
        self.assertEqual(plan.user, self.user)
        self.assertEqual(self.client.post(reverse("habit_challenge:plan_edit", args=[plan.pk]), {**data, "target_days": 4}).status_code, 302)
        self.complete(plan=plan.pk)
        response = self.client.get(self.index)
        self.assertEqual(response.context["plans"][0].checkin_count, 1)
        self.assertEqual(response.context["plans"][0].percent, 25)
        self.assertEqual(self.client.get(reverse("habit_challenge:plan_delete", args=[plan.pk])).status_code, 200)
        self.assertTrue(ChallengePlan.objects.exists())
        self.client.post(reverse("habit_challenge:plan_delete", args=[plan.pk]))
        self.assertFalse(ChallengePlan.objects.exists())
        self.assertIsNone(Completion.objects.get().plan)
        self.assertEqual(progress_for(Completion.objects.all())["total"], 10)

    def test_plan_ownership_and_checkin_kind_period(self):
        private = self.plan(user=self.other)
        for action in ["plan_edit", "plan_delete"]:
            url = reverse(f"habit_challenge:{action}", args=[private.pk])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, {}).status_code, 404)
        for plan in [private, self.plan(kind="share"), self.plan(starts_on=self.today + timedelta(days=1)), self.plan(starts_on=self.today - timedelta(days=7), ends_on=self.today - timedelta(days=1))]:
            self.assertEqual(self.complete(plan=plan.pk).status_code, 400)
        self.assertFalse(Completion.objects.exists())

    def test_plan_validation_and_recorded_dates_are_preserved(self):
        plan = self.plan()
        self.complete(plan=plan.pk)
        data = {"title": "Target", "kind": "pantry", "target_days": 3,
                "starts_on": self.today, "ends_on": self.today + timedelta(days=6)}
        for change in [{"ends_on": self.today - timedelta(days=1)}, {"target_days": 0}, {"target_days": 8}, {"kind": "share"}, {"starts_on": self.today + timedelta(days=1)}]:
            form = ChallengePlanForm({**data, **change}, instance=ChallengePlan.objects.get(pk=plan.pk))
            self.assertFalse(form.is_valid(), change)

    def test_plan_form_has_category_filtered_lookup(self):
        response = self.client.get(reverse("habit_challenge:plan_add"))
        self.assertContains(response, 'id="habit-product-search"')
        self.assertContains(response, 'value="en:dairies"')
        self.assertContains(response, reverse("main:products"))
