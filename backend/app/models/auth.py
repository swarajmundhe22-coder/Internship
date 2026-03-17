from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import EmailStr, Field

from app.models.common import BaseDomainModel


class UserRole(str, Enum):
    admin = "admin"
    engineer = "engineer"
    viewer = "viewer"


class UserRegisterRequest(BaseDomainModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.engineer


class UserLoginRequest(BaseDomainModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginOtpRequest(BaseDomainModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginOtpVerifyRequest(BaseDomainModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class RegistrationOtpRequest(BaseDomainModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.engineer


class RegistrationOtpVerifyRequest(BaseDomainModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class RegistrationOtpChallengeResponse(BaseDomainModel):
    message: str
    email: EmailStr
    expires_in_seconds: int
    dev_otp: str | None = None


class RefreshTokenRequest(BaseDomainModel):
    refresh_token: str


class LogoutRequest(BaseDomainModel):
    refresh_token: str


class AuthTokenResponse(BaseDomainModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthPrincipal(BaseDomainModel):
    user_id: UUID
    email: str
    role: UserRole
    session_id: UUID
