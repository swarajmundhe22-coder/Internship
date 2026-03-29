# Performance and Reliability Runbook

This runbook defines sustained-load and failure-mode validation expected before release.

## Staging Parity Requirement

All performance and reliability gates must run against a staging environment that matches production for:

- application version,
- database engine and schema,
- network policy,
- CPU/memory limits,
- external dependency mocks or mirrors.

## Sustained-Load Gate

Command:

```bash
python scripts/performance_reliability_gate.py --strict
```

Checks:

- p95 and p99 latency budgets.
- error budget rate.
- controlled behavior for unauthorized and malformed requests.

## Failure-Mode and Chaos Gate

Command:

```bash
python scripts/failure_mode_chaos_gate.py --strict
```

Checks:

- no unexpected 5xx responses during valid and malformed request bursts,
- unauthorized and invalid-token paths reject correctly,
- malformed and negative-value payloads fail with controlled validation responses.

## Release Criteria

A release candidate is eligible only when all are true:

- sustained-load gate passes,
- chaos/failure-mode gate passes,
- no unresolved P0/P1 reliability issues,
- latest backup drill passed in last 30 days.

## Regression Handling

If any gate fails:

1. block release branch promotion,
2. open reliability incident with owner,
3. attach report artifacts from `artifacts/performance_reports` and `artifacts/chaos_reports`,
4. rerun gates only after fix merge.
