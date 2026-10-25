from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from waste_audit.models import FoodWasteLog


class Command(BaseCommand):
    help = "Add explicitly requested synthetic food waste examples to a local demo account."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Data contoh ini hanya untuk lingkungan lokal dengan DEBUG aktif.")
        user = get_user_model().objects.filter(username=options["username"]).first()
        if user is None:
            raise CommandError("Buat akun demo terlebih dahulu dengan seed_demo.")
        # All numbers are synthetic, and no pantry stock is modified.
        examples = [
            ("Nasi putih", "1.5", "porsi", 0, "excess", "7500"),
            ("Susu kemasan", "250", "ml", 1, "expired", "6000"),
            ("Bayam", "100", "gram", 2, "spoiled", "3000"),
            ("Roti tawar", "2", "pcs", 4, "expired", None),
            ("Nasi putih", "0.5", "porsi", 6, "excess", "2500"),
            ("Tomat", "0.25", "kg", 10, "spoiled", "4000"),
            ("Kerupuk", "1", "pcs", 12, "other", "0"),
            ("Pisang", "2", "pcs", 18, "spoiled", "5000"),
        ]
        created_count = 0
        for name, qty, unit, days, reason, loss in examples:
            _, created = FoodWasteLog.objects.get_or_create(
                owner=user, food_name=name, wasted_on=timezone.localdate() - timedelta(days=days),
                reason=reason, unit=unit,
                defaults={"quantity": Decimal(qty), "estimated_loss": Decimal(loss) if loss is not None else None},
            )
            created_count += created
        self.stdout.write(self.style.SUCCESS(f"{created_count} catatan contoh sintetis ditambahkan untuk {user.username}."))
