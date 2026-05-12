# Silent Decay: 30-Day Accelerated Hardening Plan

**Target**: Close top 3 gaps, increase prod readiness from 7.4/10 to 8.5/10

---

## Week 1: Diagnostics & Baseline

### Day 1-2: Audit Current State
- [ ] Load test simulation endpoint: measure max sustained TPS before 503 shedding
  ```bash
  python scripts/load_resilience_10x.py --base-url http://127.0.0.1:8000/api/v1 --concurrency 50
  ```
- [ ] Baseline p99 latency under normal load (log to `artifacts/baseline_p99.json`)
- [ ] Count unique active tenants (query `tenants` table)
- [ ] Measure top 10 material/environment combos (for offline cache)

### Day 3: Identify Pain Points
- [ ] Simulate 1-tenant surge: 100 concurrent forecast requests
  - Does it starve other tenants? Check admission rejections
- [ ] Test with unrealistic inputs: exposed_area = 1e12 m²
  - Does it get accepted? Inserted?
- [ ] Kill PostgreSQL for 30 seconds
  - What happens to in-flight prediction requests?

### Day 4: Create Test Scenarios
- [ ] Build synthetic tenant workload generator
- [ ] Document current failure modes in runbook

---

## Week 2: Gap 1 - Per-Tenant Admission (2 days)

### Day 5-6: Implement TenantAwareResilienceController

```bash
# 1. Copy template from IMPLEMENTATION_GUIDE.md
cp backend/app/core/resilience_tenant.py <new file>

# 2. Update main.py to use new controller
# OLD: resilience_controller = get_resilience_controller()
# NEW: resilience_controller = TenantAwareResilienceController()

# 3. Modify correlation_id_middleware to extract tenant_id from JWT

# 4. Add /api/v1/ops/resilience endpoint for metrics export
```

**Testing**:
```bash
# Verify per-tenant quotas are enforced
curl -H "Authorization: Bearer <token-tenant-1>" -X POST /api/v1/simulation ...
curl -H "Authorization: Bearer <token-tenant-2>" -X POST /api/v1/simulation ...
# Both should succeed even if total > legacy global_quota if quotas are balanced
```

**Validation**:
- [ ] Unit test: TenantAdmissionQuota.admit() logic
- [ ] Integration test: 3 tenants, verify quota fairness
- [ ] Load test: Repeat baseline; p99 latency should be unchanged

---

## Week 2-3: Gap 2 - API Contract Validation (2 days)

### Day 7-8: Deploy Validators

```bash
# 1. Add validation.py from IMPLEMENTATION_GUIDE.md
cp backend/app/core/validation.py <new file>

# 2. Update simulation route handler
# OLD: sim = await SimulationService.create(payload, session)
# NEW:
#   warnings = validator.validate(payload.dict())
#   if len(warnings) > 2 and not payload.override_validation_warnings:
#       raise HTTPException(422, detail={"warnings": warnings})

# 3. Add same logic to environment route handler

# 4. Add logging for warnings
```

**Testing**:
```python
# Unit test: Boundary checker
def test_impossible_area():
    validator = SimulationContractValidator()
    warnings = validator.validate({
        "exposed_area_m2": 1e12,  # Way too large
        ...
    })
    assert len(warnings) > 0
    assert "exceeds infrastructure maximum" in warnings[0]

# Integration test: API rejects impossible input
def test_api_rejects_impossible_simulation():
    response = client.post("/api/v1/simulation", json={
        "material_id": "...",
        "environment_id": "...",
        "exposed_area_m2": 1e12,  # Should fail
        ...
    })
    assert response.status_code == 422
    assert "override_validation_warnings" in response.json()["detail"]["message"]
```

---

## Week 3: Gap 4 - Offline Prediction Fallback (2 days)

### Day 9-10: Build Offline Cache

```bash
# 1. Create offline_predictor.py from IMPLEMENTATION_GUIDE.md
cp backend/app/core/offline_predictor.py <new file>

# 2. Add daily cache refresh script
cp scripts/refresh_offline_predictions.py <new file>

# 3. Schedule cron job (production):
# 0 3 * * * python scripts/refresh_offline_predictions.py

# 4. Modify simulation service to use offline predictor on DB errors

# 5. Test: Manually trigger offline fallback
```

**Testing**:
```python
# Unit test: Offline predictor returns cached result
def test_offline_predictor_returns_cache():
    predictor = OfflinePredictor()
    pred = predictor.predict(material_id, env_id)
    assert pred is not None
    assert pred.is_offline_fallback == True

# Integration test: Simulate DB down scenario
# Kill PostgreSQL, send prediction request
# Should return offline cache with caveat marker
```

**Monitoring**:
```sql
-- Count offline predictor activations (setup in app logging)
SELECT COUNT(*) FROM audit_logs
WHERE event_type = 'offline_predictor_activated'
AND created_at > NOW() - INTERVAL '24 hours';
```

---

## Week 4: Integration & Release

### Day 11-12: Full Integration Tests
```bash
pytest backend/tests/integration/ -v --capture=no
pytest backend/tests/unit/ -v --capture=no
```

### Day 13: Load Test All Changes
```bash
# Baseline → with changes: p99 should be <= 110% of baseline
python scripts/sustained_p99_analyzer.py \
  --base-url http://127.0.0.1:8000/api/v1 \
  --baseline docs/performance_baseline_reference.json \
  --strict
```

### Day 14: Staging Deployment
- Deploy to staging environment
- Run 24-hour soak test
- Monitor: p99 latency, error rates, admission metrics
- Compare with production baseline

---

## Checklist: Pre-Release Review

### Code Quality
- [ ] All new code has unit tests (40%+ coverage)
- [ ] Integration tests pass
- [ ] No lint/format issues: `black`, `isort`, `flake8`
- [ ] Type annotations added: `mypy --strict`

### Documentation
- [ ] Update `backend/README.md` with new /api/v1/ops/resilience endpoint
- [ ] Add runbook section: "Tenant Admission Troubleshooting"
- [ ] Document fallback cache refresh SLA (must complete in <5 min)

### Operations
- [ ] Metrics exported to Prometheus (validator warnings, offline activations)
- [ ] Grafana dashboard updated to show tenant quotas
- [ ] Alert on offline predictor activation (page on-call if > 5 activations/hour)
- [ ] Runbook for cache refresh failures added to docs/ops_sre_readiness_runbook.md

### Security
- [ ] No credential leaks in error messages (validator warnings, fallback caveat)
- [ ] Tenant quota bypass doesn't leak private tenant IDs in logs
- [ ] Offline cache doesn't contain recent proprietary predictions (>30 days stale)

### Performance
- [ ] p99 latency regression < 5%
- [ ] Memory usage increase < 50MB per 1000 concurrent connections
- [ ] Offline predictor cold-start (file load) < 100ms

---

## Success Metrics (Post-Deployment)

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Tenant quota fairness** | Std dev of rejection rates < 10% | `/api/v1/ops/resilience` → `tenant_quotas` |
| **Validation catch rate** | > 95% of impossible inputs rejected | Audit audit_logs for `validation_warning_rejected` |
| **Offline fallback availability** | Cache hit rate > 90% | Offline predictor metrics + historical top-100 combos |
| **p99 latency increase** | < 5% vs baseline | Compare `artifacts/baseline_p99.json` vs deployment |
| **Error budget consumed** | < 1% of SLO error budget | `(failed_requests / total_requests) vs 2%` |

---

## Rollback Plan (If Issues Arise)

**Symptoms**:
- p99 latency > baseline + 10%
- Offline predictor cache hit rate < 70%
- Validator rejecting >50% of legitimate simulations

**Rollback**:
```bash
# 1. Revert to previous commit
git revert <commit-hash>

# 2. Redeploy
kubectl rollout undo deployment/backend

# 3. Verify: run smoke tests
python scripts/phase8_smoke_test.py --base-url http://127.0.0.1:8000/api/v1

# 4. Post-mortem
# - Which component failed?
# - Was it tested in staging?
# - Add to next iteration's failure modes doc
```

---

## Why This Matters for Silent Decay Mission

Infrastructure operators trust Silent Decay to predict failures **before** they happen:
- Bridge collapse prediction
- Pipeline leak detection
- Maritime vessel corrosion risk

**If these protections fail:**

| Current State | With Gaps | With Fixes |
|---------------|-----------|-----------|
| Tenant A's surge | → starves Tenant B | → Tenant B gets fair quota |
| Outlier data | → poisons predictions | → rejected + logged for review |
| DB briefly down | → mission-critical predictions fail | → fallback cache provides answers |
| Prediction fails | → operator blind to risk | → explicit caveat marker + user decides |

These 3 gaps → $X000s in infrastructure damage if not closed.

---

## Questions for Product/Operations

Before finalizing:

1. **Field calibration timeline**: When can we partner with real infrastructure operators for ground-truth data?
2. **RTO/RPO targets**: How fast must we recover from database failure?
3. **Multi-region failover**: Should Tier 1 customers get predictions in 2+ regions?
4. **Audit retention**: How long must validation history/warnings be kept?

---

## Next Review: 60 Days

After 30-day hardening complete:
1. Gaps 1, 2, 4 status: Complete ✅
2. Gaps 5, 6, 7: Prioritize for next sprint
3. Overall readiness score: Target 8.5/10 → 8.8/10
4. Field calibration partnerships: Status update?

**Meeting**: Architecture review with ops/SRE team
