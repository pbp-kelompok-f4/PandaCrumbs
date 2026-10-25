from django.conf import settings
from django.db import models


class UIIdentity(models.Model):
    """Verified UI identity; never matched to a local username or email."""

    subject = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
