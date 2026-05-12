from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic
from typing import Any, Awaitable, Callable, Generic, TypeVar

from app.core.config import get_settings

try:
    from redis.asyncio import Redis  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - redis is optional at runtime.
    Redis = None  # type: ignore[assignment]


T = TypeVar("T")


@dataclass
class _LocalCacheRecord:
    value_json: str
    stored_at_epoch: float
    expires_at_epoch: float


class ReadThroughCache(Generic[T]):
    def __init__(self, *, namespace: str) -> None:
        self.namespace = namespace
        self.settings = get_settings()
        self._local_cache: dict[str, _LocalCacheRecord] = {}
        self._refresh_tasks: dict[str, asyncio.Task[None]] = {}

        self._hit_count = 0
        self._miss_count = 0
        self._refresh_count = 0
        self._backend_error_count = 0

        self._redis: Any | None = None
        if self.settings.redis_url and Redis is not None:
            self._redis = Redis.from_url(self.settings.redis_url, decode_responses=True)

    def snapshot(self) -> dict[str, object]:
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total) if total else 0.0
        return {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "namespace": self.namespace,
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": hit_rate,
            "target_hit_rate": self.settings.redis_target_hit_rate,
            "refreshes": self._refresh_count,
            "backend_errors": self._backend_error_count,
            "backend": "redis" if self._redis is not None else "in_memory",
            "local_entries": len(self._local_cache),
        }

    def clear_local(self) -> None:
        self._local_cache.clear()

    async def get_or_load(
        self,
        *,
        cache_key: str,
        loader: Callable[[], Awaitable[T]],
        encode: Callable[[T], str],
        decode: Callable[[str], T],
        hard_ttl_seconds: int | None = None,
        refresh_ttl_ms: int | None = None,
    ) -> T:
        hard_ttl = hard_ttl_seconds or self.settings.redis_readthrough_hard_ttl_seconds
        refresh_ttl = refresh_ttl_ms or self.settings.redis_readthrough_refresh_ttl_ms

        namespaced_key = f"{self.namespace}:{cache_key}"
        now_value = monotonic()

        encoded_payload, age_ms = await self._read(namespaced_key=namespaced_key, now_epoch=now_value)
        if encoded_payload is not None:
            self._hit_count += 1
            if age_ms >= refresh_ttl:
                self._maybe_schedule_refresh(
                    namespaced_key=namespaced_key,
                    loader=loader,
                    encode=encode,
                    hard_ttl_seconds=hard_ttl,
                )
            return decode(encoded_payload)

        self._miss_count += 1
        value = await loader()
        await self._write(
            namespaced_key=namespaced_key,
            payload_json=encode(value),
            hard_ttl_seconds=hard_ttl,
            now_epoch=now_value,
        )
        return value

    def _maybe_schedule_refresh(
        self,
        *,
        namespaced_key: str,
        loader: Callable[[], Awaitable[T]],
        encode: Callable[[T], str],
        hard_ttl_seconds: int,
    ) -> None:
        existing = self._refresh_tasks.get(namespaced_key)
        if existing is not None and not existing.done():
            return

        task = asyncio.create_task(
            self._refresh(
                namespaced_key=namespaced_key,
                loader=loader,
                encode=encode,
                hard_ttl_seconds=hard_ttl_seconds,
            )
        )
        self._refresh_tasks[namespaced_key] = task

    async def _refresh(
        self,
        *,
        namespaced_key: str,
        loader: Callable[[], Awaitable[T]],
        encode: Callable[[T], str],
        hard_ttl_seconds: int,
    ) -> None:
        try:
            value = await loader()
            await self._write(
                namespaced_key=namespaced_key,
                payload_json=encode(value),
                hard_ttl_seconds=hard_ttl_seconds,
                now_epoch=monotonic(),
            )
            self._refresh_count += 1
        except Exception:
            self._backend_error_count += 1

    async def _read(self, *, namespaced_key: str, now_epoch: float) -> tuple[str | None, int]:
        if self._redis is not None:
            try:
                raw = await self._redis.get(namespaced_key)
                if raw:
                    record = json.loads(raw)
                    payload_json = str(record.get("value_json", ""))
                    stored_at_epoch = float(record.get("stored_at_epoch", now_epoch))
                    age_ms = int(max((now_epoch - stored_at_epoch) * 1000, 0))
                    return payload_json, age_ms
            except Exception:
                self._backend_error_count += 1

        local = self._local_cache.get(namespaced_key)
        if local is None:
            return None, 0
        if local.expires_at_epoch <= now_epoch:
            self._local_cache.pop(namespaced_key, None)
            return None, 0

        age_ms = int(max((now_epoch - local.stored_at_epoch) * 1000, 0))
        return local.value_json, age_ms

    async def _write(
        self,
        *,
        namespaced_key: str,
        payload_json: str,
        hard_ttl_seconds: int,
        now_epoch: float,
    ) -> None:
        envelope = json.dumps(
            {
                "value_json": payload_json,
                "stored_at_epoch": now_epoch,
            },
            separators=(",", ":"),
        )

        if self._redis is not None:
            try:
                await self._redis.set(namespaced_key, envelope, ex=hard_ttl_seconds)
                return
            except Exception:
                self._backend_error_count += 1

        self._local_cache[namespaced_key] = _LocalCacheRecord(
            value_json=payload_json,
            stored_at_epoch=now_epoch,
            expires_at_epoch=now_epoch + hard_ttl_seconds,
        )
