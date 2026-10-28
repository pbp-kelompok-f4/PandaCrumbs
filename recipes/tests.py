from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from .models import Recipe, Bookmark


class RecipeTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            "owner", password="testing-password-123"
        )
        self.other = get_user_model().objects.create_user(
            "other", password="testing-password-123"
        )
        self.data = dict(
            title="Nasi Goreng",
            ingredients="nasi\ntelur\nwortel",
            steps="Tumis bahan.\nMasak nasi.",
            portions=2,
            minutes=10,
        )
        self.recipe = Recipe.objects.create(author=self.owner, **self.data)

    def test_public_can_read_list_and_detail(self):
        for url in [
            reverse("recipes:index"),
            reverse("recipes:detail", args=[self.recipe.pk]),
        ]:
            self.assertContains(self.client.get(url), "Nasi Goreng")
        self.assertEqual(str(self.recipe), "Nasi Goreng")

    def test_anonymous_mutations_and_private_tabs_require_login(self):
        for name in ["add", "edit", "delete", "bookmark"]:
            args = [] if name == "add" else [self.recipe.pk]
            self.assertEqual(
                self.client.post(
                    reverse("recipes:" + name, args=args), self.data
                ).status_code,
                302,
            )
        for tab in ["saved", "mine"]:
            self.assertEqual(
                self.client.get(reverse("recipes:index"), {"tab": tab}).status_code, 302
            )

    def test_owner_crud(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("recipes:add")).status_code, 200)
        self.client.post(
            reverse("recipes:add"),
            {**self.data, "title": "Sup", "author": self.other.pk},
        )
        self.assertEqual(Recipe.objects.get(title="Sup").author, self.owner)
        self.client.post(
            reverse("recipes:edit", args=[self.recipe.pk]),
            {**self.data, "title": "Nasi Baru"},
        )
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, "Nasi Baru")
        self.assertEqual(
            self.client.get(
                reverse("recipes:delete", args=[self.recipe.pk])
            ).status_code,
            200,
        )
        self.client.post(reverse("recipes:delete", args=[self.recipe.pk]))
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())

    def test_other_user_cannot_edit_delete(self):
        self.client.force_login(self.other)
        for route in ["edit", "delete"]:
            self.assertEqual(
                self.client.post(
                    reverse("recipes:" + route, args=[self.recipe.pk]), self.data
                ).status_code,
                404,
            )

    def test_bookmark_idempotence_and_privacy(self):
        self.client.force_login(self.other)
        url = reverse("recipes:bookmark", args=[self.recipe.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        for _ in range(2):
            self.assertTrue(
                self.client.post(
                    url, {"saved": "1"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
                ).json()["saved"]
            )
        self.assertEqual(Bookmark.objects.count(), 1)
        self.assertContains(
            self.client.get(reverse("recipes:index"), {"tab": "saved"}), "Nasi Goreng"
        )
        self.client.force_login(self.owner)
        self.assertNotContains(
            self.client.get(reverse("recipes:index"), {"tab": "saved"}), "Nasi Goreng"
        )
        self.client.force_login(self.other)
        self.client.post(url, {"saved": "0"})
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_database_filters_match_all_selected_ingredients(self):
        for params, expected in [
            ({"ingredient": ["nasi", "telur"]}, True),
            ({"ingredient": ["nasi", "tempe"]}, False),
            ({"q": "wortel"}, True),
            ({"q": "roti"}, False),
        ]:
            result = self.client.get(
                reverse("recipes:index"), params, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            ).json()["html"]
            self.assertEqual("Nasi Goreng" in result, expected)

    def test_mine_filter(self):
        self.client.force_login(self.other)
        self.assertNotContains(
            self.client.get(reverse("recipes:index"), {"tab": "mine"}), "Nasi Goreng"
        )
        self.client.force_login(self.owner)
        self.assertContains(
            self.client.get(reverse("recipes:index"), {"tab": "mine"}), "Nasi Goreng"
        )

    def test_invalid_portions_and_xss_escaping(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("recipes:add"), {**self.data, "portions": 0}
        )
        self.assertTrue(response.context["form"].errors)
        self.recipe.title = "<script>alert(1)</script>"
        self.recipe.save()
        response = self.client.get(reverse("recipes:index"))
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(
            client.post(
                reverse("recipes:bookmark", args=[self.recipe.pk]), {"saved": "1"}
            ).status_code,
            403,
        )

    def test_ajax_and_full_page_share_counts_and_filtered_results(self):
        self.client.force_login(self.owner)
        Bookmark.objects.create(user=self.owner, recipe=self.recipe)
        params = {"tab": "saved", "ingredient": ["nasi", "telur"]}
        full = self.client.get(reverse("recipes:index"), params)
        ajax = self.client.get(
            reverse("recipes:index"), params, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        import re

        normalize = lambda html: re.sub(
            r'name="csrfmiddlewaretoken" value="[^"]+"',
            'name="csrfmiddlewaretoken"',
            html,
        )
        self.assertIn(normalize(ajax.json()["html"]), normalize(full.content.decode()))
        self.assertContains(full, "Tersimpan (1)")

    def test_private_tab_login_preserves_complete_search(self):
        from urllib.parse import parse_qs, urlsplit

        response = self.client.get(reverse("recipes:index"), {
            "tab": "saved", "q": "Nasi & telur", "ingredient": ["nasi", "telur"],
        })
        next_url = parse_qs(urlsplit(response.url).query)["next"][0]
        self.assertEqual(parse_qs(urlsplit(next_url).query), {
            "tab": ["saved"], "q": ["Nasi & telur"], "ingredient": ["nasi", "telur"],
        })

    def test_empty_post_displays_validation_errors_without_saving(self):
        self.client.force_login(self.owner)
        for url in [reverse("recipes:add"), reverse("recipes:edit", args=[self.recipe.pk])]:
            response = self.client.post(url, {})
            self.assertTrue(response.context["form"].is_bound)
            self.assertIn("title", response.context["form"].errors)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, "Nasi Goreng")
        self.assertEqual(Recipe.objects.count(), 1)

    def test_invalid_bookmark_action_does_not_delete_saved_recipe(self):
        self.client.force_login(self.owner)
        Bookmark.objects.create(user=self.owner, recipe=self.recipe)
        for value in [None, "", "true", "2"]:
            with self.subTest(value=value):
                response = self.client.post(
                    reverse("recipes:bookmark", args=[self.recipe.pk]),
                    {} if value is None else {"saved": value},
                    HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json())
                self.assertTrue(Bookmark.objects.filter(user=self.owner, recipe=self.recipe).exists())

    def test_remove_and_reset_ingredients_preserve_search_and_private_tab(self):
        self.client.force_login(self.owner)
        Bookmark.objects.create(user=self.owner, recipe=self.recipe)
        for action, expected in [({"remove_ingredient": "tempe"}, ["telur"]), ({"reset_ingredients": "1"}, [])]:
            with self.subTest(action=action):
                response = self.client.get(reverse("recipes:index"), {
                    "tab": "saved", "q": "Nasi", "ingredient": ["telur", "tempe"], **action,
                })
                self.assertEqual(response.context["ingredients"], expected)
                self.assertEqual(response.context["tab"], "saved")
                self.assertEqual(response.context["q"], "Nasi")
                self.assertContains(response, "Nasi Goreng")

    def test_unknown_tab_falls_back_to_all(self):
        response = self.client.get(reverse("recipes:index"), {"tab": "unknown"})
        self.assertEqual(response.context["tab"], "all")
        self.assertContains(response, "Nasi Goreng")

    def test_all_recipe_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for name, args in [("add", []), ("edit", [self.recipe.pk]), ("delete", [self.recipe.pk])]:
            self.assertEqual(client.post(reverse("recipes:" + name, args=args), self.data).status_code, 403)
        self.assertEqual(Recipe.objects.count(), 1)

    def test_delete_also_removes_bookmarks_without_touching_other_recipes(self):
        other = Recipe.objects.create(author=self.other, **{**self.data, "title": "Sup"})
        Bookmark.objects.create(user=self.other, recipe=self.recipe)
        self.client.force_login(self.owner)
        self.client.post(reverse("recipes:delete", args=[self.recipe.pk]))
        self.assertFalse(Bookmark.objects.filter(recipe_id=self.recipe.pk).exists())
        self.assertTrue(Recipe.objects.filter(pk=other.pk).exists())
