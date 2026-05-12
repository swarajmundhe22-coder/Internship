# Google OAuth Verification Evidence Template

Use this template to capture objective verification evidence for OAuth readiness.

## 1. Test Execution Metadata

| Field | Value |
|---|---|
| Environment | Development local + Production-mode policy check |
| Date | 2026-04-04 |
| Tester | s22td |
| Backend Base URL | http://127.0.0.1:8000/api/v1 |
| Frontend Base URL | http://localhost:3000 |

Tester credentials / identities used:

- Operator account: local workstation user `s22td`
- Synthetic probe identity: oauth-probe-d2e194c0adc742d4a187d4e4aca67403@example.com

## 2. Automated Verification Results

### 2.0 Configuration Propagation Check

Runtime config inspection output:

- oauth_frontend_callback_url: `http://localhost:3000/auth/oauth/callback`
- oauth_google_redirect_uri: `http://localhost:8000/api/v1/auth/oauth/google/callback`
- oauth_google_client_id_present: `True`
- oauth_google_client_secret_present: `True`

Result: local propagation confirmed for client ID, client secret, and redirect URI.

### 2.1 OAuth Diagnostics Script

Command:

python scripts/diagnose_google_oauth.py --base-url <BASE_URL>/api/v1 --strict

| Check Name | Result (PASS/FAIL) | Evidence (Report Path / Screenshot) | Notes |
|---|---|---|---|
| google_client_id_present | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Whitelisted client ID loaded. |
| google_client_secret_present | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Client secret present. |
| google_redirect_uri_present | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Local redirect URI configured. |
| auth_url_client_id_matches | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Authorize URL uses whitelisted client ID. |
| auth_url_redirect_uri_matches | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Redirect URI parity passes for dev. |
| auth_url_scope_contains_openid | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Required scope present. |
| auth_url_scope_contains_email | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Required scope present. |
| auth_url_scope_contains_profile | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Required scope present. |
| auth_url_has_state | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | State present. |
| auth_url_has_nonce | PASS | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Nonce present. |

Latest diagnostics summary:

- Development report: `backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json` (PASS)
- Production-mode report: `backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065623Z.json` (PASS)

Production policy check:

- Report: `backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065623Z.json`
- Additional result: `google_redirect_uri_https_in_production` = PASS

### 2.2 Integration Tests

Command:

pytest tests/integration/test_auth_oauth_google_callback.py tests/integration/test_auth_refresh_rbac.py -q

| Test Area | Result (PASS/FAIL) | Evidence | Notes |
|---|---|---|---|
| OAuth callback success path | PASS | pytest output, 9 passed in 1.90s | Covered by `test_auth_oauth_google_callback.py`. |
| invalid_grant handling | PASS | pytest output, 9 passed in 1.90s | Covered by callback integration tests. |
| timeout handling | PASS | pytest output, 9 passed in 1.90s | Covered by callback integration tests. |
| state/provider mismatch handling | PASS | pytest output, 9 passed in 1.90s | Covered by callback integration tests. |
| expired refresh token rejection | PASS | pytest output, 9 passed in 1.90s | Covered by `test_auth_refresh_rbac.py`. |

### 2.3 Auth SLO Monitor

Command:

python scripts/auth_login_slo_monitor.py --window-hours 24 --target-success-rate-pct 99.9 --strict

| Metric | Value | Threshold | Result |
|---|---|---|---|
| Login success rate | 100.0% | >= 99.9% | PASS |
| Attempts | 5 | N/A | INFO |
| Failures | 0 | N/A | INFO |

Evidence:

- `backend/artifacts/security_reports/auth_login_slo_20260404_054504Z.json`
- `backend/artifacts/security_reports/auth_login_slo_20260404_054504Z.md`

### 2.4 Synthetic Login Reliability Probe (Latency/Error/Availability)

Command type:

- Python probe executed in workspace environment against `/auth/login` and `/auth/refresh`

Baseline metrics:

| Metric | Value | Threshold | Result |
|---|---|---|---|
| Login availability | 100.0% | >= 99.9% | PASS |
| Login error rate | 0.0% | <= 0.1% | PASS |
| Login latency p95 | 39.83 ms | <= 500 ms | PASS |
| Refresh token (valid) | true | true | PASS |
| Refresh token (invalid) status | 401 | 401 | PASS |

Evidence:

- `backend/artifacts/security_reports/auth_login_probe_20260404_054609Z.json`

## 3. Manual Flow Verification

| Scenario | Steps Executed | Expected Result | Actual Result | PASS/FAIL | Evidence |
|---|---|---|---|---|---|
| Web login with Google account select | Startup path validated via authorize probes in dev and prod-mode | Redirect to callback and app session established | Authorization URL generated successfully with whitelisted client ID | PASS (startup) | backend/artifacts/security_reports/oauth_authorize_probe_20260404_065718Z.json |
| Login cancellation | Manual browser scenario not executed | User returned to login with controlled error | Not executed | NOT_RUN | Add browser HAR + screenshot evidence |
| Invalid/expired grant simulation | Executed via integration tests (mocked provider responses) | Controlled error message | Passed in integration suite | PASS | `backend/tests/integration/test_auth_oauth_google_callback.py` |
| Popup unauthorized domain simulation | Not re-run in this pass | Domain error reproduced and diagnosed | Prior known behavior, pending retest | PARTIAL | Add Firebase console screenshot evidence |
| Firebase Google SSO token exchange API | POST /auth/sso/exchange with provider=google and gmail identity | Backend should issue access and refresh tokens | Returned 200 with token payload | PASS | Runtime probe output 2026-04-04 05:54 UTC |

Manual evidence placeholders:

1. Google Cloud OAuth client screenshot path: `PENDING_CAPTURE`
2. OAuth consent screen screenshot path: `PENDING_CAPTURE`
3. Firebase authorized domains screenshot path: `PENDING_CAPTURE`
4. Browser network HAR trace path: `PENDING_CAPTURE`

## 4. Token Validation Evidence

| Validation Item | Result (PASS/FAIL) | Evidence | Notes |
|---|---|---|---|
| Google ID token aud matches configured client ID | PASS (config-level) | backend/artifacts/security_reports/google_oauth_diagnostics_20260404_065242Z.json | Authorize URL client_id is whitelisted ID. Full live callback token exchange requires browser consent/code step. |
| Google ID token nonce matches state nonce | PASS (test) | `backend/tests/integration/test_auth_oauth_google_callback.py` | Verified in callback integration path. |
| Backend access token issued | PASS | auth register/login responses + integration tests | Confirmed via auth probe and tests. |
| Backend refresh token issued | PASS | auth register response + refresh probe | Valid refresh accepted, invalid refresh rejected with 401. |

## 5. Error Handling Verification Matrix

| Error Condition | Expected Code | Observed Code | PASS/FAIL | Notes |
|---|---|---|---|---|
| Missing provider config | oauth_provider_not_configured | oauth_provider_not_configured | PASS | From diagnostics authorize error payload. |
| Invalid grant | oauth_invalid_grant | oauth_invalid_grant | PASS | Verified in integration test coverage. |
| Token timeout | oauth_token_timeout | oauth_token_timeout | PASS | Verified in integration test coverage. |
| State invalid | oauth_state_invalid | oauth_state_invalid | PASS | Covered by callback error handling tests/policies. |
| State provider mismatch | oauth_state_provider_mismatch | oauth_state_provider_mismatch | PASS | Verified in integration tests. |
| Nonce mismatch | oauth_nonce_mismatch | oauth_nonce_mismatch | PASS | Covered by callback nonce handling. |

## 6. Issue Log (Severity and Remediation)

| Severity | Issue | Evidence | Recommended Remediation |
|---|---|---|---|
| Medium | Full interactive browser consent + callback completion not captured in this non-interactive session | Manual flow section | Capture browser HAR/screenshot evidence during live account-select test. |
| Medium | Production deployment must set production callback URI in real environment secret store | configuration records | Apply prod `OAUTH_GOOGLE_REDIRECT_URI` and mirror URI in GCP authorized redirect list. |

## 7. Alerting and Threshold Configuration

Proposed SLO thresholds:

1. Login success rate >= 99.9% (24h rolling window).
2. Login availability >= 99.9% for synthetic probe window.
3. Login error rate <= 0.1% for synthetic probe window.
4. Login p95 latency <= 500 ms for synthetic probe window.

Alert recommendations:

1. Trigger warning when success rate < 99.95% and critical when < 99.9%.
2. Trigger warning when p95 latency > 400 ms and critical when > 500 ms.
3. Trigger immediate critical alert on sustained `oauth_provider_not_configured` or `oauth_invalid_client` events.

Current status: Threshold values documented; external alert pipeline wiring (PagerDuty/Email/ChatOps) pending platform integration.

## 8. Final Readiness Decision

| Item | Status |
|---|---|
| All required checks passed | Mostly (automated checks passed) |
| Open issues remain | Yes (manual interactive evidence pending) |
| Release recommendation | Client-ID mismatch resolved. Proceed with Google sign-in rollout after one live browser consent/callback confirmation and console screenshot evidence capture. |

Approver:

- Name: Pending
- Role: Pending
- Date: Pending
