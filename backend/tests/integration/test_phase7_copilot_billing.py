import hashlib
import hmac
import json
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import TenantEntity


async def _register_engineer_headers(api_client: AsyncClient) -> dict[str, str]:
    response = await api_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"phase7-{uuid4().hex}@example.com",
            "password": "StrongPass123",
            "role": "engineer",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_copilot_endpoints_return_model_tag(api_client: AsyncClient) -> None:
    headers = await _register_engineer_headers(api_client)

    for endpoint, expected_model in (
        ("/api/v1/copilot/query", "nvidia/llama-3.1-nemotron-ultra-253b-v1"),
        ("/api/v1/copilot/doc", "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"),
        ("/api/v1/copilot/search", "nvidia/nv-embedqa-e5-v5"),
    ):
        response = await api_client.post(endpoint, json={"user_input": "Assess risk trend"}, headers=headers)
        assert response.status_code == 200
        payload = response.json()
        assert payload["model"] == expected_model
        assert isinstance(payload["response"], str)


@pytest.mark.asyncio
async def test_billing_webhook_updates_tenant_tier(api_client: AsyncClient, db_session: AsyncSession) -> None:
    tenant = TenantEntity(org_name=f"Phase7 Org {uuid4().hex[:8]}", subscription_tier="free")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)

    event = {
        "event_type": "BILLING.SUBSCRIPTION.UPDATED",
        "resource": {
            "custom_id": str(tenant.id),
            "subscription_tier": "professional",
        },
    }

    body = json.dumps(event, separators=(",", ":"), sort_keys=True)
    secret = "test-paypal-secret"
    signature = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()

    previous_secret = None
    from app.core.config import get_settings

    settings = get_settings()
    previous_secret = settings.paypal_webhook_secret
    settings.paypal_webhook_secret = secret

    try:
        response = await api_client.post(
            "/api/v1/billing/webhook",
            json=event,
            headers={"X-PayPal-Signature": signature},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["tenant"]["subscription_tier"] == "professional"
    finally:
        settings.paypal_webhook_secret = previous_secret


@pytest.mark.asyncio
async def test_billing_webhook_rejects_invalid_signature(api_client: AsyncClient) -> None:
    event = {
        "event_type": "BILLING.SUBSCRIPTION.UPDATED",
        "resource": {
            "custom_id": str(uuid4()),
            "subscription_tier": "professional",
        },
    }

    from app.core.config import get_settings

    settings = get_settings()
    previous_secret = settings.paypal_webhook_secret
    settings.paypal_webhook_secret = "required-secret"

    try:
        response = await api_client.post(
            "/api/v1/billing/webhook",
            json=event,
            headers={"X-PayPal-Signature": "bad-signature"},
        )
        assert response.status_code == 401
    finally:
        settings.paypal_webhook_secret = previous_secret
