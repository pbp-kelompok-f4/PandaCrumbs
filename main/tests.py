from io import StringIO
from unittest.mock import Mock, patch
import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from main.products import pantry_category_for
from pantry.models import PantryItem
from recipes.models import Recipe


class AccountTests(TestCase):
    def test_landing_and_login_pages(self):
        for url in ["/", "/accounts/login/", "/accounts/register/"]:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_registration_and_password_validation(self):
        data = {
            "username": "newuser",
            "email": "test@example.com",
            "password1": "short",
            "password2": "short",
        }
        response = self.client.post(reverse("main:register"), data)
        self.assertTrue(response.context["form"].errors)
        data.update(
            password1="long-test-secret-135!", password2="long-test-secret-135!"
        )
        self.assertEqual(
            self.client.post(reverse("main:register"), data).status_code, 302
        )
        self.assertEqual(self.client.get("/pantry/").status_code, 200)
        self.assertEqual(self.client.get(reverse("main:register")).status_code, 302)
        self.assertEqual(self.client.get("/accounts/logout/").status_code, 405)
        self.client.post("/accounts/logout/")
        self.assertEqual(self.client.get("/pantry/").status_code, 302)

    def test_login_rejects_external_redirect(self):
        get_user_model().objects.create_user("user", password="long-test-secret-135!")
        response = self.client.post(
            "/accounts/login/",
            {
                "username": "user",
                "password": "long-test-secret-135!",
                "next": "https://example.com/",
            },
        )
        self.assertEqual(response.url, "/pantry/")

    def test_seed_is_idempotent_and_keeps_password(self):
        user = get_user_model().objects.create_user(
            "demo", password="original-password"
        )
        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(PantryItem.objects.count(), 3)
        self.assertEqual(Recipe.objects.count(), 3)
        user.refresh_from_db()
        self.assertTrue(user.check_password("original-password"))


class ProductSearchTests(TestCase):
    def setUp(self):
        cache.clear()
        user = get_user_model().objects.create_user(
            "searcher", password="long-test-secret"
        )
        self.client.force_login(user)
        self.url = reverse("main:products")

    def tearDown(self):
        cache.clear()

    def test_auth_and_min_length(self):
        self.assertEqual(self.client.get(self.url, {"q": "a"}).status_code, 400)
        self.client.logout()
        self.assertEqual(self.client.get(self.url, {"q": "milk"}).status_code, 302)

    @patch("main.products.requests.get")
    def test_search_cache_category_and_throttle(self, get):
        get.return_value = Mock(
            json=lambda: {
                "products": [
                    {"product_name": "Milk", "code": "123", "categories": "Dairy"}
                ]
            }
        )
        params = {"q": "milk", "category": "dairy"}
        for _ in range(2):
            response = self.client.get(self.url, params)
            self.assertEqual(response.json()["products"][0]["name"], "Milk")
        self.assertEqual(get.call_count, 1)
        self.assertEqual(get.call_args.kwargs["params"]["tag_0"], "dairy")
        self.assertEqual(self.client.get(self.url, {"q": "bread"}).status_code, 429)

    @patch("main.products.requests.get", side_effect=requests.Timeout)
    def test_api_timeout_returns_actionable_error(self, get):
        response = self.client.get(self.url, {"q": "milk"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("manual", response.json()["error"])

    @patch("main.products.requests.get")
    def test_invalid_upstream_payload(self, get):
        get.return_value = Mock(json=lambda: {"products": None})
        self.assertEqual(self.client.get(self.url, {"q": "milk"}).status_code, 503)


@override_settings(DEBUG=False, STATIC_ROOT="", SECURE_SSL_REDIRECT=True)
class ProductionStaticTests(TestCase):
    """PWS starts from source without a collected static manifest."""

    def test_pages_and_assets_without_collectstatic(self):
        from django.contrib.staticfiles.storage import staticfiles_storage

        for url in ["/", "/accounts/login/", "/accounts/register/", "/recipes/"]:
            with self.subTest(page=url):
                self.assertEqual(self.client.get(url, secure=True).status_code, 200)
        for asset in [
            "main/css/app.css",
            "main/css/fonts.css",
            "main/css/tailwind.css",
            "main/js/app.js",
            "main/fonts/font-0.ttf",
            "main/images/1-2-imgImage3.png",
        ]:
            with self.subTest(asset=asset):
                response = self.client.get(staticfiles_storage.url(asset), secure=True)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(b"".join(response.streaming_content))
                response.close()


class ProductSearchContractTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.client.force_login(get_user_model().objects.create_user("lookup-contract"))
        self.url = reverse("main:products")

    @patch("main.products.requests.get")
    def test_empty_results_are_cached_and_do_not_consume_another_search(self, get):
        get.return_value = Mock(json=lambda: {"products": []})
        for _ in range(2):
            response = self.client.get(self.url, {"q": "missing"})
            self.assertEqual(response.json(), {"products": []})
        self.assertEqual(get.call_count, 1)
        self.assertEqual(self.client.get(self.url, {"q": "another"}).status_code, 429)

    @patch("main.products.requests.get")
    def test_normalized_query_and_product_fields_keep_existing_limits(self, get):
        get.return_value = Mock(
            json=lambda: {
                "products": [
                    None,
                    "invalid",
                    {},
                    {"product_name": ""},
                    {
                        "product_name": "n" * 130,
                        "code": "b" * 40,
                        "categories": "c" * 170,
                        "image_front_small_url": "https://example.com/image.png",
                    },
                ]
            }
        )
        response = self.client.get(
            self.url, {"q": "  " + "q" * 90 + "  ", "category": "  " + "c" * 70 + "  "}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "products": [
                    {
                        "name": "n" * 120,
                        "barcode": "b" * 32,
                        "category": "c" * 160,
                        "pantry_category": "",
                        "image": "https://example.com/image.png",
                    }
                ]
            },
        )
        self.assertEqual(get.call_args.kwargs["params"]["search_terms"], "q" * 80)
        self.assertEqual(get.call_args.kwargs["params"]["tag_0"], "c" * 60)
        self.assertEqual(get.call_args.kwargs["timeout"], (3, 8))

    def test_open_food_facts_categories_map_to_pantry_choices(self):
        for categories, expected in [
            ("Yogurts, dairy products", "Yogurt"),
            ("Fresh fruits", "Buah Segar"),
            ("Frozen vegetables", "Sayuran"),
            ("Milk and cheese", "Susu"),
            ("Meat, fish and eggs", "Protein"),
            ("Bread, rice and cereals", "Bahan Pokok"),
            ("Snacks and beverages", ""),
        ]:
            with self.subTest(categories=categories):
                self.assertEqual(pantry_category_for(categories), expected)

    @patch("main.products.requests.get")
    def test_http_and_json_failures_keep_manual_entry_available(self, get):
        for error in [requests.HTTPError(), ValueError(), TypeError()]:
            with self.subTest(error=type(error).__name__):
                cache.clear()
                get.side_effect = error
                response = self.client.get(self.url, {"q": "milk"})
                self.assertEqual(response.status_code, 503)
                self.assertIn("manual", response.json()["error"])

    @patch("main.products.requests.get")
    def test_invalid_queries_and_post_do_not_call_upstream(self, get):
        self.assertEqual(self.client.get(self.url, {"q": " a "}).status_code, 400)
        self.assertEqual(self.client.post(self.url, {"q": "milk"}).status_code, 405)
        get.assert_not_called()
