# Model Risk Controls

This document describes drift control, fallback policy, and recalibration cadence for the corrosion model.

## Runtime Controls

Config keys:

- `MODEL_CONFIDENCE_FALLBACK_THRESHOLD`
- `MODEL_RISK_FLOOR_SCORE`
- `RECALIBRATION_CADENCE_DAYS`
- `DRIFT_ALERT_RELATIVE_THRESHOLD`

When `calibration_confidence` drops below threshold, simulation output applies conservative fallback behavior:

- raise design corrosion rate to upper uncertainty bound,
- floor risk score at configured risk floor,
- recompute uncertainty bands,
- mark response with fallback metadata and recalibration due date.

## Drift Detection

Drift gate command:

```bash
python scripts/check_model_drift.py --strict
```

Inputs:

- baseline file: `docs/model_drift_baseline.json`
- current calibration report: latest `artifacts/calibration_reports/calibration_report_*.json`

Gate fails when relative drift exceeds thresholds for global or region-level metrics.

## External Field Validation

Validation command:

```bash
python scripts/run_field_validation.py --dataset docs/field_validation_benchmark.csv --strict
```

Inputs:

- benchmark dataset with holdout partitions,
- global and region targets from `docs/field_validation_targets.json`.

Outputs:

- JSON and Markdown reports in `artifacts/field_validation`.

## Governance Cadence

- Drift check: every CI run on release branches.
- Field validation: at least weekly in staging and before production release.
- Full recalibration: every 30 days or immediately when drift gate fails.
