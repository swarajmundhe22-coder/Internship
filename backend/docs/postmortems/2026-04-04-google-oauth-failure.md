# Postmortem: Google OAuth Authentication Failure

Date: 2026-04-04
Owner: Platform Authentication Team
Status: Closed with remediation deployed

## Summary

Users were unable to complete Google sign-in reliably. Production-like failures surfaced as OAuth popup/domain errors and callback token-exchange failures with insufficiently granular diagnostics.

## Impact

- Users saw social-login failure messages and were redirected back to login.
- OAuth troubleshooting was slower due to generic callback errors.
- Risk of login success-rate degradation below the 99.9% SLO target.

## Root Cause

Two combined factors:

1. OAuth provider configuration and callback failures were not surfaced with actionable error codes.
2. Frontend fallback behavior could route users into Firebase popup flows where domain authorization was not guaranteed.

## Contributing Factors

- Token-exchange/network exceptions were collapsed into broad failure paths.
- State/nonce mismatch diagnostics were not explicit.
- Limited automated tests for invalid_grant and timeout conditions.

## Detection

Detected through:

- User-reported OAuth failures on login
- Callback-level failures in auth flow

## Resolution

Implemented in this release:

- Granular OAuth callback error handling with structured codes.
- State provider and nonce validation checks hardened.
- Token-exchange, userinfo, and claim-parse failure classes separated.
- Frontend callback now propagates oauth_error_code to login UI.
- Login UI maps OAuth error codes to operator-actionable messages.
- Added integration tests for invalid_grant, timeout, state mismatch, and successful callback JWT issuance.
- Added expired refresh-token integration test.
- Added operational scripts for OAuth diagnostics and auth SLO monitoring.

## Corrective Actions

Completed:

- backend/app/api/auth_routes.py hardening and audit signal improvements.
- backend/tests/integration/test_auth_oauth_google_callback.py added.
- backend/tests/integration/test_auth_refresh_rbac.py expanded with expired-token test.
- frontend/pages/auth/oauth/callback.tsx error-code propagation.
- frontend/pages/auth/login.tsx OAuth error-code mappings.
- frontend/__tests__/auth-oauth-callback.page.test.tsx added.
- backend/scripts/diagnose_google_oauth.py added.
- backend/scripts/auth_login_slo_monitor.py added.
- backend/docs/google_oauth_production_runbook.md added.

Follow-up:

- Add dashboard panel for auth.oauth.callback success/failure by code.
- Add alert when oauth_invalid_grant or oauth_token_timeout rates exceed baseline.

## Prevention

- Run OAuth diagnostics script before each production deployment.
- Enforce callback integration tests in CI for auth routes.
- Track rolling auth login success SLO with strict gate in operational checks.
