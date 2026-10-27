from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Sum
from django.test import SimpleTestCase, TestCase, override_settings

from .models import FoodWasteLog
from .templatetags.audit_format import amount, rupiah


@override_settings(DEBUG=True)
class AuditDemoCommandTests(TestCase):
    def setUp(self):
        self.demo = get_user_model().objects.create_user(username="seed-audit-demo")
        self.other = get_user_model().objects.create_user(username="seed-audit-other")
        self.today = date(2026, 10, 15)
        self.other_entry = FoodWasteLog.objects.create(
            owner=self.other, food_name="Catatan akun lain",
            quantity=Decimal("1"), unit="pcs", wasted_on=self.today,
            reason="other", estimated_loss=Decimal("9000"),
        )
        self.clock = patch(
            "waste_audit.management.commands.seed_audit_demo.timezone.localdate",
            return_value=self.today,
        )
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def seed(self, username=None):
        call_command(
            "seed_audit_demo",
            username=username or self.demo.username,
            stdout=StringIO(),
        )

    def test_seed_creates_valid_examples_for_requested_owner_only(self):
        self.seed()
        entries = FoodWasteLog.objects.filter(owner=self.demo)
        self.assertEqual(entries.count(), 8)
        self.assertEqual(
            entries.aggregate(total=Sum("estimated_loss"))["total"],
            Decimal("28000"),
        )
        self.assertEqual(entries.filter(estimated_loss__isnull=True).count(), 1)
        self.assertEqual(entries.filter(estimated_loss=0).count(), 1)
        self.assertSetEqual(
            set(entries.values_list("reason", flat=True)),
            {"expired", "spoiled", "excess", "other"},
        )
        self.assertSetEqual(
            set(entries.values_list("wasted_on", flat=True)),
            {self.today - timedelta(days=d) for d in [0, 1, 2, 4, 6, 10, 12, 18]},
        )
        for entry in entries:
            entry.full_clean()
        self.other_entry.refresh_from_db()
        self.assertEqual(self.other_entry.food_name, "Catatan akun lain")
        self.assertEqual(self.other_entry.estimated_loss, Decimal("9000"))
        self.assertEqual(FoodWasteLog.objects.filter(owner=self.other).count(), 1)

    def test_repeated_seed_preserves_edits_and_does_not_duplicate_records(self):
        self.seed()
        entry = FoodWasteLog.objects.get(owner=self.demo, food_name="Bayam")
        entry.quantity = Decimal("200")
        entry.estimated_loss = Decimal("8000")
        entry.save()
        self.seed()
        entry.refresh_from_db()
        self.assertEqual(FoodWasteLog.objects.filter(owner=self.demo).count(), 8)
        self.assertEqual(entry.quantity, Decimal("200"))
        self.assertEqual(entry.estimated_loss, Decimal("8000"))

    def test_missing_account_is_rejected_without_creating_records(self):
        before = FoodWasteLog.objects.count()
        with self.assertRaises(CommandError):
            self.seed("account-that-does-not-exist")
        self.assertEqual(FoodWasteLog.objects.count(), before)
        self.assertFalse(get_user_model().objects.filter(
            username="account-that-does-not-exist"
        ).exists())

    @override_settings(DEBUG=False)
    def test_production_is_rejected_without_creating_records(self):
        before = FoodWasteLog.objects.count()
        with self.assertRaises(CommandError):
            self.seed()
        self.assertEqual(FoodWasteLog.objects.count(), before)


class AuditFormattingTests(SimpleTestCase):
    def test_amount_formats_missing_zero_integer_and_fraction(self):
        for value, expected in [
            (None, ""), (Decimal("0.00"), "0"),
            (Decimal("100"), "100"), (Decimal("1.50"), "1,5"),
        ]:
            with self.subTest(value=value):
                self.assertEqual(amount(value), expected)

    def test_rupiah_distinguishes_unknown_from_zero_and_formats_decimals(self):
        for value, expected in [
            (None, "Belum diisi"), (Decimal("0"), "Rp0"),
            (Decimal("12500"), "Rp12.500"),
            (Decimal("12500.75"), "Rp12.500,75"),
        ]:
            with self.subTest(value=value):
                self.assertEqual(rupiah(value), expected)
