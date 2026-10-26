from datetime import timedelta
from math import isqrt

from django.db.models import Sum
from django.utils import timezone


def progress_for(completions, today=None):
    today = today or timezone.localdate()
    completions = completions.filter(completed_on__lte=today)
    total = completions.aggregate(total=Sum("points"))["total"] or 0
    # Level 1 needs 50 points, level 2 needs 100 more, and so on.
    level = (1 + isqrt(1 + 4 * (total // 25))) // 2
    floor = 25 * level * (level - 1)
    earned = total - floor
    target = 50 * level
    days = set(completions.values_list("completed_on", flat=True).distinct())
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return {
        "total": total, "level": level, "earned": earned, "target": target,
        "percent": earned * 100 // target, "streak": streak,
    }
