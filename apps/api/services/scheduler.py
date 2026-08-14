from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import ContentVariant, Publication


def next_slots(db: Session, settings: Settings, count: int) -> list[datetime]:
    zone = ZoneInfo(settings.timezone)
    local_now = datetime.now(zone)
    windows: list[tuple[int, int]] = []
    for raw in settings.posting_windows.split(","):
        start, end = raw.strip().split("-")
        windows.append((int(start.split(":")[0]), int(end.split(":")[0])))
    slots: list[datetime] = []
    day = local_now.date()
    while len(slots) < count:
        day_start = datetime.combine(day, datetime.min.time(), zone)
        published = int(
            db.scalar(
                select(func.count(Publication.id)).where(
                    Publication.published_at >= day_start.astimezone(UTC),
                    Publication.published_at < (day_start + timedelta(days=1)).astimezone(UTC),
                )
            )
            or 0
        )
        capacity = max(settings.max_posts_per_day - published, 0)
        for start_hour, end_hour in windows:
            if capacity <= 0 or len(slots) >= count:
                break
            midpoint = day_start.replace(hour=start_hour) + timedelta(minutes=((end_hour - start_hour) * 60) // 2)
            if midpoint > local_now:
                slots.append(midpoint.astimezone(UTC))
                capacity -= 1
        day += timedelta(days=1)
    return slots


def schedule_approved(db: Session, settings: Settings) -> int:
    variants = db.scalars(
        select(ContentVariant).where(ContentVariant.status == "approved", ContentVariant.scheduled_for.is_(None))
    ).all()
    for variant, slot in zip(variants, next_slots(db, settings, len(variants)), strict=False):
        variant.scheduled_for = slot
        variant.status = "scheduled"
    db.commit()
    return len(variants)
