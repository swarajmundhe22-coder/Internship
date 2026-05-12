# Google OAuth Configuration Record Template

Use this template to capture exact configuration values and their locations in Firebase and Google Cloud.

## 1. Environment Metadata

| Field | Value |
|---|---|
| Environment | Development (Localhost) |
| Date Updated | 2026-04-04 |
| Updated By | s22td (with GitHub Copilot execution) |
| Reviewed By | Pending |
| Deployment Version | Local workspace validation |

## 2. Backend Environment Variables

| Variable Name | Value (Masked if Secret) | Secret Manager / Config Location | Owner | Last Rotated |
|---|---|---|---|---|
| OAUTH_GOOGLE_CLIENT_ID | 723167494467-5gv13dsb0vbroveefvh7obag3olp5kjn.apps.googleusercontent.com | backend/.env | Platform Auth Team | 2026-04-04 |
| OAUTH_GOOGLE_CLIENT_SECRET | SET (masked) | backend/.env | Platform Auth Team | 2026-04-04 |
| OAUTH_GOOGLE_REDIRECT_URI | http://localhost:8000/api/v1/auth/oauth/google/callback | backend/.env | Platform Auth Team | 2026-04-04 |
| OAUTH_FRONTEND_CALLBACK_URL | http://localhost:3000/auth/oauth/callback | backend/.env | Platform Auth Team | 2026-04-04 |

## 3. Google Cloud OAuth Client Settings

| Element | Console Location | Configured Value | Matches Backend? (Y/N) | Notes |
|---|---|---|---|---|
| OAuth Client Name | APIs and Services > Credentials | REQUIRED_FROM_GCP | Unknown | Must be Web Application client for this backend flow. |
| Client ID | APIs and Services > Credentials > OAuth 2.0 Client IDs | REQUIRED_FROM_GCP | Unknown | Must be copied to OAUTH_GOOGLE_CLIENT_ID. |
| Authorized Redirect URI #1 | OAuth client > Authorized redirect URIs | http://localhost:8000/api/v1/auth/oauth/google/callback | Unknown | Must exactly match backend variable. |
| Authorized Redirect URI #2 | OAuth client > Authorized redirect URIs | ADD_STAGING_OR_PROD_CALLBACK_URI | Unknown | Add each environment-specific callback URI. |
| Authorized JavaScript Origin #1 | OAuth client > Authorized JavaScript origins | http://localhost:3000 | Unknown | Required for browser-initiated OAuth/popup paths. |
| Authorized JavaScript Origin #2 | OAuth client > Authorized JavaScript origins | ADD_STAGING_OR_PROD_FRONTEND_ORIGIN | Unknown | Include deployed frontend origin(s). |

## 4. OAuth Consent Screen Configuration

| Element | Console Location | Configured Value | Verified (Y/N) | Notes |
|---|---|---|---|---|
| App Name | OAuth consent screen > App information | The On Lookers: Silent Decay | Partial | Taken from Firebase app metadata screenshot; confirm in GCP consent screen. |
| User Support Email | OAuth consent screen > App information | REQUIRED_VALID_SUPPORT_EMAIL | No | Must be populated in GCP consent screen. |
| Developer Contact Email | OAuth consent screen > App information | REQUIRED_VALID_DEV_CONTACT_EMAIL | No | Must be monitored mailbox. |
| User Type | OAuth consent screen | External or Internal per org policy | No | Confirm target audience model. |
| Publishing Status | OAuth consent screen | Testing or In production | No | Must permit target users to authenticate. |
| Authorized Domain #1 | OAuth consent screen > App domain | gen-lang-client-0898320750.firebaseapp.com | Partial | From Firebase authDomain; confirm present in consent screen. |
| Authorized Domain #2 | OAuth consent screen > App domain | REQUIRED_PRODUCTION_DOMAIN | No | Add deployed production domain. |

## 5. Consent Screen Scopes

| Scope | Required (Y/N) | Present (Y/N) | Notes |
|---|---|---|---|
| openid | Y | Yes (generated auth URL) | Verified in `google_oauth_diagnostics_20260404_065242Z.json`. |
| email | Y | Yes (generated auth URL) | Verified in `google_oauth_diagnostics_20260404_065242Z.json`. |
| profile | Y | Yes (generated auth URL) | Verified in `google_oauth_diagnostics_20260404_065242Z.json`. |

## 6. Firebase Authentication Domain Configuration

| Environment | Firebase Console Location | Authorized Domains Configured |
|---|---|---|
| Local | Authentication > Settings > Authorized domains | REQUIRED: localhost, 127.0.0.1 |
| Staging | Authentication > Settings > Authorized domains | REQUIRED: staging frontend hostname |
| Production | Authentication > Settings > Authorized domains | REQUIRED: production frontend hostname(s) |

## 7. Redirect URI Parity Check Record

| Check Item | Backend Value | GCP Value | Exact Match (Y/N) | Evidence Link |
|---|---|---|---|---|
| Scheme | http | REQUIRED_FROM_GCP | Unknown | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json |
| Hostname | localhost | REQUIRED_FROM_GCP | Unknown | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json |
| Port | 8000 | REQUIRED_FROM_GCP | Unknown | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json |
| Path | /api/v1/auth/oauth/google/callback | REQUIRED_FROM_GCP | Unknown | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json |
| Trailing Slash | none | REQUIRED_FROM_GCP | Unknown | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json |
| Full URI String | http://localhost:8000/api/v1/auth/oauth/google/callback | REQUIRED_FROM_GCP | Unknown | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json |

## 8. Custom Firebase/Web Settings (Reference)

Source: `frontend/components/outsource/local-simulated/firebase-applet-config.json`

| Setting | Value | Security / Implementation Note |
|---|---|---|
| projectId | gen-lang-client-0898320750 | Non-secret identifier; keep consistent across environments. |
| appId | 1:195401579051:web:1b5815e08124d46e03486e | Non-secret Firebase app identifier. |
| apiKey | AIzaSyDg1MmJ36wlybo4dXgIdYAercKsZALxDJY | API keys are not OAuth client secrets; still restrict by domain/app in console. |
| authDomain | gen-lang-client-0898320750.firebaseapp.com | Must align with Firebase auth configuration. |
| firestoreDatabaseId | ai-studio-9f5161f5-8465-46e9-bbca-d1a6e9987568 | Verify DB ID for tenant/data isolation expectations. |
| storageBucket | gen-lang-client-0898320750.firebasestorage.app | Validate storage rules before production usage. |
| messagingSenderId | 195401579051 | Used by Firebase messaging integrations. |

## 9. Security Considerations and Implementation Notes

1. Never commit `OAUTH_GOOGLE_CLIENT_SECRET` to source control.
2. Store OAuth client secret only in secret manager / protected environment variable store.
3. Rotate OAuth client secret on credential leak suspicion and at scheduled intervals.
4. Use HTTPS callback URI in production; current localhost HTTP URI is dev-only.
5. Keep backend OAuth credentials and Firebase config conceptually separate:
	- Backend OAuth uses GCP OAuth client ID/secret.
	- Firebase web config values do not replace backend OAuth client secret.

## 10. Client ID Mismatch Analysis and Resolution

| Item | Value |
|---|---|
| Previously configured web client ID | 195401579051-ebgc3bhknjg2gol4g797o36efj6si424.apps.googleusercontent.com |
| Whitelisted client ID in Google Cloud | 723167494467-5gv13dsb0vbroveefvh7obag3olp5kjn.apps.googleusercontent.com |
| Selected credential source | Whitelisted Google Cloud Web OAuth client |
| Resolution status | Applied in backend `.env`; diagnostics PASS in dev and production-mode probes |

Resolution notes:

1. Backend OAuth config now uses whitelisted client ID.
2. Authorize URL generation confirms correct client ID, redirect URI, scopes, state, and nonce.
3. Any GCP `redirect_uri_mismatch` or `invalid_client` errors should now be investigated at console redirect/origin configuration level, not application-level client-id mismatch.

## 11. Approval

| Role | Name | Date | Signature / Approval Reference |
|---|---|---|---|
| Platform Engineer | Pending | Pending | Pending |
| Security Reviewer | Pending | Pending | Pending |
| Service Owner | Pending | Pending | Pending |
