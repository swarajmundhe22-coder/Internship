# Security and Compliance Runbook

This document codifies secrets rotation policy, CI security gates, and penetration test sign-off requirements.

## Secrets Rotation Policy

### Scope

Apply to all production and staging credentials:

- `JWT_SECRET_KEY`
- SMTP credentials
- database credentials
- NVIDIA and payment provider API keys
- webhook signing secrets
- device and satellite integration secrets

### Rotation Cadence

- High-risk credentials: every 30 days.
- Standard credentials: every 90 days.
- Emergency rotation: immediate after suspected leak, staff offboarding, or failed compliance control.

### Rotation Procedure

1. Create replacement credential in provider console.
2. Store secret in approved secret manager.
3. Deploy to staging and run smoke tests.
4. Promote to production during low-risk change window.
5. Revoke old credential and confirm no dependent failures.
6. Record ticket ID, operator, reviewer, and timestamp.

## CI Security Gates

Required gates run in backend CI:

- dependency audit (`pip-audit`)
- static analysis (`bandit`)
- dynamic API gate (`python scripts/security_dast_gate.py --strict`)

Blocking policy:

- New high/critical vulnerabilities block merge.
- High-confidence high-severity bandit findings block merge.
- Failing DAST checks block merge.

## Penetration Testing Sign-off

External penetration testing must be completed before production cutover.

Required artifacts:

- Scope statement.
- Methodology and toolchain.
- Findings with CVSS and exploitability notes.
- Retest report for remediated findings.
- Sign-off by Security Lead and Engineering Lead.

### Sign-off Template

- Test window:
- Tester organization:
- In-scope endpoints:
- Critical findings open:
- High findings open:
- Exceptions approved (ID list):
- Remediation SLA accepted by:
- Final production sign-off date:

## Exception and Waiver Policy

Any temporary gate bypass requires:

- documented risk acceptance,
- compensating controls,
- expiry date,
- approver from security leadership.
