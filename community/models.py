from django.db import models
from datetime import timedelta
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone

# Create your models here.
class FoodOffer(models.Model):
    STATUS_CHOICES =[
        ("AVAILABLE", "Tersedia"),
        ("FULLY_CLAIMED", "Habis Diklaim"),
        ("COMPLETED", "Selesai"),
        ("CANCELLED", "Dibatalkan"),
    ]

    FOOD_CATEGORIES = [
        ("Makanan Siap Santap", "Makanan Siap Santap"),
        ("Bahan Pokok", "Bahan Pokok"),
        ("Roti dan Kue", "Roti dan Kue"),
        ("Buah dan Sayur", "Buah dan Sayur"),
        ("Minuman", "Minuman"),
        ("Lainnya", "Lainnya"),
    ]

    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name="food_offers",
        verbose_name="Pemberi Makanan",
    )

    title = models.CharField("Nama Makanan", max_length=120)

    category = models.CharField(
        "Kategori",
        max_length=40,
        choices=FOOD_CATEGORIES,
        default="Makanan Siap Santap",
    )

    description = models.TextField("Deskripsi dan Kondisi Makanan")

    portions = models.PositiveSmallIntegerField(
        "Jumlah Porsi atau Paket",
        default = 1,
        validators = [MinValueValidator(1)],
    )

    remaining_portions = models.PositiveSmallIntegerField(
        "Sisa Porsi Tersedia",
        default = 1,
    )

    pickup_location = models.CharField("Alamat Titik Jemput", max_length=255)

    contact_info = models.CharField(
        "Kontak Penjemputan (WhatsApp/HP)",
        max_length=60,
        help_text="Hanya dapat dilihat oleh penerima yang mengajukan klaim.",
    )

    pickup_deadline = models.DateTimeField("Batas Waktu Penjemputan")

    latitude = models.DecimalField(
        "Latitude",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        "Longitude",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    image_url = models.URLField("URL Foto Makanan (opsional)", blank=True)

    status = models.CharField(
        "Status Ketersediaan",
        max_length=20,
        choices=STATUS_CHOICES,
        default="AVAILABLE",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition = models.Q(portions__gte=1),
                name="food_offer_portions_positive",
            ),
            models.CheckConstraint(
                condition = models.Q(remaining_portions__gte=0),
                name="food_offer_remaining_not_negative",
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.remaining_portions}/{self.portions} porsi)"

    @property
    def is_expired(self):
        return timezone.now() > self.pickup_deadline

class FoodClaim(models.Model):
    offer = models.ForeignKey(
        FoodOffer,
        on_delete = models.CASCADE,
        related_name = "claims",
        verbose_name = "Penawaran Makanan",
    )

    claimer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "food_claims",
        verbose_name = "Penerima Makanan",
    )

    portions_claimed = models.PositiveSmallIntegerField(
        "Jumlah Porsi Diklaim",
        default=1,
        validators=[MinValueValidator(1)],
    )

    notes = models.TextField("Catatan atau Waktu Perkiraan Ambil", blank=True)
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-claimed_at"]

    def __str__(self):
        return f"{self.claimer.username} mengklaim {self.portions_claimed} porsi {self.offer.title}"