from __future__ import annotations

from threading import Lock
from time import monotonic
from uuid import UUID

from app.core.config import get_settings


_ACTIVE_SESSION_CACHE: dict[UUID, float] = {}
_CACHE_LOCK = Lock()


def _evict_expired_locked(now_monotonic: float) -> None:
    expired_keys = [session_id for session_id, expires_at in _ACTIVE_SESSION_CACHE.items() if expires_at <= now_monotonic]
    for session_id in expired_keys:
        _ACTIVE_SESSION_CACHE.pop(session_id, None)


def _trim_to_capacity_locked(max_entries: int) -> None:
    overflow = len(_ACTIVE_SESSION_CACHE) - max_entries
    if overflow <= 0:
        return

    for session_id, _ in sorted(_ACTIVE_SESSION_CACHE.items(), key=lambda item: item[1])[:overflow]:
        _ACTIVE_SESSION_CACHE.pop(session_id, None)


def remember_active_session(session_id: UUID) -> None:
    settings = get_settings()
    ttl_seconds = settings.auth_session_active_cache_ttl_seconds
    if ttl_seconds <= 0:
        return

    max_entries = settings.auth_session_active_cache_max_entries
    now_monotonic = monotonic()

    with _CACHE_LOCK:
        if len(_ACTIVE_SESSION_CACHE) >= max_entries:
            _evict_expired_locked(now_monotonic)
            _trim_to_capacity_locked(max_entries=max_entries)
        _ACTIVE_SESSION_CACHE[session_id] = now_monotonic + ttl_seconds


def is_session_marked_active(session_id: UUID) -> bool:
    settings = get_settings()
    if settings.auth_session_active_cache_ttl_seconds <= 0:
        return False

    now_monotonic = monotonic()
    with _CACHE_LOCK:
        expires_at = _ACTIVE_SESSION_CACHE.get(session_id)
        if expires_at is None:
            return False
        if expires_at <= now_monotonic:
            _ACTIVE_SESSION_CACHE.pop(session_id, None)
            return False
        return True


def mark_session_inactive(session_id: UUID) -> None:
    with _CACHE_LOCK:
        _ACTIVE_SESSION_CACHE.pop(session_id, None)
