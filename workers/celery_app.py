from celery import Celery

from apps.api.core.config import get_settings

settings = get_settings()
celery_app = Celery("dealforge", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "product-sync-every-six-hours": {"task": "workers.tasks.product_sync", "schedule": 21600.0},
        "publish-due-content-every-minute": {"task": "workers.tasks.publish_due", "schedule": 60.0},
        "revalidate-active-deals-hourly": {
            "task": "workers.tasks.revalidate_deals",
            "schedule": 3600.0,
        },
        "daily-optimization": {"task": "workers.tasks.daily_optimization", "schedule": 86400.0},
    },
)
celery_app.autodiscover_tasks(["workers"])
