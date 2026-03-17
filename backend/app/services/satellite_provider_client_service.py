from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import get_settings


class SatelliteProviderClientService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch_imagery(self, *, provider: str, region: str) -> dict[str, Any]:
        base_url = self.settings.satellite_provider_base_url
        if not base_url:
            return self._mock_provider_response(provider=provider, region=region)

        timestamp = datetime.now(UTC).isoformat()
        signature_payload = f"{provider}:{region}:{timestamp}".encode("utf-8")

        signature = ""
        if self.settings.satellite_provider_hmac_secret:
            signature = hmac.new(
                self.settings.satellite_provider_hmac_secret.encode("utf-8"),
                signature_payload,
                hashlib.sha256,
            ).hexdigest()

        headers = {
            "X-OnLooker-Provider": provider,
            "X-OnLooker-Timestamp": timestamp,
            "X-OnLooker-Signature": signature,
            "Content-Type": "application/json",
        }
        if self.settings.satellite_provider_api_key:
            headers["Authorization"] = f"Bearer {self.settings.satellite_provider_api_key}"

        async with httpx.AsyncClient(timeout=float(self.settings.satellite_provider_timeout_seconds)) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/providers/{provider}/imagery/sync",
                json={"region": region},
                headers=headers,
            )

        if response.status_code >= 400:
            raise ValueError(f"Satellite provider request failed: {response.status_code}")

        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Satellite provider response must be an object")
        return payload

    @staticmethod
    def _mock_provider_response(*, provider: str, region: str) -> dict[str, Any]:
        digest = hashlib.sha256(f"{provider}:{region}".encode("utf-8")).hexdigest()
        seed = int(digest[:6], 16)
        severity_index = round(min(1.0, ((seed % 800) / 1000) + 0.15), 3)
        return {
            "provider": provider,
            "region": region,
            "severity_index": severity_index,
            "frames": [
                {"frame_id": f"{provider}-a", "cloud_pct": (seed % 40) + 10, "quality": "high"},
                {"frame_id": f"{provider}-b", "cloud_pct": (seed % 35) + 15, "quality": "medium"},
            ],
        }
