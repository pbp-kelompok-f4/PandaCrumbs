from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from community.models import FoodOffer, FoodClaim
from community.forms import FoodOfferForm, FoodClaimForm

class CommunityModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.donor_user = User.objects.create_user(username="donor_pbp", password="password123")
        self.claimer_user = User.objects.create_user(username="claimer_pbp", password="password123")

        self.future_time = timezone.now() + timedelta(days=2)
        self.past_time = timezone.now() - timedelta(days=1)

        self.offer = FoodOffer.objects.create(
            donor=self.donor_user,
            title="Roti Tawar Gandum",
            category="BAKERY",
            description="Masih segar, tersisa 5 lembar",
            portions=5,
            remaining_portions=5,
            pickup_location="Fasilkom UI Depok",
            contact_info="08123456789",
            pickup_deadline=self.future_time,
            latitude=-6.362700,
            longitude=106.827100,
            status="AVAILABLE",
        )

    # --- PENGUJIAN MODEL & LOGIKA BISNIS ---
    def test_model_str_and_properties(self):
        self.assertIn("Roti Tawar Gandum", str(self.offer))
        self.assertFalse(self.offer.is_expired)
        self.assertEqual(self.offer.status, "AVAILABLE")

    # --- PENGUJIAN FORM VALIDATION ---
    def test_food_offer_form_validation(self):
        # Validasi porsi tidak boleh 0 atau negatif
        invalid_data = {
            "title": "Donat Cokelat",
            "category": "SNACKS",
            "description": "Deskripsi makanan",
            "portions": 0,
            "pickup_location": "Kutek",
            "contact_info": "0812345",
            "pickup_deadline": self.future_time.strftime("%Y-%m-%dT%H:%M"),
            "latitude": -6.36,
            "longitude": 106.82,
        }
        form = FoodOfferForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("portions", form.errors)

        # Validasi batas penjemputan tidak boleh di masa lampau
        invalid_data["portions"] = 2
        invalid_data["pickup_deadline"] = self.past_time.strftime("%Y-%m-%dT%H:%M")
        form_expired = FoodOfferForm(data=invalid_data)
        self.assertFalse(form_expired.is_valid())
        self.assertIn("pickup_deadline", form_expired.errors)

    # --- PENGUJIAN VIEW & AKSES AUTH ---
    def test_catalog_view_accessible(self):
        response = self.client.get(reverse("community:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Roti Tawar Gandum")

    def test_create_offer_requires_login(self):
        response = self.client.get(reverse("community:add"))
        self.assertEqual(response.status_code, 302)

    def test_create_offer_authenticated(self):
        self.client.login(username="donor_pbp", password="password123")

        # Ambil pilihan kategori valid pertama langsung dari model agar pasti cocok dengan choices
        category_field = FoodOffer._meta.get_field("category")
        valid_category = category_field.choices[0][0] if category_field.choices else "MEALS"

        post_data = {
            "title": "Nasi Kotak Ayam",
            "category": valid_category,
            "description": "Nasi kotak higienis",
            "portions": 3,
            "pickup_location": "Kantin Vokasi",
            "contact_info": "08199988877",
            "pickup_deadline": self.future_time.strftime("%Y-%m-%dT%H:%M"),
            "latitude": "-6.365000",
            "longitude": "106.828000",
            "image_url": "",
        }
        response = self.client.post(reverse("community:add"), data=post_data)

        # Cetak error spesifik form jika validasi masih tertahan
        if response.status_code != 302 and response.context and "form" in response.context:
            print("\n[DEBUG FORM ERRORS]:", response.context["form"].errors)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(FoodOffer.objects.filter(title="Nasi Kotak Ayam").exists())

    # --- PENGUJIAN TRANSAKSI AJAX CLAIM ---
    def test_ajax_claim_food_success(self):
        self.client.login(username="claimer_pbp", password="password123")
        claim_url = reverse("community:claim", args=[self.offer.pk])
        
        response = self.client.post(
            claim_url,
            data={"portions_claimed": 2, "notes": "Saya ambil jam 16.00"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.remaining_portions, 3)
        self.assertTrue(FoodClaim.objects.filter(offer=self.offer, claimer=self.claimer_user).exists())

    def test_donor_cannot_claim_own_offer(self):
        self.client.login(username="donor_pbp", password="password123")
        claim_url = reverse("community:claim", args=[self.offer.pk])
        response = self.client.post(
            claim_url,
            data={"portions_claimed": 1, "notes": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)