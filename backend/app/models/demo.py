from __future__ import annotations

from uuid import UUID

from pydantic import EmailStr, Field, HttpUrl

from app.models.common import BaseDomainModel


class DemoRequestCreate(BaseDomainModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    company: str = Field(min_length=2, max_length=120)
    role: str = Field(min_length=2, max_length=120)
    use_case: str = Field(min_length=10, max_length=1200)
    preferred_auth_provider: str = Field(default="email", pattern="^(email|google|apple)$")


class DemoRequestResponse(BaseDomainModel):
    request_id: UUID
    message: str
    booking_url: HttpUrl
