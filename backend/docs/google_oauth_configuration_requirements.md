# Google OAuth Configuration Requirements and Verification Guide

This document defines the exact setup requirements for Google OAuth across Firebase, Google Cloud Platform, and backend environment configuration.

Scope:

- Google OAuth client configuration (client ID, client secret, redirect URI)
- OAuth consent screen requirements
- Firebase authorized domains for popup implementations
- Validation procedures for redirect URI parity and end-to-end auth flow
- Troubleshooting and documentation templates

## 1. Required Configuration Inventory

| Configuration Element | Required Value Pattern | Source Console Location | Backend Variable / Usage | Notes |
|---|---|---|---|---|
| Google OAuth Client ID | `<id>.apps.googleusercontent.com` | Google Cloud Console > APIs and Services > Credentials > OAuth 2.0 Client IDs > Web client | `OAUTH_GOOGLE_CLIENT_ID` | Must match `aud` in Google ID token validation. |
| Google OAuth Client Secret | Secret string | Google Cloud Console > APIs and Services > Credentials > OAuth 2.0 Client IDs > Web client | `OAUTH_GOOGLE_CLIENT_SECRET` | Keep in secret manager, never in frontend. |
| Google Redirect URI | Full backend callback URL | Google Cloud Console > APIs and Services > Credentials > OAuth 2.0 Client IDs > Web client > Authorized redirect URIs | `OAUTH_GOOGLE_REDIRECT_URI` | Must exactly match GCP redirect URI entry. |
| Frontend OAuth Callback URL | Full frontend callback URL | Application deployment config | `OAUTH_FRONTEND_CALLBACK_URL` | Used for final browser redirect after backend callback. |
| OAuth Scopes | `openid email profile` | Google Cloud Console > APIs and Services > OAuth consent screen > Data access | Generated in backend authorize URL | Mandatory for identity retrieval. |
| OAuth App Name | Product-facing app name | Google Cloud Console > APIs and Services > OAuth consent screen > App information | N/A | Must reflect production application naming. |
| User Support Email | Valid monitored mailbox | Google Cloud Console > APIs and Services > OAuth consent screen > App information | N/A | Must be owned by operator/admin team. |
| Authorized Domains (Consent Screen) | Domain list | Google Cloud Console > APIs and Services > OAuth consent screen > App domain | N/A | Must include all public domains used in OAuth flow. |
| Firebase Authorized Domains | Domain list | Firebase Console > Authentication > Settings > Authorized domains | Used by popup flow | Required if Firebase popup flow is enabled in any environment. |

## 2. Prerequisites

1. Access to Firebase project owner/editor role.
2. Access to Google Cloud project owner/editor role for the same Firebase-linked project.
3. Backend deployment access for setting secure environment variables.
4. Confirmed environment list:
   - local
   - staging
   - production

## 3. Firebase Console Requirements

### 3.1 Enable Google Provider

1. Open Firebase Console.
2. Navigate to Authentication > Sign-in method.
3. Enable Google sign-in provider.
4. Set support email.
5. Save.

### 3.2 Configure Firebase Authorized Domains (Popup Flow)

If popup sign-in is used, add every environment hostname:

1. Go to Authentication > Settings > Authorized domains.
2. Add local domains when needed:
   - localhost
   - 127.0.0.1
3. Add staging and production web app hostnames.
4. Save and verify domains appear in the list.

Recommended domain matrix:

| Environment | Domain Entries Required in Firebase Authorized Domains |
|---|---|
| Local | localhost, 127.0.0.1 |
| Staging | staging web hostname |
| Production | production web hostname(s) |

## 4. Google Cloud Console Requirements

### 4.1 OAuth Consent Screen Configuration

Navigate to Google Cloud Console > APIs and Services > OAuth consent screen.

Required fields:

1. User type set appropriately for deployment audience.
2. App name configured.
3. User support email configured and monitored.
4. Developer contact email configured.
5. Authorized domains include all public domains used in login flow.
6. Data access scopes include:
   - openid
   - email
   - profile
7. Publishing status appropriate for target users.
8. If in testing mode, target user accounts must be added as test users.

### 4.2 OAuth Client Credentials

Navigate to Google Cloud Console > APIs and Services > Credentials.

For OAuth 2.0 Client ID (Web application):

1. Create or edit a Web application OAuth client.
2. Verify Authorized JavaScript origins for frontend hosts (if browser popup or JS flow depends on these).
3. Verify Authorized redirect URIs contains exact backend callback URL(s):
   - `<scheme>://<host>[:port]/api/v1/auth/oauth/google/callback`
4. Copy client ID and client secret.
5. Store secret in secret manager.

## 5. Backend Environment Configuration Requirements

Set these values in backend environment (deployment secrets):

- `OAUTH_GOOGLE_CLIENT_ID`
- `OAUTH_GOOGLE_CLIENT_SECRET`
- `OAUTH_GOOGLE_REDIRECT_URI`
- `OAUTH_FRONTEND_CALLBACK_URL`

Optional but recommended:

- Separate values per environment (local/staging/prod)
- Secret rotation metadata and owner tags

## 6. Redirect URI Parity Verification Process

Redirect URI mismatch is a top failure source. Use this exact process.

### 6.1 Backend Value Confirmation

1. Read deployed backend value for `OAUTH_GOOGLE_REDIRECT_URI`.
2. Confirm expected path ends with `/api/v1/auth/oauth/google/callback`.

### 6.2 Google Cloud Value Confirmation

1. Open Google Cloud Console OAuth client.
2. Copy one entry from Authorized redirect URIs.
3. Compare with backend value character-by-character.

### 6.3 Exact-Match Rules

All of these must match exactly:

1. Scheme (http vs https)
2. Hostname
3. Port
4. Path
5. Trailing slash behavior

### 6.4 Automated Parity Check

Run diagnostics script:

`python scripts/diagnose_google_oauth.py --base-url http://127.0.0.1:8000/api/v1 --strict`

Pass criteria includes:

- `auth_url_redirect_uri_matches` = true
- `auth_url_client_id_matches` = true
- `auth_url_scope_contains_openid` = true
- `auth_url_scope_contains_email` = true
- `auth_url_scope_contains_profile` = true

## 7. End-to-End Verification Procedures

### 7.1 Configuration Health Verification

1. Run OAuth diagnostics script in strict mode.
2. Confirm report status PASS.
3. Archive report under security artifacts.

### 7.2 OAuth Flow Manual Test

1. Open login page in private browser window.
2. Start Google sign-in.
3. Select account and grant consent.
4. Confirm redirect reaches frontend callback.
5. Confirm app session is established.

### 7.3 Token Validation Verification

Confirm successful callback behavior:

1. Backend exchanges code for token.
2. ID token audience equals configured client ID.
3. Nonce/state validations pass.
4. Backend issues internal access and refresh tokens.

Validation sources:

- Backend logs / audit events for `auth.oauth.callback` and `auth.sso.exchange`
- Integration tests:
  - `tests/integration/test_auth_oauth_google_callback.py`
  - `tests/integration/test_auth_refresh_rbac.py`

### 7.4 Error Handling Scenario Verification

Validate the following scenarios:

| Scenario | Expected Behavior | Expected Error Code |
|---|---|---|
| Missing client ID/secret/redirect URI | OAuth authorize returns provider not configured | `oauth_provider_not_configured` |
| Expired/revoked authorization code | Callback redirects to login with actionable message | `oauth_invalid_grant` |
| Token endpoint timeout | Callback handles timeout gracefully | `oauth_token_timeout` |
| Invalid state | Callback rejected | `oauth_state_invalid` |
| Provider mismatch in state | Callback rejected | `oauth_state_provider_mismatch` |
| Nonce mismatch | Callback rejected | `oauth_nonce_mismatch` |
| Firebase popup unauthorized domain | Popup failure until domain is added | Firebase unauthorized-domain error |

### 7.5 Ongoing SLO Verification

Run auth login SLO monitor:

`python scripts/auth_login_slo_monitor.py --window-hours 24 --target-success-rate-pct 99.9 --strict`

Pass criteria:

- Login success rate >= 99.9%

## 8. Troubleshooting Guide

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `oauth_provider_not_configured` | Missing backend env variables | Set `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET`, `OAUTH_GOOGLE_REDIRECT_URI` and redeploy. |
| `redirect_uri_mismatch` from Google | URI mismatch between backend and GCP OAuth client | Copy exact URI from backend config into GCP Authorized redirect URIs. |
| Popup blocked unauthorized-domain | Missing Firebase authorized domain | Add hostname in Firebase Authentication authorized domains. |
| `oauth_invalid_client` | Wrong client credentials in backend | Rotate and reapply correct client ID/secret from GCP OAuth client. |
| `oauth_invalid_grant` | Expired/reused code or wrong client binding | Retry login, validate correct OAuth client and redirect URI alignment. |
| `oauth_google_audience_mismatch` | ID token audience does not match configured client ID | Ensure backend client ID belongs to the OAuth client issuing the token. |
| Works locally but fails in production | Production host/domain not configured in consent screen or Firebase domains | Add production domains in GCP consent screen and Firebase authorized domains. |

## 9. Required Documentation and Evidence

Use these templates to record configuration and verification details:

- `docs/google_oauth_configuration_record_template.md`
- `docs/google_oauth_verification_evidence_template.md`

Minimum audit evidence to retain:

1. OAuth client metadata (non-secret fields)
2. Redirect URI parity check records
3. Consent screen field values
4. Firebase authorized domain list per environment
5. Diagnostics report output
6. Manual flow test results
7. SLO report output

## 10. Sign-Off Checklist

Mark all items complete before release:

1. Backend environment variables set and validated.
2. Redirect URI parity check passed.
3. Consent screen configuration complete and published/test-user-ready.
4. Firebase authorized domains complete for active environments.
5. Automated diagnostics script passed.
6. Integration tests passed.
7. Manual OAuth flow validated in browser.
8. SLO check passed.
