from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.models.intelligence import IoTConnectorEvent


@dataclass
class ConnectorPullRequest:
    connector_type: str
    tenant_id: str
    max_events: int
    topic: str | None = None


class ConnectorAdapterService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def pull_events(self, request: ConnectorPullRequest) -> list[IoTConnectorEvent]:
        connector = request.connector_type.strip().lower()
        if connector == "mqtt":
            return await self._pull_mqtt(request)
        if connector == "kafka":
            return await self._pull_kafka(request)
        if connector in {"device_gateway", "gateway", "http_gateway"}:
            return await self._pull_device_gateway(request)
        raise ValueError("Unsupported connector_type")

    async def _pull_mqtt(self, request: ConnectorPullRequest) -> list[IoTConnectorEvent]:
        try:
            import paho.mqtt.client as mqtt  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover
            raise ValueError("paho-mqtt dependency not available") from exc

        broker_url = self.settings.mqtt_broker_url
        topic = request.topic or self.settings.mqtt_topic
        if not broker_url or not topic:
            raise ValueError("MQTT connector is not configured")

        parsed = urlparse(broker_url)
        host = parsed.hostname
        port = parsed.port or (8883 if parsed.scheme in {"mqtts", "ssl"} else 1883)
        if not host:
            raise ValueError("MQTT_BROKER_URL is invalid")

        events: list[IoTConnectorEvent] = []
        done = asyncio.Event()

        def on_connect(client, _userdata, _flags, rc, _properties=None):  # type: ignore[no-untyped-def]
            if rc != 0:
                done.set()
                return
            client.subscribe(topic)

        def on_message(_client, _userdata, msg):  # type: ignore[no-untyped-def]
            try:
                payload = json.loads(msg.payload.decode("utf-8"))
            except Exception:
                payload = {"raw": msg.payload.decode("utf-8", errors="ignore")}

            sensor_id = str(payload.get("sensor_id") or f"mqtt-{msg.topic}")
            if isinstance(payload, dict):
                payload = dict(payload)
                payload.pop("sensor_id", None)
            else:
                payload = {"value": payload}

            events.append(IoTConnectorEvent(sensor_id=sensor_id, payload=payload))
            if len(events) >= request.max_events:
                done.set()

        client = mqtt.Client(protocol=mqtt.MQTTv5)
        if self.settings.mqtt_username:
            client.username_pw_set(self.settings.mqtt_username, self.settings.mqtt_password)
        if self.settings.mqtt_tls_enabled:
            client.tls_set()

        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(host, port, keepalive=30)
        client.loop_start()

        try:
            await asyncio.wait_for(done.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            pass
        finally:
            client.loop_stop()
            client.disconnect()

        return events

    async def _pull_kafka(self, request: ConnectorPullRequest) -> list[IoTConnectorEvent]:
        try:
            from aiokafka import AIOKafkaConsumer  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover
            raise ValueError("aiokafka dependency not available") from exc

        servers = self.settings.kafka_bootstrap_servers
        topic = request.topic or self.settings.kafka_topic
        if not servers or not topic:
            raise ValueError("Kafka connector is not configured")

        kwargs: dict[str, Any] = {
            "bootstrap_servers": servers,
            "group_id": self.settings.kafka_group_id,
            "security_protocol": self.settings.kafka_security_protocol,
            "auto_offset_reset": "latest",
            "enable_auto_commit": False,
        }
        if self.settings.kafka_sasl_mechanism:
            kwargs["sasl_mechanism"] = self.settings.kafka_sasl_mechanism
        if self.settings.kafka_sasl_username:
            kwargs["sasl_plain_username"] = self.settings.kafka_sasl_username
        if self.settings.kafka_sasl_password:
            kwargs["sasl_plain_password"] = self.settings.kafka_sasl_password

        consumer = AIOKafkaConsumer(topic, **kwargs)
        await consumer.start()
        events: list[IoTConnectorEvent] = []
        try:
            batches = await consumer.getmany(timeout_ms=1500, max_records=request.max_events)
            for records in batches.values():
                for record in records:
                    try:
                        payload = json.loads(record.value.decode("utf-8"))
                    except Exception:
                        payload = {"raw": record.value.decode("utf-8", errors="ignore")}

                    sensor_id = str(payload.get("sensor_id") or f"kafka-{record.partition}-{record.offset}")
                    if isinstance(payload, dict):
                        payload = dict(payload)
                        payload.pop("sensor_id", None)
                    else:
                        payload = {"value": payload}

                    events.append(IoTConnectorEvent(sensor_id=sensor_id, payload=payload))
                    if len(events) >= request.max_events:
                        return events
            return events
        finally:
            await consumer.stop()

    async def _pull_device_gateway(self, request: ConnectorPullRequest) -> list[IoTConnectorEvent]:
        gateway_url = self.settings.device_gateway_url
        if not gateway_url:
            raise ValueError("Device gateway connector is not configured")

        timestamp = datetime.now(UTC).isoformat()
        signature_payload = f"{request.tenant_id}:{request.max_events}:{timestamp}".encode("utf-8")

        signature = ""
        if self.settings.device_gateway_hmac_secret:
            signature = hmac.new(
                self.settings.device_gateway_hmac_secret.encode("utf-8"),
                signature_payload,
                hashlib.sha256,
            ).hexdigest()

        headers = {
            "X-OnLooker-Timestamp": timestamp,
            "X-OnLooker-Signature": signature,
        }
        if self.settings.device_gateway_api_key:
            headers["Authorization"] = f"Bearer {self.settings.device_gateway_api_key}"

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                f"{gateway_url.rstrip('/')}/events",
                params={"tenant_id": request.tenant_id, "limit": request.max_events},
                headers=headers,
            )
        if response.status_code >= 400:
            raise ValueError(f"Device gateway request failed: {response.status_code}")

        data = response.json()
        if not isinstance(data, list):
            raise ValueError("Device gateway response must be a list")

        events: list[IoTConnectorEvent] = []
        for row in data[: request.max_events]:
            if not isinstance(row, dict):
                continue
            sensor_id = str(row.get("sensor_id") or "gateway-sensor")
            payload = row.get("payload")
            if not isinstance(payload, dict):
                payload = {"value": payload}
            events.append(IoTConnectorEvent(sensor_id=sensor_id, payload=payload))
        return events
