from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.models import AuditLogEntity
from app.database.session import AsyncSessionLocal

logger = get_logger("gifip.audit.batch")


@dataclass(frozen=True)
class AuditWriteRequest:
    event_type: str
    success: bool
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    user_email: str | None = None
    detail: str | None = None


class AuditBatchProcessor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.enabled = bool(self.settings.audit_async_enabled)
        self.queue: asyncio.Queue[AuditWriteRequest] = asyncio.Queue(maxsize=self.settings.audit_batch_queue_size)
        self._worker_task: asyncio.Task[None] | None = None
        self._stop_requested = False

        self._producer: Any | None = None

        self._enqueued_count = 0
        self._dropped_count = 0
        self._persisted_count = 0
        self._batch_flush_count = 0
        self._kafka_error_count = 0
        self._db_error_count = 0

    async def start(self) -> None:
        if not self.enabled:
            return
        if self._worker_task is not None and not self._worker_task.done():
            return
        self._stop_requested = False

        if self.settings.kafka_async_batching_enabled and self.settings.kafka_bootstrap_servers and self.settings.kafka_topic:
            try:
                from aiokafka import AIOKafkaProducer  # type: ignore[import-not-found]

                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self.settings.kafka_bootstrap_servers,
                    linger_ms=self.settings.kafka_linger_ms,
                    batch_size=self.settings.kafka_batch_size_bytes,
                    security_protocol=self.settings.kafka_security_protocol,
                )
                await self._producer.start()
            except Exception as exc:  # pragma: no cover
                self._kafka_error_count += 1
                self._producer = None
                logger.warning("Kafka producer was not started for audit batching", extra={"error": str(exc)})

        self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if not self.enabled:
            return
        self._stop_requested = True

        if self._worker_task is not None:
            await self._worker_task
            self._worker_task = None

        if self._producer is not None:
            try:
                await self._producer.stop()
            except Exception:
                self._kafka_error_count += 1
            self._producer = None

    def enqueue(self, request: AuditWriteRequest) -> bool:
        if not self.enabled:
            return False
        try:
            self.queue.put_nowait(request)
            self._enqueued_count += 1
            return True
        except asyncio.QueueFull:
            self._dropped_count += 1
            return False

    @property
    def is_running(self) -> bool:
        if not self.enabled:
            return False
        return self._worker_task is not None and not self._worker_task.done()

    def snapshot(self) -> dict[str, object]:
        return {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "enabled": self.enabled,
            "queue_depth": self.queue.qsize(),
            "enqueued": self._enqueued_count,
            "dropped": self._dropped_count,
            "persisted": self._persisted_count,
            "batch_flush_count": self._batch_flush_count,
            "kafka_error_count": self._kafka_error_count,
            "db_error_count": self._db_error_count,
            "kafka_batch_size_bytes": self.settings.kafka_batch_size_bytes,
            "kafka_linger_ms": self.settings.kafka_linger_ms,
        }

    async def _worker(self) -> None:
        linger_seconds = self.settings.kafka_linger_ms / 1000.0
        max_batch_bytes = self.settings.kafka_batch_size_bytes

        while True:
            if self._stop_requested and self.queue.empty():
                break

            try:
                first = await asyncio.wait_for(self.queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

            batch = [first]
            batch_bytes = self._estimate_item_size(first)
            deadline = monotonic() + linger_seconds

            while batch_bytes < max_batch_bytes and len(batch) < 2000:
                if monotonic() >= deadline:
                    break
                try:
                    item = self.queue.get_nowait()
                    batch.append(item)
                    batch_bytes += self._estimate_item_size(item)
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0)
                    continue

            await self._flush_batch(batch)
            for _ in batch:
                self.queue.task_done()

    async def _flush_batch(self, batch: list[AuditWriteRequest]) -> None:
        if not batch:
            return

        if self._producer is not None and self.settings.kafka_topic:
            try:
                payload = [self._as_dict(item) for item in batch]
                message = json.dumps(payload, separators=(",", ":")).encode("utf-8")
                await self._producer.send_and_wait(self.settings.kafka_topic, message)
            except Exception:
                self._kafka_error_count += 1

        entities = [
            AuditLogEntity(
                event_type=item.event_type,
                success=item.success,
                tenant_id=item.tenant_id,
                user_id=item.user_id,
                user_email=item.user_email,
                detail=item.detail,
            )
            for item in batch
        ]

        try:
            async with AsyncSessionLocal() as session:
                session.add_all(entities)
                await session.commit()
                self._persisted_count += len(entities)
                self._batch_flush_count += 1
        except Exception:
            self._db_error_count += 1

    @staticmethod
    def _estimate_item_size(item: AuditWriteRequest) -> int:
        return len(
            json.dumps(
                {
                    "event_type": item.event_type,
                    "success": item.success,
                    "tenant_id": str(item.tenant_id) if item.tenant_id else None,
                    "user_id": str(item.user_id) if item.user_id else None,
                    "user_email": item.user_email,
                    "detail": item.detail,
                },
                separators=(",", ":"),
            )
        )

    @staticmethod
    def _as_dict(item: AuditWriteRequest) -> dict[str, object]:
        return {
            "event_type": item.event_type,
            "success": item.success,
            "tenant_id": str(item.tenant_id) if item.tenant_id else None,
            "user_id": str(item.user_id) if item.user_id else None,
            "user_email": item.user_email,
            "detail": item.detail,
            "generated_at_utc": datetime.now(UTC).isoformat(),
        }


_processor = AuditBatchProcessor()


def get_audit_batch_processor() -> AuditBatchProcessor:
    return _processor
