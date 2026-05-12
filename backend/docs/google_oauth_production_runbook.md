# Google OAuth Production Debugging Runbook

This runbook is the operational path for diagnosing and resolving Google OAuth login failures in production.

For initial setup requirements, configuration inventory, and sign-off templates, see:

- `docs/google_oauth_configuration_requirements.md`
- `docs/google_oauth_configuration_record_template.md`
- `docs/google_oauth_verification_evidence_template.md`

## 1. Triage Signals

Typical user-facing errors:

- oauth_provider_not_configured
- oauth_invalid_grant
- oauth_token_timeout
- oauth_nonce_mismatch
- oauth_state_invalid
- OAuth popup unauthorized-domain errors from Firebase

Primary telemetry source:

- audit event type auth.oauth.callback
- audit event type auth.oauth.authorize
- audit event type auth.sso.exchange

## 2. Collect Detailed Error Logs

Collect recent callback failures:

```bash
curl "http://127.0.0.1:8000/api/v1/audit-logs?event_type=auth.oauth.callback&page=1&page_size=200" \
  -H "Authorization: Bearer <admin_access_token>"
```

Look for detail fields containing:

- provider=google
- code=oauth_invalid_grant
- code=oauth_token_timeout
- code=oauth_google_userinfo_failed
- code=oauth_state_provider_mismatch

## 3. Verify Google OAuth Client Configuration

Run server-side diagnostics:

```bash
python scripts/diagnose_google_oauth.py --base-url http://127.0.0.1:8000/api/v1 --strict
```

Required deployment variables:

- OAUTH_GOOGLE_CLIENT_ID
- OAUTH_GOOGLE_CLIENT_SECRET
- OAUTH_GOOGLE_REDIRECT_URI

Redirect URI must exactly match Google Cloud Console OAuth client settings.

Expected callback path:

- /api/v1/auth/oauth/google/callback

## 4. Verify OAuth Consent Screen and Scopes

The authorize URL must request:

- openid
- email
- profile

Manual Google Cloud checks:

- OAuth consent screen publishing status is valid for target users.
- Required scopes are approved and visible.
- App domain and support email are valid.

## 5. Verify Token Exchange and JWT Issuance

The backend callback route:

- Exchanges authorization code at Google token endpoint.
- Validates id_token audience against configured client ID.
- Validates nonce when claim is provided.
- Falls back to userinfo endpoint if identity claims are missing.
- Mints backend access and refresh JWTs via auth.sso.exchange.

Integration tests covering this path:

- backend/tests/integration/test_auth_oauth_google_callback.py

## 6. State and Nonce Validation

Checks enforced:

- OAuth state exists and signature is valid.
- State provider matches callback provider.
- State nonce exists.
- id_token nonce mismatch is rejected.

Failure error codes:

- oauth_state_missing
- oauth_state_invalid
- oauth_state_provider_mismatch
- oauth_state_nonce_missing
- oauth_nonce_mismatch

## 7. Refresh Token Storage and Rotation Security

Refresh-token lifecycle checks:

- Refresh sessions are persisted in refresh_sessions.
- Refresh token JTI rotates on /auth/refresh.
- Revoked sessions cannot be reused.
- Expired refresh tokens are rejected.

Integration coverage:

- backend/tests/integration/test_auth_refresh_rbac.py

## 8. Web and Mobile Flow Validation

Web validation:

- Query-parameter callback with access_token and refresh_token stores tokens and redirects.

Mobile validation:

- Hash-fragment callback with access_token and refresh_token stores tokens and redirects.

Frontend coverage:

- frontend/__tests__/auth-oauth-callback.page.test.tsx

## 9. SLO Monitoring (99.9% Login Success)

Generate rolling login SLO report:

```bash
python scripts/auth_login_slo_monitor.py --window-hours 24 --target-success-rate-pct 99.9 --strict
```

Events counted:

- auth.login
- auth.login.otp.verify
- auth.sso.exchange
- auth.oauth.callback

## 10. Firebase Domain Requirements

If Firebase popup fallback is enabled, verify authorized domains include:

- localhost
- 127.0.0.1
- production web hostnames

If Firebase is not intended for production OAuth, keep fallback disabled in frontend environment configuration and rely on backend OAuth redirect flow.
