# Silent Decay: High-Priority Gap Implementation Guide

## Gap 1: Per-Tenant Request Admission Control
**Priority**: HIGH | **Time**: 2 days | **Impact**: Prevents tenant starvation attacks

### Problem
Single tenant's forecast job wave can exhaust admissions, starving other organizations.

### Solution: Tenant-Aware Resilience Controller

**File: `backend/app/core/resilience_tenant.py`** (NEW)

```python
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
import uuid

class TenantAdmissionQuota:
    """Per-tenant request admission quota tracker."""

    def __init__(self, tenant_id: uuid.UUID, max_concurrent: int):
        self.tenant_id = tenant_id
        self.max_concurrent = max_concurrent
        self.inflight_count = 0
        self.last_reset = datetime.utcnow()
        self.rejected_count = 0

    def admit(self) -> tuple[bool, Optional[str]]:
        """Returns (admitted, reason_if_rejected)."""
        if self.inflight_count >= self.max_concurrent:
            self.rejected_count += 1
            return False, f"tenant_quota_exhausted ({self.inflight_count}/{self.max_concurrent})"
        self.inflight_count += 1
        return True, None

    def release(self):
        """Release an admission slot."""
        self.inflight_count = max(0, self.inflight_count - 1)

    def is_severely_throttled(self) -> bool:
        """True if > 80% quota consumed."""
        return self.inflight_count > (self.max_concurrent * 0.8)


class TenantAwareResilienceController:
    """Resilience with per-tenant quotas + global backpressure."""

    GLOBAL_QUOTA = 4096
    BASE_TENANT_QUOTA = 64  # Minimum per active tenant

    def __init__(self):
        self.global_inflight = 0
        self.tenant_quotas: dict[uuid.UUID, TenantAdmissionQuota] = defaultdict()
        self.active_tenants_30m = set()  # Tenants active in last 30 min

    def admit(
        self,
        path: str,
        tenant_id: uuid.UUID,
        protected_paths: list[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if request from tenant should be admitted.

        Checks:
        1. Global overload (> GLOBAL_QUOTA)
        2. Tenant quota (per-tenant fairness)
        3. Protected path (bypass tenant quota for auth/critical paths)
        """
        protected_paths = protected_paths or []
        is_protected = any(path.startswith(p) for p in protected_paths)

        # Check global queue first
        if self.global_inflight >= self.GLOBAL_QUOTA:
            return False, "global_overload"

        # Protected paths bypass tenant quotas but still count globally
        if is_protected:
            self.global_inflight += 1
            return True, None

        # Get or create tenant quota
        if tenant_id not in self.tenant_quotas:
            tenant_quota = self._allocate_quota_for_tenant(tenant_id)
            self.tenant_quotas[tenant_id] = tenant_quota

        quota = self.tenant_quotas[tenant_id]
        admitted, reason = quota.admit()

        if admitted:
            self.global_inflight += 1
            self.active_tenants_30m.add(tenant_id)
            return True, None

        return False, reason

    def release(
        self,
        tenant_id: uuid.UUID,
        path: str,
        status_code: int
    ):
        """Release admission slot after request completes."""
        self.global_inflight = max(0, self.global_inflight - 1)

        # Only tenant-scoped paths consume tenant quota
        protected_paths = ["/api/v1/auth/", "/api/v1/ops/"]
        is_protected = any(path.startswith(p) for p in protected_paths)

        if not is_protected and tenant_id in self.tenant_quotas:
            self.tenant_quotas[tenant_id].release()

    def _allocate_quota_for_tenant(self, tenant_id: uuid.UUID) -> TenantAdmissionQuota:
        """
        Allocate fair quota for new tenant.

        Logic:
        - If <10 active tenants: BASE_TENANT_QUOTA each
        - If >10 active tenants: divide GLOBAL_QUOTA / num_active
        """
        num_active = len([t for t in self.active_tenants_30m if self.tenant_quotas.get(t)])

        if num_active < 10:
            quota = self.BASE_TENANT_QUOTA
        else:
            # Dynamic allocation: ensure all active tenants get min share
            quota = max(self.BASE_TENANT_QUOTA, self.GLOBAL_QUOTA // (num_active + 1))

        return TenantAdmissionQuota(tenant_id, quota)

    def get_metrics(self) -> dict:
        """Observability export."""
        return {
            "global_inflight": self.global_inflight,
            "global_quota": self.GLOBAL_QUOTA,
            "active_tenants": len(self.active_tenants_30m),
            "tenant_quotas": {
                str(tid): {
                    "inflight": quota.inflight_count,
                    "max_concurrent": quota.max_concurrent,
                    "rejected_count": quota.rejected_count,
                    "is_throttled": quota.is_severely_throttled()
                }
                for tid, quota in self.tenant_quotas.items()
            }
        }
```

**File: `backend/app/main.py`** (MODIFY)

```python
# Replace resilience_controller initialization:
from app.core.resilience_tenant import TenantAwareResilienceController

resilience_controller = TenantAwareResilienceController()

# Update middleware:
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    # Extract tenant_id from JWT if present, else use default
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")  # Anonymous
    if hasattr(request.state, "user") and hasattr(request.state.user, "primary_tenant_id"):
        tenant_id = request.state.user.primary_tenant_id

    start_time = time.perf_counter()
    response: Response | None = None
    status_code = 500
    admitted = False

    try:
        admitted, shed_reason = resilience_controller.admit(
            path=request.url.path,
            tenant_id=tenant_id,  # NEW
            protected_paths=["/api/v1/auth/", "/api/v1/ops/"]
        )
        # ... rest of logic unchanged
    finally:
        if admitted:
            resilience_controller.release(
                tenant_id=tenant_id,  # NEW
                path=request.url.path,
                status_code=status_code
            )
        # ... rest unchanged
```

**Metrics Export** (add to `/api/v1/ops/resilience`):
```python
@app.get("/api/v1/ops/resilience")
async def get_resilience_metrics():
    return resilience_controller.get_metrics()
```

---

## Gap 2: API Contract Validation Layer
**Priority**: HIGH | **Time**: 3 days | **Impact**: Prevents impossible predictions from poisoning model

### Problem
API accepts values that violate physical laws (area > Earth, corrosion rate 1000x nominal). These outliers can skew model calibration.

### Solution: Boundary Validation Middleware

**File: `backend/app/core/validation.py`** (NEW)

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import uuid

class SimulationContractValidator:
    """
    Validate simulation inputs against physical/operational boundaries.

    Thresholds based on infrastructure domain knowledge:
    - Area: Largest bridge span ~250k m²
    - Corrosion rate: Atmospheric max ~1.0 mm/yr, immersed ~5.0 mm/yr
    - Lifespan: Infrastructure design horizon ~200 years
    """

    # Physical boundaries
    MAX_EXPOSED_AREA_M2 = 1_000_000  # Conservative for any structure
    MIN_EXPOSED_AREA_M2 = 0.01      # mm²+

    MAX_CORROSION_RATE = 10.0       # 10x worst-case immersed
    MIN_CORROSION_RATE = 0.0

    MAX_LIFESPAN_YEARS = 200
    MIN_LIFESPAN_YEARS = 0.1

    MAX_EXPOSURE_TIME_HOURS = 100_000  # ~11 years continuous
    MIN_EXPOSURE_TIME_HOURS = 1

    def validate(self, data: dict, material_id: uuid.UUID, env_id: uuid.UUID) -> list[str]:
        """
        Validate simulation input.

        Returns: list of validation warnings/errors.
        If >2 violations: recommend manual review before insert.
        """
        violations = []

        # Area checks
        area = data.get("exposed_area_m2", 0)
        if area > self.MAX_EXPOSED_AREA_M2:
            violations.append(
                f"Area {area}m² exceeds infrastructure maximum {self.MAX_EXPOSED_AREA_M2}m²"
            )
        if area < self.MIN_EXPOSED_AREA_M2:
            violations.append(
                f"Area {area}m² below minimum measurable {self.MIN_EXPOSED_AREA_M2}m²"
            )

        # Corrosion rate checks
        rate = data.get("corrosion_rate_mm_per_year", 0)
        if rate > self.MAX_CORROSION_RATE:
            violations.append(
                f"Corrosion rate {rate}mm/yr exceeds worst-case {self.MAX_CORROSION_RATE}mm/yr; "
                "check material/environment combination"
            )

        # Lifespan checks
        lifespan = data.get("estimated_lifespan_years", 0)
        if lifespan > self.MAX_LIFESPAN_YEARS:
            violations.append(
                f"Lifespan {lifespan}yr exceeds design horizon {self.MAX_LIFESPAN_YEARS}yr"
            )

        # Exposure time sanity
        exposure = data.get("exposure_time_hours", 0)
        if exposure > self.MAX_EXPOSURE_TIME_HOURS:
            violations.append(
                f"Exposure {exposure}hr exceeds ~11 years; verify timestamp"
            )

        # Physical consistency: rate * time should correlate with area loss
        # This is a heuristic: if rate is high but time is 1 hour, warn
        if rate > 5.0 and exposure < 168:  # 1 week
            violations.append(
                f"High rate ({rate}mm/yr) with short exposure ({exposure}hr); "
                "consider accelerated test scenario"
            )

        return violations


class EnvironmentContractValidator:
    """Validate environment profile inputs."""

    def validate(self, data: dict) -> list[str]:
        """Returns validation warnings."""
        violations = []

        # Temperature bounds (Kelvin equivalent: -50°C to 80°C typical for infrastructure)
        temp = data.get("temperature_c", 0)
        if temp < -50 or temp > 80:
            violations.append(
                f"Temperature {temp}°C outside typical infrastructure range [-50°C, 80°C]"
            )

        # Humidity must be 0-100%
        rh = data.get("relative_humidity_pct", 0)
        if rh < 0 or rh > 100:
            violations.append(f"Humidity {rh}% invalid (must be 0-100)")

        # if humidity > 80% AND temp > 15°C: high corrosion risk (expected, not error)

        # pH must be 0-14
        ph = data.get("ph", 0)
        if ph < 0 or ph > 14:
            violations.append(f"pH {ph} invalid (must be 0-14)")

        # Chloride (marine environment indicator)
        chloride = data.get("chloride_ppm", 0)
        if chloride > 35000:  # Seawater is ~35000 ppm
            violations.append(
                f"Chloride {chloride}ppm exceeds seawater concentration"
            )

        return violations


# Integration: ValidationError exception
class ValidationWarningsException(Exception):
    """Raised when validation warnings exceed threshold."""
    def __init__(self, warnings: list[str], threshold: int = 2):
        self.warnings = warnings
        self.threshold = threshold
        super().__init__(
            f"{len(warnings)} validation issues (threshold: {threshold})"
        )
```

**File: `backend/app/api/simulation_routes.py`** (MODIFY)

```python
from app.core.validation import SimulationContractValidator, ValidationWarningsException
from fastapi import HTTPException

validator = SimulationContractValidator()

@router.post("/api/v1/simulation", response_model=SimulationResponse)
async def create_simulation(
    payload: SimulationRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    # NEW: Validate contract
    warnings = validator.validate(
        {
            "exposed_area_m2": payload.exposed_area_m2,
            "corrosion_rate_mm_per_year": payload.corrosion_rate_mm_per_year,
            "estimated_lifespan_years": payload.estimated_lifespan_years,
            "exposure_time_hours": payload.exposure_time_hours,
        },
        material_id=payload.material_id,
        env_id=payload.environment_id
    )

    # If >2 warnings: require explicit override flag
    if len(warnings) > 2 and not payload.override_validation_warnings:
        logger.warning(
            "Validation warnings on simulation input",
            extra={"warnings": warnings, "user_id": current_user.id}
        )
        raise HTTPException(
            status_code=422,
            detail={
                "validation_warnings": warnings,
                "message": "Input violates physical boundaries. Set override_validation_warnings=true to proceed.",
            }
        )

    # Log warnings for later analysis
    if warnings:
        logger.info(
            "Simulation created with validation warnings",
            extra={"warnings": warnings, "simulation_id": str(sim_id)}
        )

    # ... rest of creation logic unchanged
```

---

## Gap 4: Offline Prediction Fallback Cache
**Priority**: HIGH | **Time**: 3 days | **Impact**: Predictions available during brief DB outages

### Problem
If PostgreSQL is unavailable, entire prediction service fails. Infrastructure operators may need urgent risk assessments in degraded conditions.

### Solution: Pre-Computed Fallback Cache

**File: `backend/app/core/offline_predictor.py`** (NEW)

```python
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import uuid

@dataclass
class OfflinePrediction:
    """Prediction from offline cache with caveat marker."""
    risk_score: float
    corrosion_rate_mm_per_year: float
    estimated_lifespan_years: float
    risk_classification: str
    is_offline_fallback: bool = True
    caveat: str = "Offline fallback: predictions frozen at last DB sync. Verify with live system when available."


class OfflinePredictor:
    """
    Provides fallback predictions when PostgreSQL is unavailable.

    Cache is pre-computed and refreshed daily from 100 most-common
    material/environment combinations.
    """

    CACHE_DIR = Path("artifacts/offline_predictions")
    CACHE_FILE = CACHE_DIR / "fallback_cache.json"

    def __init__(self):
        self.cache: dict[str, dict] = {}
        self.loaded_at: Optional[float] = None
        self._load_cache()

    def _load_cache(self):
        """Load pre-computed predictions from disk."""
        if not self.CACHE_FILE.exists():
            logger.warning(f"Offline cache not found at {self.CACHE_FILE}")
            return

        try:
            with open(self.CACHE_FILE) as f:
                self.cache = json.load(f)
            self.loaded_at = os.path.getmtime(self.CACHE_FILE)
            logger.info(
                "Offline prediction cache loaded",
                extra={"entries": len(self.cache)}
            )
        except Exception as e:
            logger.error(f"Failed to load offline cache: {e}")
            self.cache = {}

    def predict(
        self,
        material_id: uuid.UUID,
        environment_id: uuid.UUID
    ) -> Optional[OfflinePrediction]:
        """
        Return cached prediction if available.
        Returns None if not in cache (caller should raise "unavailable" error).
        """
        key = f"{material_id}_{environment_id}"

        if key not in self.cache:
            return None

        pred_dict = self.cache[key]
        return OfflinePrediction(
            risk_score=pred_dict["risk_score"],
            corrosion_rate_mm_per_year=pred_dict["corrosion_rate_mm_per_year"],
            estimated_lifespan_years=pred_dict["estimated_lifespan_years"],
            risk_classification=pred_dict["risk_classification"],
            is_offline_fallback=True,
            caveat=f"Offline fallback (cached {self.loaded_at}). Live predictions unavailable."
        )

    def predict_conservative(self) -> OfflinePrediction:
        """
        When neither cache nor live DB available: return extreme conservative estimate.

        This forces users to view risk profile as "CRITICAL" until system recovers.
        """
        return OfflinePrediction(
            risk_score=95,
            corrosion_rate_mm_per_year=5.0,
            estimated_lifespan_years=5.0,
            risk_classification="CRITICAL",
            is_offline_fallback=True,
            caveat="SYSTEM OFFLINE: Conservative estimate only. Do not rely for critical infrastructure decisions."
        )


# Usage in simulation service:
# backend/app/services/simulation_record_service.py

async def get_or_predict_simulation(
    simulation_id: uuid.UUID,
    session: AsyncSession
) -> SimulationResponse:
    """Get simulation, with fallback to offline predictor if DB unavailable."""
    try:
        sim = await SimulationRepository.get_by_id(simulation_id, session)
        return sim
    except ConnectionError as e:
        logger.warning(
            f"DB connection lost; attempting offline fallback",
            extra={"simulation_id": simulation_id, "error": str(e)}
        )

        offline_pred = offline_predictor.predict(
            material_id=sim.material_id,  # From request state
            environment_id=sim.environment_id
        )

        if offline_pred:
            return SimulationResponse(
                **offline_pred,
                source="offline_fallback",
                original_simulation_id=simulation_id
            )

        # No cache entry: return extreme conservative
        return SimulationResponse(
            **offline_predictor.predict_conservative(),
            source="offline_conservative_fallback",
            original_simulation_id=simulation_id
        )
```

**Daily Cache Refresh Script** (`scripts/refresh_offline_predictions.py`):

```python
"""
Refresh offline prediction cache daily.
Run via cron: 0 3 * * * (3am UTC)
"""

async def refresh_offline_cache():
    """
    1. Query top 100 material/environment combinations by usage
    2. Run predictions for each
    3. Serialize to JSON
    4. Backup previous version
    """
    async with get_db_session() as session:
        # Find 100 most common combos
        top_combos = await session.execute(
            """
            SELECT material_id, environment_id, COUNT(*) as freq
            FROM simulation
            GROUP BY material_id, environment_id
            ORDER BY freq DESC
            LIMIT 100
            """
        )

        cache = {}
        for material_id, env_id, freq in top_combos:
            try:
                pred = await predict_simulation(
                    material_id=material_id,
                    environment_id=env_id
                )
                key = f"{material_id}_{env_id}"
                cache[key] = {
                    "risk_score": pred.risk_score,
                    "corrosion_rate_mm_per_year": pred.corrosion_rate_mm_per_year,
                    "estimated_lifespan_years": pred.estimated_lifespan_years,
                    "risk_classification": pred.risk_classification,
                    "frequency": freq,
                }
            except Exception as e:
                logger.error(f"Failed to predict {material_id}/{env_id}: {e}")

        # Write cache
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)

        logger.info(
            "Offline prediction cache refreshed",
            extra={"entries": len(cache)}
        )
```

---

## Summary: 3-Day Implementation Plan

| Day | Gap | Deliverable |
|-----|-----|-------------|
| 1 | Per-tenant admission | TenantAwareResilienceController + middleware update |
| 2 | API validation | SimulationContractValidator + EnvironmentValidator |
| 3 | Offline predictor | OfflinePredictor + daily refresh script |

**Testing**:
- Unit: Validator boundaries, quota allocation math
- Integration: Tenant starvation scenarios, fallback activation
- Load: Verify p99 latency unchanged with validators

**Metrics to Export**:
- `resilience_tenant_quota_rejections_total` (Prometheus)
- `validation_warnings_total` (by field)
- `offline_predictor_activations_total`

---

## References
- Main app: `backend/app/main.py`
- Config: `backend/app/core/config.py`
- Simulation routes: `backend/app/api/simulation_routes.py` (find pattern to extend)
- Testing pattern: `backend/tests/integration/test_api_crud.py`
