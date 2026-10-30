from datetime import timedelta
from math import isqrt

from django.db.models import Sum
from django.utils import timezone


def progress_for(completions, today=None):
    today = today or timezone.localdate()
    completions = completions.filter(completed_on__lte=today)
    total = completions.aggregate(total=Sum("points"))["total"] or 0
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


def award_community_post(offer):
    from django.utils import timezone
    from .models import Completion
    local_day = timezone.localtime(offer.created_at).date()
    completion, created = Completion.objects.get_or_create(
        user=offer.donor, kind="share", completed_on=local_day,
        defaults={"food": offer.title[:120], "points": 15},
    )
    return created


def sync_community_posts(user, today=None):
    from datetime import datetime, time, timedelta
    from django.utils import timezone
    from community.models import FoodOffer
    from .models import Completion

    today = today or timezone.localdate()
    tz = timezone.get_current_timezone()

    start = timezone.make_aware(
        datetime.combine(today, time.min), tz
    )
    end = timezone.make_aware(
        datetime.combine(today + timedelta(days=1), time.min), tz
    )

    offer = FoodOffer.objects.filter(
        donor=user,
        created_at__gte=start,
        created_at__lt=end
    ).order_by("created_at", "pk").first()

    if offer is None:
        return False

    _, created = Completion.objects.get_or_create(
        user=user,
        kind="share",
        completed_on=today,
        defaults={
            "food": offer.title[:120],
            "points": 15,
        },
    )

    return created

