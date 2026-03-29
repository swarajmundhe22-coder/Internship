# Production Readiness Checklist

This checklist consolidates the backend CI gate sequence into release sign-off criteria. A release candidate is not ready unless every required item below is checked and the linked evidence is archived with the release record.

## Sign-Off Rules

- All required gates must pass on the release candidate commit.
- Evidence must include command output, generated artifacts, and the reviewer who approved the gate.
- Any failed gate blocks release promotion until the underlying issue is resolved and the gate is rerun successfully.
- If production data is used for validation, it must be a vetted holdout dataset with documented provenance and retention rules.

## Gate Checklist

### 1. Dependency and Environment Setup

Release sign-off criteria:

- Dependencies install cleanly in the target Python version.
- Database services are reachable and migrations apply without error.
- The runtime environment matches the intended deployment shape closely enough to make downstream gate results meaningful.

Evidence:

- CI job logs from dependency installation.
- Successful `alembic upgrade head` output.

### 2. Unit Test Suite

Release sign-off criteria:

- `pytest -q` passes with no unexpected failures.
- Test failures are not masked by skips, xfails, or fixture shortcuts that invalidate coverage.

Evidence:

- Pytest output attached to the release record.

### 3. Calibration Envelope Validation

Release sign-off criteria:

- `python scripts/generate_calibration_report.py --strict` passes.
- All calibration scenarios remain inside the approved envelope.
- Any drift from the expected envelope is explained and accepted by the model owner.

Evidence:

- Calibration report artifacts in `artifacts/calibration_reports/`.

### 4. External Field Validation

Release sign-off criteria:

- `python scripts/run_field_validation.py --dataset docs/field_validation_benchmark.csv --strict` passes.
- Regional and global validation targets are satisfied.
- The benchmark dataset is representative of the release target population.

Evidence:

- Field validation artifacts in `artifacts/field_validation/`.
- Dataset provenance and review notes.

### 5. Model Drift Gate

Release sign-off criteria:

- `python scripts/check_model_drift.py --strict` passes.
- Drift metrics remain within the baseline bounds.
- Any drift explanation is recorded before promotion.

Evidence:

- Drift reports in `artifacts/model_drift/`.
- Baseline reference from `docs/model_drift_baseline.json`.

### 6. API Availability Check

Release sign-off criteria:

- The API starts successfully on the release image.
- `/api/v1/health` responds successfully before any live gate begins.
- Health failures are investigated before continuing.

Evidence:

- Server startup logs.
- Health probe output.

### 7. Security Gates

Release sign-off criteria:

- `python -m pip_audit -r requirements.txt` passes.
- `python -m bandit -r app scripts -x tests -lll -ii` passes.
- `python scripts/security_dast_gate.py --base-url http://127.0.0.1:8000/api/v1 --strict` passes.
- No unresolved high-severity security findings remain open.

Evidence:

- Dependency audit output.
- Bandit report output.
- DAST report artifacts in `artifacts/security_reports/`.

### 8. Performance and Reliability Gates

Release sign-off criteria:

- `python scripts/performance_reliability_gate.py --base-url http://127.0.0.1:8000/api/v1 --p95-budget-ms 1200 --p99-budget-ms 2000 --error-budget-rate 0.02 --strict` passes.
- `python scripts/failure_mode_chaos_gate.py --base-url http://127.0.0.1:8000/api/v1 --strict` passes.
- Latency and error budget behavior stay within the published SLOs.
- Malformed, unauthorized, and negative-path traffic fails safely.

Evidence:

- Performance artifacts in `artifacts/performance_reports/`.
- Chaos artifacts in `artifacts/chaos_reports/`.
- Runbook alignment with [docs/performance_reliability_runbook.md](performance_reliability_runbook.md).

### 9. Backup and Restore Drill

Release sign-off criteria:

- `python scripts/backup_restore_drill.py --strict` passes.
- The latest successful drill is within the required operational window.
- Restore evidence is retained for audit and incident review.

Evidence:

- Backup drill artifacts in `artifacts/backup_drills/`.
- Runbook alignment with [docs/ops_sre_readiness_runbook.md](ops_sre_readiness_runbook.md).

### 10. Release Artifact Review

Release sign-off criteria:

- All gate artifacts are collected in the release bundle.
- The release owner confirms no gate was bypassed.
- Operations, security, and engineering sign off before promotion.

Evidence:

- Release checklist completion record.
- Final approval note from the release owner.

## Final Release Decision

A release may be approved only when every required gate above is green, all evidence is attached, and any exceptions are explicitly documented with owner approval and an expiration date.