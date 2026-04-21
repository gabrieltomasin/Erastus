"""Publish events from Celery workers to Redis for WebSocket delivery."""

import json
import redis
from app.config import settings

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL)
    return _redis_client


def publish_event(session_id: int, event_type: str, data: dict | None = None):
    """Publish an event to the session's Redis channel."""
    r = _get_redis()
    payload = {"type": event_type, **(data or {})}
    r.publish(f"rpg:session:{session_id}", json.dumps(payload))


def publish_status(session_id: int, status: str):
    publish_event(session_id, "status_change", {"status": status})


def publish_log(session_id: int, step: str, message: str, level: str = "info"):
    publish_event(session_id, "log", {"step": step, "message": message, "level": level})


def publish_progress(session_id: int, step: str, current: int, total: int, detail: str = ""):
    percent = int((current / total) * 100) if total > 0 else 0
    publish_event(session_id, "progress", {
        "step": step,
        "current": current,
        "total": total,
        "percent": percent,
        "detail": detail,
    })
