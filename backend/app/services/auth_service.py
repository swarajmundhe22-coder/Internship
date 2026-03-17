from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from hashlib import sha256
import logging
import secrets
import smtplib
from dataclasses import dataclass
from uuid import UUID

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

from app.core.config import get_settings
from app.models.auth import AuthPrincipal, AuthTokenResponse, RegistrationOtpChallengeResponse, UserRole
from app.repositories.refresh_session_repository import RefreshSessionRepository
from app.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
logger = logging.getLogger(__name__)


@dataclass
class PendingRegistration:
    email: str
    hashed_password: str
    role: UserRole
    otp_hash: str
    otp_salt: str
    expires_at: datetime
    attempts: int = 0


@dataclass
class PendingLogin:
    user_id: UUID
    email: str
    role: UserRole
    otp_hash: str
    otp_salt: str
    expires_at: datetime
    attempts: int = 0


class AuthService:
    _pending_registrations: dict[str, PendingRegistration] = {}
    _pending_logins: dict[str, PendingLogin] = {}
    _pending_lock = asyncio.Lock()

    def __init__(self, repository: UserRepository, refresh_repository: RefreshSessionRepository | None = None) -> None:
        self.repository = repository
        self.refresh_repository = refresh_repository
        self.settings = get_settings()

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return pwd_context.verify(password, hashed_password)

    async def register(self, email: str, password: str, role: UserRole = UserRole.engineer) -> AuthTokenResponse:
        existing = await self.repository.get_by_email(email)
        if existing is not None:
            raise ValueError("A user with this email already exists")

        user = await self.repository.create(email=email, hashed_password=self.hash_password(password), role=role.value)
        return await self.issue_tokens(user_id=user.id, email=user.email, role=UserRole(user.role))

    async def login(self, email: str, password: str) -> AuthTokenResponse:
        user = await self.repository.get_by_email(email)
        if user is None or not self.verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        return await self.issue_tokens(user_id=user.id, email=user.email, role=UserRole(user.role))

    async def request_registration_otp(
        self,
        email: str,
        password: str,
        role: UserRole = UserRole.engineer,
    ) -> RegistrationOtpChallengeResponse:
        normalized_email = email.strip().lower()
        existing = await self.repository.get_by_email(normalized_email)
        if existing is not None:
            raise ValueError("A user with this email already exists")

        otp_code = f"{secrets.randbelow(1_000_000):06d}"
        otp_salt = secrets.token_urlsafe(16)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.settings.registration_otp_expire_minutes)
        pending = PendingRegistration(
            email=normalized_email,
            hashed_password=self.hash_password(password),
            role=role,
            otp_hash=self._hash_otp(otp_code, otp_salt),
            otp_salt=otp_salt,
            expires_at=expires_at,
        )

        async with self._pending_lock:
            self._pending_registrations[normalized_email] = pending

        delivered = await asyncio.to_thread(self._dispatch_otp_email, normalized_email, otp_code, "Registration")
        if not delivered and self.settings.environment.lower() == "production":
            raise ValueError("OTP delivery is not configured")

        dev_otp = None
        if not delivered and self.settings.environment.lower() != "production":
            logger.warning("OTP email transport unavailable for %s; using development fallback", normalized_email)
            dev_otp = otp_code

        return RegistrationOtpChallengeResponse(
            message="Verification code sent to your email",
            email=normalized_email,
            expires_in_seconds=self.settings.registration_otp_expire_minutes * 60,
            dev_otp=dev_otp,
        )

    async def verify_registration_otp(self, email: str, otp: str) -> AuthTokenResponse:
        normalized_email = email.strip().lower()
        existing = await self.repository.get_by_email(normalized_email)
        if existing is not None:
            raise ValueError("A user with this email already exists")

        async with self._pending_lock:
            pending = self._pending_registrations.get(normalized_email)
            if pending is None:
                raise ValueError("No active OTP challenge found. Request a new code")

            now = datetime.now(timezone.utc)
            if pending.expires_at <= now:
                del self._pending_registrations[normalized_email]
                raise ValueError("OTP has expired. Request a new code")

            if pending.attempts >= self.settings.registration_otp_max_attempts:
                del self._pending_registrations[normalized_email]
                raise ValueError("OTP attempts exceeded. Request a new code")

            candidate_hash = self._hash_otp(otp.strip(), pending.otp_salt)
            if candidate_hash != pending.otp_hash:
                pending.attempts += 1
                self._pending_registrations[normalized_email] = pending
                raise ValueError("Invalid OTP")

            del self._pending_registrations[normalized_email]

        user = await self.repository.create(
            email=normalized_email,
            hashed_password=pending.hashed_password,
            role=pending.role.value,
        )
        return await self.issue_tokens(user_id=user.id, email=user.email, role=UserRole(user.role))

    async def request_login_otp(self, email: str, password: str) -> RegistrationOtpChallengeResponse:
        normalized_email = email.strip().lower()
        user = await self.repository.get_by_email(normalized_email)
        if user is None or not self.verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        otp_code = f"{secrets.randbelow(1_000_000):06d}"
        otp_salt = secrets.token_urlsafe(16)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.settings.login_otp_expire_minutes)
        pending = PendingLogin(
            user_id=user.id,
            email=user.email,
            role=UserRole(user.role),
            otp_hash=self._hash_otp(otp_code, otp_salt),
            otp_salt=otp_salt,
            expires_at=expires_at,
        )

        async with self._pending_lock:
            self._pending_logins[normalized_email] = pending

        delivered = await asyncio.to_thread(self._dispatch_otp_email, normalized_email, otp_code, "Sign-in")
        if not delivered and self.settings.environment.lower() == "production":
            raise ValueError("OTP delivery is not configured")

        dev_otp = None
        if not delivered and self.settings.environment.lower() != "production":
            logger.warning("Login OTP email transport unavailable for %s; using development fallback", normalized_email)
            dev_otp = otp_code

        return RegistrationOtpChallengeResponse(
            message="Sign-in verification code sent to your email",
            email=normalized_email,
            expires_in_seconds=self.settings.login_otp_expire_minutes * 60,
            dev_otp=dev_otp,
        )

    async def verify_login_otp(self, email: str, otp: str) -> AuthTokenResponse:
        normalized_email = email.strip().lower()

        async with self._pending_lock:
            pending = self._pending_logins.get(normalized_email)
            if pending is None:
                raise ValueError("No active sign-in OTP challenge found. Request a new code")

            now = datetime.now(timezone.utc)
            if pending.expires_at <= now:
                del self._pending_logins[normalized_email]
                raise ValueError("OTP has expired. Request a new code")

            if pending.attempts >= self.settings.registration_otp_max_attempts:
                del self._pending_logins[normalized_email]
                raise ValueError("OTP attempts exceeded. Request a new code")

            candidate_hash = self._hash_otp(otp.strip(), pending.otp_salt)
            if candidate_hash != pending.otp_hash:
                pending.attempts += 1
                self._pending_logins[normalized_email] = pending
                raise ValueError("Invalid OTP")

            del self._pending_logins[normalized_email]

        return await self.issue_tokens(user_id=pending.user_id, email=pending.email, role=pending.role)

    async def issue_tokens(self, user_id: UUID, email: str, role: UserRole) -> AuthTokenResponse:
        if self.refresh_repository is None:
            raise ValueError("Refresh repository is required")

        refresh_jti = self._new_token_jti()
        refresh_expiry = datetime.now(timezone.utc) + timedelta(minutes=self.settings.jwt_refresh_expire_minutes)
        session = await self.refresh_repository.create(user_id=user_id, token_jti=refresh_jti, expires_at=refresh_expiry)
        access_token = self.create_access_token(user_id=user_id, email=email, role=role, session_id=session.id)
        refresh_token = self.create_refresh_token(user_id=user_id, email=email, role=role, session_id=session.id, token_jti=refresh_jti)
        return AuthTokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> AuthTokenResponse:
        if self.refresh_repository is None:
            raise ValueError("Refresh repository is required")

        claims = self.decode_token_claims(refresh_token, expected_type="refresh")
        jti = str(claims.get("jti"))
        if not jti or not await self.refresh_repository.is_active(jti):
            raise ValueError("Refresh token is invalid or expired")

        session_id = UUID(str(claims["sid"]))
        user_id = UUID(str(claims["sub"]))
        role = UserRole(str(claims.get("role", UserRole.engineer.value)))
        email = str(claims.get("email", ""))

        rotated_jti = self._new_token_jti()
        refresh_expiry = datetime.now(timezone.utc) + timedelta(minutes=self.settings.jwt_refresh_expire_minutes)
        rotated_session = await self.refresh_repository.rotate(session_id=session_id, token_jti=rotated_jti, expires_at=refresh_expiry)
        if rotated_session is None:
            raise ValueError("Session not found")

        access_token = self.create_access_token(user_id=user_id, email=email, role=role, session_id=rotated_session.id)
        new_refresh_token = self.create_refresh_token(
            user_id=user_id,
            email=email,
            role=role,
            session_id=rotated_session.id,
            token_jti=rotated_jti,
        )
        return AuthTokenResponse(access_token=access_token, refresh_token=new_refresh_token)

    async def logout(self, refresh_token: str) -> None:
        if self.refresh_repository is None:
            raise ValueError("Refresh repository is required")
        claims = self.decode_token_claims(refresh_token, expected_type="refresh")
        token_jti = str(claims.get("jti", ""))
        if not token_jti or not await self.refresh_repository.revoke_by_jti(token_jti):
            raise ValueError("Refresh token is invalid")

    def create_access_token(self, user_id: UUID, email: str, role: UserRole, session_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.settings.jwt_expire_minutes)
        payload = {
            "iss": self.settings.jwt_issuer,
            "sub": str(user_id),
            "email": email,
            "role": role.value,
            "sid": str(session_id),
            "jti": self._new_token_jti(),
            "iat": int(now.timestamp()),
            "type": "access",
            "exp": expires_at,
        }
        return jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def create_refresh_token(self, user_id: UUID, email: str, role: UserRole, session_id: UUID, token_jti: str) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.settings.jwt_refresh_expire_minutes)
        payload = {
            "iss": self.settings.jwt_issuer,
            "sub": str(user_id),
            "email": email,
            "role": role.value,
            "sid": str(session_id),
            "jti": token_jti,
            "type": "refresh",
            "exp": expires_at,
        }
        return jwt.encode(payload, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)

    def decode_token_claims(self, token: str, expected_type: str) -> dict[str, str]:
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                issuer=self.settings.jwt_issuer,
            )
        except PyJWTError as exc:
            raise ValueError("Invalid token") from exc
        if payload.get("type") != expected_type:
            raise ValueError("Invalid token type")
        return payload

    def decode_access_token(self, token: str) -> AuthPrincipal:
        payload = self.decode_token_claims(token, expected_type="access")
        return AuthPrincipal(
            user_id=UUID(str(payload["sub"])),
            email=str(payload["email"]),
            role=UserRole(str(payload.get("role", UserRole.engineer.value))),
            session_id=UUID(str(payload["sid"])),
        )

    def _new_token_jti(self) -> str:
        return secrets.token_urlsafe(32)

    def _hash_otp(self, otp: str, salt: str) -> str:
        return sha256(f"{salt}:{otp}".encode("utf-8")).hexdigest()

    def _dispatch_otp_email(self, email: str, otp_code: str, context_label: str) -> bool:
        smtp_host = self.settings.smtp_host
        smtp_from = self.settings.smtp_from_email
        if not smtp_host or not smtp_from:
            return False

        expiry = self.settings.registration_otp_expire_minutes
        message = EmailMessage()
        message["Subject"] = f"Your The On Lookers {context_label.lower()} verification code"
        message["From"] = smtp_from
        message["To"] = email
        message.set_content(
            "\n".join(
                [
                    "Welcome to The On Lookers.",
                    "",
                    f"Your verification code is: {otp_code}",
                    f"This code expires in {expiry} minutes.",
                    f"Context: {context_label}",
                    "",
                    "If you did not request this, ignore this email.",
                ]
            )
        )

        admin_notification = self.settings.otp_admin_notification_email
        if admin_notification:
            message["Cc"] = admin_notification

        recipients = [email]
        if admin_notification:
            recipients.append(admin_notification)

        try:
            with smtplib.SMTP(smtp_host, self.settings.smtp_port, timeout=15) as smtp:
                if self.settings.smtp_use_tls:
                    smtp.starttls()
                if self.settings.smtp_username and self.settings.smtp_password:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.send_message(message, to_addrs=recipients)
            return True
        except Exception:  # pragma: no cover - external SMTP failures are environment-dependent
            logger.exception("Failed to dispatch OTP email to %s", email)
            return False
