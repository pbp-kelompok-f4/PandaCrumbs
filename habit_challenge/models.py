from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class ChallengePlan(models.Model):
    CATEGORIES = [
        ("", "Semua kategori"), ("en:dairies", "Produk susu"),
        ("en:breads", "Roti"), ("en:vegetables", "Sayuran"),
        ("en:fruits", "Buah"), ("en:cereals", "Biji-bijian dan sereal"),
        ("en:snacks", "Camilan"), ("en:beverages", "Minuman"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField("Nama rencana", max_length=120)
    kind = models.CharField("Jenis tantangan", max_length=12, choices=[
        ("pantry", "Pakai stok tersisa"), ("leftovers", "Olah makanan sisa"),
        ("share", "Berbagi makanan"),
    ])
    target_days = models.PositiveSmallIntegerField("Target hari aktif", default=7, validators=[MinValueValidator(1)])
    category = models.CharField("Kategori makanan sasaran", max_length=30, choices=CATEGORIES, blank=True)
    food = models.CharField("Bahan atau produk sasaran", max_length=120, blank=True)
    starts_on = models.DateField("Tanggal mulai", default=timezone.localdate)
    ends_on = models.DateField("Tanggal selesai")

    class Meta:
        ordering = ["-starts_on", "-pk"]
        constraints = [
            models.CheckConstraint(condition=models.Q(ends_on__gte=models.F("starts_on")), name="habit_plan_valid_period"),
            models.CheckConstraint(condition=models.Q(target_days__gte=1), name="habit_plan_positive_target"),
        ]

    def __str__(self):
        return self.title


class Completion(models.Model):
    class Kind(models.TextChoices):
        PANTRY = "pantry", "Pakai stok tersisa"
        LEFTOVERS = "leftovers", "Olah makanan sisa"
        SHARE = "share", "Berbagi makanan"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    plan = models.ForeignKey(ChallengePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name="completions")
    food = models.CharField("Makanan atau bahan yang digunakan", max_length=120)
    completed_on = models.DateField(default=timezone.localdate)
    points = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_on", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "kind", "completed_on"],
                name="habit_one_completion_per_day",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(kind__in=["pantry", "leftovers"], points=10)
                    | models.Q(kind="share", points=15)
                ),
                name="habit_valid_reward",
            ),
        ]

    def __str__(self):
        return f"{self.user} · {self.get_kind_display()} · {self.completed_on}"
