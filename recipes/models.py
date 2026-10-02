from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Recipe(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField("Judul resep", max_length=120)
    ingredients = models.TextField("Bahan dan takaran", help_text="Satu bahan beserta takaran per baris.")
    steps = models.TextField("Langkah memasak", help_text="Satu langkah per baris.")
    portions = models.PositiveSmallIntegerField("Porsi", default=2, validators=[MinValueValidator(1)])
    minutes = models.PositiveSmallIntegerField("Waktu memasak (menit)", default=15, validators=[MinValueValidator(1)])
    image_url = models.URLField("URL foto (opsional)", blank=True)
    demo_image = models.CharField(max_length=100, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(condition=models.Q(portions__gte=1), name="recipe_portions_positive"),
            models.CheckConstraint(condition=models.Q(minutes__gte=1), name="recipe_minutes_positive"),
        ]

    def __str__(self):
        return self.title


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "recipe"], name="unique_user_recipe_bookmark")]
