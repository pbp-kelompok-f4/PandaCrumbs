"""Optional real-browser checks: manage.py test waste_audit.browser_tests."""
import os
from pathlib import Path
import shutil
import subprocess

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings

from .models import FoodWasteLog


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class AuditBrowserTests(StaticLiveServerTestCase):
    def test_search_crud_and_mobile_in_real_browser(self):
        node = os.environ.get("AUDIT_NODE_BIN") or shutil.which("node")
        self.assertTrue(node, "Install Node.js or set AUDIT_NODE_BIN to its executable.")
        owner = get_user_model().objects.create_user(username="browser-owner")
        other = get_user_model().objects.create_user(username="browser-other")
        for user, name in ((owner, "Ayam goreng"), (owner, "Bayam"), (other, "Ayam rahasia")):
            FoodWasteLog.objects.create(owner=user, food_name=name, quantity=1,
                                        unit="pcs", reason="spoiled", estimated_loss=5000)
        self.client.force_login(owner)
        env = os.environ.copy()
        env["AUDIT_BROWSER_SESSION"] = self.client.cookies["sessionid"].value
        env["AUDIT_BROWSER_URL"] = self.live_server_url
        result = subprocess.run(
            [node, str(Path(__file__).with_name("browser_checks.cjs"))],
            env=env, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(FoodWasteLog.objects.filter(owner=owner).count(), 2)
        self.assertEqual(FoodWasteLog.objects.filter(owner=other).count(), 1)
        print(result.stdout.strip())
