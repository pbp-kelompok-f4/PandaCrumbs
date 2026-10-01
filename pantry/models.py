from datetime import timedelta
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class PantryItem(models.Model):
    CATEGORIES = [(x, x) for x in ("Buah Segar", "Sayuran", "Susu", "Yogurt", "Protein", "Bahan Pokok", "Lainnya")]
    LOCATIONS = [(x, x) for x in ("Kulkas", "Freezer", "Rak Dapur")]
    UNITS = [(x, x) for x in ("pcs", "kg", "gram", "liter", "pack", "botol", "kotak")]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField("Nama bahan makanan", max_length=120)
    category = models.CharField("Jenis makanan", max_length=30, choices=CATEGORIES)
    quantity = models.PositiveIntegerField("Jumlah stok", default=1, validators=[MinValueValidator(1)])
    unit = models.CharField("Satuan", max_length=12, choices=UNITS, default="pcs")
    location = models.CharField("Lokasi penyimpanan", max_length=30, choices=LOCATIONS)
    expires_on = models.DateField("Tanggal kedaluwarsa")
    stored_on = models.DateField("Tanggal masuk penyimpanan", default=timezone.localdate)
    image_url = models.URLField("URL foto (opsional)", blank=True)
    barcode = models.CharField(max_length=32, blank=True)
    is_demo = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["expires_on", "pk"]
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gte=1), name="pantry_quantity_positive")]

    @property
    def status(self):
        today = timezone.localdate()
        if self.expires_on < today:
            return "expired"
        return "soon" if self.expires_on <= today + timedelta(days=3) else "safe"

    @property
    def status_label(self):
        return {"expired": "Kadaluarsa", "soon": "Hampir Kadaluarsa", "safe": "Aman"}[self.status]

    def __str__(self):
        return self.name
