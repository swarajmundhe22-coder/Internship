# Silent Decay Platform: Comprehensive Architectural Review
**Date**: 2026-04-08
**Phase**: 10 (Governance Consortium)
**Scope**: Full-stack assessment aligned to mission-critical reliability requirements

---

## Executive Summary

The **Silent Decay** platform is a well-engineered, production-grade predictive infrastructure intelligence system. It has demonstrated capability across 10 phases of incremental hardening, enterprise integration, and operational maturity. The codebase shows strong fundamentals in:

- ✅ **Reliability patterns**: Resilience controls, circuit breakers, connection pool monitoring
- ✅ **Observability**: Correlation ID tracing, Prometheus metrics, performance budgets (p99)
- ✅ **Security**: RBAC enforcement, OAuth/OTP flows, audit logging, CSP headers
- ✅ **Data integrity**: Optimistic locking, check constraints, foreign key enforcement
- ✅ **Multi-tenancy**: Tenant isolation, billing lifecycle, role-based access

However, **mission-critical infrastructure applications** (where corrosion predicts bridge collapses or pipeline failures) require three additional layers of rigor:

1. **Unambiguous data contract enforcement** at API boundaries
2. **Closed-loop field validation** with real-world sensor feedback
3. **Automated graceful degradation** when critical subsystems fail

This review identifies **7 actionable gaps** and provides implementation blueprints to bridge them.

---

## Current Architecture Assessment

### 1. **Backend Microarchitecture** ✅ Solid

**Strengths:**
- Clean service/repository/model layering with clear boundaries
- Async/await throughout (FastAPI + asyncpg)
- Connection pool tuned to CPU count: `pool_size = max(4, cpu_count * 2)`
- Leak detection on connections held > 5 seconds
- Pre-ping enabled on database checkout to detect stale connections

**Code Sample** (session.py):
```python
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,           # 4-8 (cpu-aware)
    max_overflow=settings.db_pool_max_overflow, # 2-4
    pool_timeout=5,                             # fail fast
    pool_pre_ping=True,                         # alive check
)
```

**Risk**: Connection pool exhaustion during sustained forecast generation (no per-tenant rate limiting on simulation endpoint).

---

### 2. **Resilience & Request Shedding** ✅ Advanced

**Strengths:**
- Admission control in middleware (resilience_controller.admit)
- Protected paths: `/api/v1/simulation/simulate`, `/api/v1/auth/login`
- Max inflight: 4096 requests
- Returns 503 with `Retry-After` header when overloaded
- Audit trail on shedding

**Gap on Lines 46-60 (main.py)**: Request shedding works, but no **tenant-scoped backpressure**. A single tenant's forecast job wave can starve others.

**Recommendation**: Implement per-tenant admission quotas:
```python
resilience_controller.admit(
    path=request.url.path,
    tenant_id=request.state.tenant_id,  # NEW
    quota_per_tenant=max(100, settings.resilience_max_inflight_requests // num_active_tenants)
)
```

---

### 3. **Data Validation** ⚠️ Weak at Boundaries

**Current State**:
- Database constraints are strong: `CHECK`, `UNIQUE`, foreign key `RESTRICT` on deletes
- ORM model validation via Pydantic
- No explicit contract validation layer on API ingress

**Risk Example - Simulation Endpoint**:
API accepts `exposed_area_m2` and `corrosion_rate_mm_per_year`. No bounds checking for:
- Impossibly high values (exposed_area > earth surface)
- Physically unrealistic combinations (corrosion_rate 1000x nominal)
- Missing tenant binding verification before write

**Recommendation**: Add a contract validation middleware:

```python
# app/core/validation.py
class SimulationContractValidator:
    MAX_EXPOSED_AREA_M2 = 1_000_000  # Largest bridge: ~250k m²
    MAX_CORROSION_RATE = 10.0  # mm/year (worst case: 5x typical)
    MAX_LIFESPAN_YEARS = 200  # Infrastructure design horizon

    def validate_simulation_input(self, payload: dict, tenant_id: uuid.UUID):
        if payload["exposed_area_m2"] > self.MAX_EXPOSED_AREA_M2:
            raise ValueError(f"Area {payload['exposed_area_m2']} exceeds maximum")
        # ... more validations
```

---

### 4. **Scientific Algorithm Calibration** ⚠️ Requires Field Feedback Loop

**Current State** (backend/app/algorithms/):
- Electrochemistry (Faraday's Law, Nernst equation) ✅ Theoretically sound
- Degradation modeling based on environmental factors
- Lifespan estimation
- Risk classification

**Problem**: Algorithms are "production-structured placeholders" (per README line 329). They output deterministic results but lack:
1. **Calibration baseline** against real-world field data
2. **Accuracy tracking** over time (model drift)
3. **Feedback loop** for continuous improvement

**What's Missing**:
- No A/B testing framework for algorithm changes
- No holdout test set validation in production
- Field validation benchmark exists (`docs/field_validation_benchmark.csv`) but is static

**Recommendation**: Implement a 4-quarter closed-loop system:

```
Q1: Deploy prediction → emit tenant reference ID
Q2: Collect ground truth from field sensors (partnership agreement)
Q3: Compare predictions vs. actual degradation
Q4: Retrain algorithms, A/B test improvements, deploy
```

**Measurement**: Current flow tests exist, but no **accuracy @ field scale** metrics.

---

### 5. **Graceful Degradation Under Cascading Failures** ⚠️ Incomplete

**Current Failure Modes**:

| Failure | Current Behavior | Impact |
|---------|------------------|--------|
| PostgreSQL down | HTTP 500, correlation ID | Prediction unavailable (mission-critical) |
| Redis down | Cache miss, fallback to DB | Acceptable (slower but works) |
| AI copilot unreachable | Request fails | Insights unavailable (nice-to-have) |
| Satellite data provider timeout | Request timeout | Degradation risk silent-fails to conservative estimate |

**Gap**: No **offline prediction mode**. If PostgreSQL is unavailable for 30 seconds during a critical infrastructure assessment, the entire product fails.

**Recommendation**: Implement emergency prediction cache:

```python
# app/core/resilience.py - NEW
class OfflinePredictor:
    """Fall back to pre-computed degradation models when DB offline."""

    def __init__(self, model_dir: str = "artifacts/cached_predictions"):
        # Load 100 most common material/environment pairs
        self.cache = self._load_cache(model_dir)

    async def predict_fallback(self, material_id, env_id):
        key = f"{material_id}_{env_id}"
        if key in self.cache:
            return self.cache[key].with_caveat_marker()  # Mark as offline
        # Else: return extreme conservative estimate
        return ConservativeRiskEstimate(risk_score=95, caveat="offline_fallback")
```

---

### 6. **Multi-Tenant Isolation Boundaries** ✅ Strong, but Untested

**Current State**:
- `tenant_id` on all project, simulation, report records
- Query filters enforce tenant scope (e.g., `project.tenant_id == user.primary_tenant`)
- Tenant membership verified before CRUD

**Gap**: No cryptographic proof of tenant scope in API responses. Tenant IDs are UUIDs (not secrets), but an attacker with UUID enumeration could potentially correlate predictions across tenants.

**Recommendation**: Add tenant scope signature to sensitive payloads:

```python
# Generate HMAC-SHA256 of response payload + tenant_id
response["_integrity_token"] = hmac(
    settings.integrity_key,
    f"{response_id}:{tenant_id}:{utc_now()}",
    hashlib.sha256
).hexdigest()
```

---

### 7. **Disaster Recovery & Backup Restore Testing** ⚠️ Exists, Not Automated

**Current State**:
- Backup drill script: `scripts/backup_restore_drill.py`
- Alembic migration + rollback documented
- PostgreSQL WAL archiving not explicitly configured

**Gap**: Backup restore not tested in CI/CD. Production readiness gate runs many tests but doesn't validate restore in a separate environment.

**Recommendation**: Add daily restore validation:

```python
# scripts/daily_restore_validation.py
async def validate_restore():
    """
    1. Create fresh restore environment
    2. Restore latest backup to it
    3. Run smoke tests
    4. Compare row counts with production
    5. Alert if divergence > threshold
    """
```

---

## Critical Path: 7 Gaps → Actionable Fixes

### Gap 1: Per-Tenant Request Admission ⚠️ HIGH
**Time**: 2 days
**Effort**: Modify resilience_controller to track tenant quotas
**Benefit**: Prevents tenant wave attacks from starving other orgs

### Gap 2: API Contract Validation ⚠️ HIGH
**Time**: 3 days
**Effort**: Add SimulationContractValidator, EnvironmentBoundsValidator
**Benefit**: Catch impossible inputs before they pollute predictions

### Gap 3: Field Calibration Loop ⚠️ CRITICAL
**Time**: 6-8 weeks (requires field partnership)
**Effort**: Build feedback pipeline, A/B test harness, retraining workflow
**Benefit**: Ensures predictions are accurate at real scale

### Gap 4: Offline Prediction Cache ⚠️ HIGH
**Time**: 3 days
**Effort**: Pre-compute common scenarios, fallback handler
**Benefit**: Predictions available even if PostgreSQL is briefly down

### Gap 5: Tenant Scope Cryptographic Proof ⚠️ MEDIUM
**Time**: 1 day
**Effort**: Add HMAC integrity token to responses
**Benefit**: Defense against cross-tenant prediction leakage

### Gap 6: Automated Restore Validation ⚠️ MEDIUM
**Time**: 2 days
**Effort**: Add daily restore smoke test in CI
**Benefit**: Catches backup corruption before it's too late

### Gap 7: Cross-Service Error Propagation ⚠️ MEDIUM
**Time**: 2 days
**Effort**: Add timeout + retry handlers on AI copilot, satellite provider APIs
**Benefit**: Insights don't fail silently; proper degradation signals

---

## Production Readiness Scorecard

| Dimension | Score | Evidence |
|-----------|-------|----------|
| **Observability** | 9/10 | Correlation ID, p99 budgets, Prometheus, Grafana |
| **Resilience** | 8/10 | Request shedding, circuit breaker, connection pool monitoring |
| **Security** | 8/10 | RBAC, OAuth/OTP, audit logging, CSP headers, JWT refresh |
| **Data Integrity** | 8/10 | Check constraints, optimistic locking, foreign keys |
| **Accuracy** | 6/10 | Algorithms sound, but field-calibrated model unknown |
| **Multi-Tenancy** | 8/10 | Tenant isolation strong, missing scope proof |
| **Disaster Recovery** | 7/10 | Backup exists, restore not automated in prod pipeline |
| **API Contracts** | 5/10 | Pydantic models exist, no boundary validation |
| **Graceful Degradation** | 7/10 | Copilot can fail gracefully, offline prediction missing |

**Overall**: **7.4/10** → Production-ready for controlled rollout, gaps above must be closed before mission-critical infrastructure deployments.

---

## Recommended 90-Day Roadmap

### Sprint 1 (Days 1-14): Resilience Hardening
- [ ] Implement per-tenant admission quotas
- [ ] Add offline prediction fallback cache
- [ ] Deploy automated restore validation in CI

### Sprint 2 (Days 15-28): Validation & Observability
- [ ] Add SimulationContractValidator layer
- [ ] Audit all API endpoints for impossible input ranges
- [ ] Add tenant scope HMAC integrity tokens

### Sprint 3 (Days 29-60): Field Calibration
- [ ] Partner with 2-3 infrastructure operators for sensor data
- [ ] Build feedback ingestion pipeline
- [ ] Start A/B testing algorithm improvements

### Sprint 4 (Days 61-90): Cross-Service Hardening
- [ ] Add timeouts + retry handlers for external APIs
- [ ] Implement graceful insights degradation
- [ ] Full disaster recovery simulation in staging

---

## Technical Debt Summary

| Item | Severity | Est. Time |
|------|----------|-----------|
| Field validation feedback loop | CRITICAL | 6-8 weeks |
| Offline prediction mode | HIGH | 3 days |
| Per-tenant admission quotas | HIGH | 2 days |
| API contract validation | HIGH | 3 days |
| Automated restore testing | MEDIUM | 2 days |
| Tenant scope integrity tokens | MEDIUM | 1 day |
| Cross-service error propagation | MEDIUM | 2 days |

---

## References

- Backend README: `backend/README.md` (Production gates, performance SLAs, ops runbooks)
- Database models: `backend/app/database/models.py`
- Main app: `backend/app/main.py` (Middleware, resilience patterns)
- Config: `backend/app/core/config.py` (SLO budgets, admission limits)

---

## Conclusion

**Silent Decay is architecturally sound and operationally mature.** It successfully demonstrates predictive modeling, multi-tenant isolation, audit governance, and resilience patterns. The gaps identified are not fundamental flaws but refinements needed for mission-critical infrastructure work where prediction failures could have real-world consequences.

**Priority**: Close gaps 1, 2, 4 within 60 days before publicly marketing to infrastructure operators. Gap 3 (field calibration) is ongoing and non-blocking for MVP deployment.

**Next Step**: Schedule architecture review with ops/SRE team to evaluate multi-region failover strategy and disaster recovery RTO/RPO targets.
