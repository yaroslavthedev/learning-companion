"""Dashboard aggregations: one ORM query each, scoped to the given user."""

import datetime

from django.db.models import Count, Sum
from django.db.models.functions import TruncWeek
from django.utils import timezone

from accounts.models import User
from learning.models import Goal, LearningSession

WEEKS = 8


def _with_percent(rows: list[dict], key: str) -> list[dict]:
    """Add "percent" (0..100, of the largest `key` value) to every row."""
    largest = max((row[key] for row in rows), default=0)
    for row in rows:
        row["percent"] = round(row[key] * 100 / largest) if largest else 0
    return rows


def goals_per_status(user: User) -> list[dict]:
    """[{"label", "count", "percent"}, ...] for every Goal.Status, zeros included."""
    counts = dict(
        Goal.objects.for_user(user)
        .values("status")
        .annotate(count=Count("pk"))
        .values_list("status", "count")
    )
    rows = [
        {"label": label, "count": counts.get(status, 0)}
        for status, label in Goal.Status.choices
    ]
    return _with_percent(rows, "count")


def hours_per_tag(user: User) -> list[dict]:
    """[{"name", "hours", "percent"}, ...], most hours first; untagged sessions skipped.

    A session with several tags counts for each of them."""
    totals = (
        LearningSession.objects.for_user(user)
        .filter(tags__isnull=False)
        .values("tags__name")
        .annotate(minutes=Sum("duration_minutes"))
        .order_by("-minutes", "tags__name")
    )
    rows = [
        {"name": total["tags__name"], "hours": total["minutes"] / 60}
        for total in totals
    ]
    return _with_percent(rows, "hours")


def hours_per_week(user: User, today: datetime.date | None = None) -> list[dict]:
    """8 rows {"week_start", "label", "hours", "percent"}: the current ISO week and
    the 7 before it, oldest first; weeks without sessions have 0 hours."""
    today = today or timezone.localdate()
    current_monday = today - datetime.timedelta(days=today.weekday())
    week_starts = [
        current_monday - datetime.timedelta(weeks=weeks_back)
        for weeks_back in range(WEEKS - 1, -1, -1)
    ]
    minutes = dict(
        LearningSession.objects.for_user(user)
        .filter(
            date__gte=week_starts[0],
            date__lt=current_monday + datetime.timedelta(weeks=1),
        )
        .annotate(week=TruncWeek("date"))
        .values("week")
        .annotate(minutes=Sum("duration_minutes"))
        .values_list("week", "minutes")
    )
    rows = [
        {
            "week_start": week_start,
            "label": "{}-W{:02d}".format(*week_start.isocalendar()[:2]),
            "hours": minutes.get(week_start, 0) / 60,
        }
        for week_start in week_starts
    ]
    return _with_percent(rows, "hours")
