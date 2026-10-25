from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class FoodWasteLog(models.Model):
    UNITS = [(value, value) for value in ("gram", "kg", "ml", "liter", "pcs", "porsi")]
    REASONS = [
        ("expired", "Kedaluwarsa"),
        ("spoiled", "Rusak atau basi"),
        ("excess", "Porsi berlebih"),
        ("other", "Lainnya"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    food_name = models.CharField("Nama makanan", max_length=120)
    quantity = models.DecimalField(
        "Jumlah terbuang", max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit = models.CharField("Satuan", max_length=12, choices=UNITS)
    wasted_on = models.DateField("Tanggal terbuang", default=timezone.localdate)
    reason = models.CharField("Alasan", max_length=20, choices=REASONS)
    estimated_loss = models.DecimalField(
        "Perkiraan kerugian (Rp)", max_digits=12, decimal_places=2,
        blank=True, null=True, validators=[MinValueValidator(Decimal("0"))],
        help_text="Total nilai makanan yang terbuang pada catatan ini, bukan harga per satuan. Kosongkan jika belum tahu.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-wasted_on", "-pk"]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="audit_quantity_positive"),
            models.CheckConstraint(
                condition=models.Q(estimated_loss__isnull=True) | models.Q(estimated_loss__gte=0),
                name="audit_loss_nonnegative",
            ),
        ]

    def clean(self):
        super().clean()
        if self.wasted_on and self.wasted_on > timezone.localdate():
            raise ValidationError({"wasted_on": "Tanggal terbuang tidak boleh di masa depan."})

    def __str__(self):
        return self.food_name
