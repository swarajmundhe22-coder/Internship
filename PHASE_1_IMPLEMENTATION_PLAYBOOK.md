# SILENT DECAY: PHASE 1 IMPLEMENTATION PLAYBOOK
## Critical Security & Stability Fixes (Days 1-5)

**Target**: Eliminate production-blocking issues before any deployment

---

## DAY 1: CREDENTIAL ROTATION & REMOVAL

### Task 1.1: Audit Exposed Credentials

```bash
# Find all exposed secrets in git history
cd backend
git log --all --pretty=format: --diff-filter=d --summary | grep delete | awk '{print $4}' | xargs git log -S | grep -E "(password|secret|api_key|credential)"

# Display current .env exposure
cat .env | grep -E "(KEY|PASSWORD|SECRET)"
```

**Output Expected**:
```
NVIDIA_API_KEY=nvapi-...
SMTP_PASSWORD=...
OAUTH_GOOGLE_CLIENT_SECRET=...
JWT_SECRET_KEY=change-me-in-production
PAYPAL_WEBHOOK_SECRET=...
```

**Risk Assessment**:
| Credential | Blast Radius | Action |
|------------|--------------|--------|
| NVIDIA_API_KEY | Compute charges, prompt injection | Revoke immediately, generate new |
| GOOGLE_CLIENT_SECRET | OpenID token forgery | Rotate in GCP console |
| SMTP_PASSWORD | Email spoofing | Reset in email provider |
| JWT_SECRET_KEY | Session hijacking | Generate new secret |
| PAYPAL_WEBHOOK_SECRET | Billing fraud | Rotate in PayPal |

---

### Task 1.2: Generate New Credentials

**NVIDIA API Key**:
```bash
# 1. Login to NVIDIA API console: https://api.nvidia.com/
# 2. Revoke old key
# 3. Generate new API key
# 4. Store in secure vault (1Password, Vault Conductor, etc.)
NEW_NVIDIA_KEY="nvapi-<new-key>"
```

**Google OAuth**:
```bash
# 1. Go to https://console.cloud.google.com/
# 2. Project: "The On Lookers"
# 3. APIs & Services > Credentials
# 4. Delete old OAuth 2.0 Client ID
# 5. Create new OAuth 2.0 Client ID
# 6. Download new credentials
NEW_GOOGLE_SECRET="GOCSPX-<new-secret>"
GOOGLE_CLIENT_ID="<new-client-id>.apps.googleusercontent.com"
```

**SMTP Password**:
```bash
# For Gmail: Generate new app password
# 1. Go to https://myaccount.google.com/security
# 2. App passwords > Create (Select Mail + Windows/Linux)
# 3. Copy new password
NEW_SMTP_PASSWORD="<app-password>"
```

**JWT Secret**:
```bash
# Generate cryptographically secure random string (32+ bytes)
python3 << 'EOF'
import secrets
jwt_secret = secrets.token_urlsafe(32)  # 256-bit
print(f"JWT_SECRET_KEY={jwt_secret}")
EOF
```

**PayPal Webhook Secret**:
```bash
# In PayPal sandbox/production account
# 1. Go to Apps & Credentials
# 2. Create new webhook signing certificate
# 3. Copy webhook secret
NEW_PAYPAL_SECRET="<new-webhook-secret>"
```

---

### Task 1.3: Remove Secrets from Git History

```bash
# Install BFG (Faster than git-filter-branch)
brew install bfg  # macOS
# OR: apt-get install bfg  # Linux
# OR: Download from https://rclone.org/install/

# Create secrets file listing patterns to remove
cat > /tmp/secrets.txt << 'EOF'
.*API_KEY.*
.*PASSWORD.*
.*SECRET.*
.*CREDENTIAL.*
EOF

# Remove from entire git history
bfg --strip-blobs-bigger-than 1M /path/to/repo
bfg --delete-files .env
bfg --replace-text /tmp/secrets.txt /path/to/repo

# Force push to origin (review before pushing!)
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force-with-lease  # REQUIRES REVIEW
```

**⚠️ WARNING**: Force pushing rewrites history. 
- Notify all developers to re-clone repository
- Verify backup of old history before deletion
- Document in change log: "Security: Removed exposed credentials from git"

---

### Task 1.4: Update Configuration

**File: `backend/.env`** (Template Only)
```bash
# DO NOT COMMIT ACTUAL SECRETS
# Use environment variables in production

ENVIRONMENT=development

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://onlooker:onlooker@localhost:5432/onlooker

# External APIs (populate from secure vault, never hardcode)
NVIDIA_API_KEY=${NVIDIA_API_KEY}  # Load from env var
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
SMTP_PASSWORD=${SMTP_PASSWORD}
PAYPAL_WEBHOOK_SECRET=${PAYPAL_WEBHOOK_SECRET}

# Generated secrets (must be set in production)
JWT_SECRET_KEY=${JWT_SECRET_KEY}  # Min 32 bytes

# Other configs (safe to commit)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM_EMAIL=alerts@silentdecay.io
```

**File: `backend/.gitignore`** (ADD)
```
.env
.env.local
.env.*.local
# Anything with secrets
**/secrets/
**/credentials/
**/*.key
**/*.pem
```

**File: `frontend/.env.example`** (SANITIZE)
```bash
# Remove actual Firebase config, use placeholders
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
# Don't include actual deployed credentials
```

---

### Task 1.5: Deploy to Staging

```bash
# Set environment variables (using secure vault)
export ENVIRONMENT=development
export JWT_SECRET_KEY=$(openssl rand -base64 32)
export NVIDIA_API_KEY=$(vault kv get secret/nvidia_api_key)
export GOOGLE_CLIENT_SECRET=$(vault kv get secret/google_oauth)
# ... etc

# Run backend with new credentials
python -m uvicorn app.main:app --reload

# Verify it starts without errors
curl http://localhost:8000/api/v1/health
# Expected: {"service": "...", "status": "running"}

# Test with old credentials (should fail)
export OLD_JWT_SECRET="change-me-in-production"
# Should get 401 Unauthorized
```

**Time Estimate**: 3-4 hours

---

## DAY 2: CIRCUIT BREAKER IMPLEMENTATION

### Task 2.1: Implement Circuit Breaker Pattern

**File: `backend/app/core/circuit_breaker.py`** (NEW)

```python
import asyncio
import time
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, TypeVar, Any, Optional
import logging

logger = logging.getLogger("gifip.circuit_breaker")

T = TypeVar('T')

class CircuitState(Enum):
    CLOSED = "closed"          # Normal operation, requests pass through
    OPEN = "open"              # Failures detected, requests blocked
    HALF_OPEN = "half_open"    # Testing if service recovered

@dataclass
class CircuitBreakerMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: Optional[datetime] = None
    failure_count: int = 0
    state_transitions: list[tuple[datetime, CircuitState]] = None

    def __post_init__(self):
        if self.state_transitions is None:
            self.state_transitions = []

class CircuitBreaker:
    """
    Circuit breaker pattern for resilient external API calls.
    
    States:
    - CLOSED: Normal, requests pass through, failures recorded
    - OPEN: Threshold exceeded, requests blocked with CircuitBreakerOpen exception
    - HALF_OPEN: Testing recovery, limited requests allowed
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        expected_exception: type = Exception,
        half_open_max_requests: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.expected_exception = expected_exception
        self.half_open_max_requests = half_open_max_requests
        
        self.metrics = CircuitBreakerMetrics()
        self.half_open_requests = 0

    async def call(
        self, 
        func: Callable[..., T], 
        *args, 
        **kwargs
    ) -> T:
        """Execute function through circuit breaker."""
        self.metrics.total_requests += 1

        # Check if should attempt recovery
        if self.metrics.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._transition_to(CircuitState.HALF_OPEN)
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN. Retry after "
                    f"{self.recovery_timeout_seconds}s"
                )

        # In HALF_OPEN state, limit concurrent requests
        if self.metrics.state == CircuitState.HALF_OPEN:
            if self.half_open_requests >= self.half_open_max_requests:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' HALF_OPEN, max requests exceeded"
                )
            self.half_open_requests += 1

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as exc:
            self._on_failure(exc)
            raise

    def _on_success(self):
        """Handle successful request."""
        self.metrics.successful_requests += 1
        
        # Reset state on success
        if self.metrics.state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker '{self.name}' recovered, transitioning to CLOSED")
            self._transition_to(CircuitState.CLOSED)
        
        self.metrics.failure_count = 0
        self.half_open_requests = 0

    def _on_failure(self, exc: Exception):
        """Handle failed request."""
        self.metrics.failed_requests += 1
        self.metrics.failure_count += 1
        self.metrics.last_failure_time = datetime.utcnow()

        logger.warning(
            f"Circuit breaker '{self.name}' failure",
            extra={
                "error": str(exc),
                "failure_count": self.metrics.failure_count,
                "threshold": self.failure_threshold,
            }
        )

        # Transition to OPEN if threshold exceeded
        if self.metrics.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker '{self.name}' opening",
                extra={
                    "failure_count": self.metrics.failure_count,
                    "threshold": self.failure_threshold,
                }
            )
            self._transition_to(CircuitState.OPEN)

    def _should_attempt_recovery(self) -> bool:
        """Check if recovery timeout has elapsed."""
        if self.metrics.last_failure_time is None:
            return False
        
        elapsed = (datetime.utcnow() - self.metrics.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout_seconds

    def _transition_to(self, new_state: CircuitState):
        """Record state transition."""
        old_state = self.metrics.state
        self.metrics.state = new_state
        self.metrics.state_transitions.append((datetime.utcnow(), new_state))
        
        logger.info(
            f"Circuit breaker '{self.name}' state transition",
            extra={"from": old_state.value, "to": new_state.value}
        )

    def get_metrics(self) -> dict:
        """Export metrics for monitoring."""
        return {
            "name": self.name,
            "state": self.metrics.state.value,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "failure_count": self.metrics.failure_count,
            "failure_rate": (
                self.metrics.failed_requests / self.metrics.total_requests
                if self.metrics.total_requests > 0
                else 0
            ),
            "last_failure_time": self.metrics.last_failure_time.isoformat() 
                if self.metrics.last_failure_time else None,
        }

class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open."""
    pass
```

---

### Task 2.2: Integrate with Services

**File: `backend/app/services/copilot_service.py`** (UPDATE)

```python
# ADD: Import circuit breaker
from app.core.circuit_breaker import CircuitBreaker

# Create breaker instance (module level)
nvidia_circuit_breaker = CircuitBreaker(
    name="nvidia_copilot_api",
    failure_threshold=5,           # Open after 5 failures
    recovery_timeout_seconds=60,   # Retry after 60s
    expected_exception=Exception,  # Catch all exceptions
)

class CopilotService:
    async def query(
        self, 
        user_input: str, 
        model: str = "nvidia/llama-3.1-nemotron-ultra"
    ) -> tuple[str, str]:
        """
        Query NVIDIA copilot through circuit breaker.
        
        Returns:
            (response_text, source)  # source: "nvidia" or "fallback"
        """
        try:
            # Route through circuit breaker
            response = await nvidia_circuit_breaker.call(
                self._call_nvidia_api_internal,
                user_input=user_input,
                model=model
            )
            return response, "nvidia"
        
        except CircuitBreakerOpenException:
            # Circuit is open, return cached response
            logger.warning("NVIDIA copilot circuit breaker OPEN, using cached response")
            return CACHED_FALLBACK_RESPONSE, "circuit_breaker_open"
        
        except Exception as exc:
            # Other failures, return fallback
            logger.error(f"NVIDIA copilot failed: {exc}")
            return DEFAULT_COPILOT_RESPONSE, "fallback"

    async def _call_nvidia_api_internal(
        self, 
        user_input: str, 
        model: str
    ) -> tuple[str, str]:
        """Internal API call (gets wrapped by circuit breaker)."""
        response = await self.client.post(
            url=self.settings.nvidia_api_url,
            headers={
                "Authorization": f"Bearer {self.settings.nvidia_api_key}"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": user_input}],
            },
            timeout=10.0,  # Explicit timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"NVIDIA API returned {response.status_code}")
        
        return response.json()["choices"][0]["message"]["content"], "nvidia"

# Expose metrics endpoint
@router.get("/api/v1/ops/circuit-breakers")
async def get_circuit_breaker_metrics():
    """Return metrics for all circuit breakers."""
    return {
        "circuit_breakers": {
            "nvidia_copilot": nvidia_circuit_breaker.get_metrics(),
            "satellite_provider": satellite_breaker.get_metrics(),  # Add satellite too
        }
    }
```

**File: `backend/app/services/satellite_provider_client_service.py`** (UPDATE)

```python
from app.core.circuit_breaker import CircuitBreaker

satellite_breaker = CircuitBreaker(
    name="satellite_provider_api",
    failure_threshold=3,
    recovery_timeout_seconds=120,
)

async def fetch_degradation_data(material_id, env_id):
    """Fetch satellite data through circuit breaker."""
    try:
        return await satellite_breaker.call(
            self._fetch_satellite_internal,
            material_id=material_id,
            env_id=env_id
        )
    except CircuitBreakerOpenException:
        logger.warning("Satellite provider circuit breaker OPEN")
        return {
            "status": "unavailable",
            "caveat": "Satellite data unavailable, using cached predictions",
        }
    except Exception as exc:
        logger.error(f"Satellite provider error: {exc}")
        return {
            "status": "error",
            "caveat": "Could not retrieve satellite data",
        }
```

---

### Task 2.3: Test Circuit Breaker

**File: `backend/tests/unit/test_circuit_breaker.py`** (NEW)

```python
import pytest
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException, CircuitState

@pytest.mark.asyncio
async def test_circuit_breaker_passes_successful_calls():
    """Verify circuit breaker allows successful calls."""
    async def success_func():
        return "success"
    
    breaker = CircuitBreaker(name="test", failure_threshold=3)
    result = await breaker.call(success_func)
    
    assert result == "success"
    assert breaker.metrics.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    """Verify circuit breaker opens after failure threshold."""
    async def fail_func():
        raise Exception("API down")
    
    breaker = CircuitBreaker(name="test", failure_threshold=3)
    
    # First 3 calls fail
    for i in range(3):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    assert breaker.metrics.state == CircuitState.OPEN
    
    # 4th call blocked by circuit breaker
    with pytest.raises(CircuitBreakerOpenException):
        await breaker.call(fail_func)

@pytest.mark.asyncio
async def test_circuit_breaker_recovers():
    """Verify circuit breaker recovers after timeout."""
    call_count = 0
    
    async def sometimes_fails():
        nonlocal call_count
        call_count += 1
        if call_count <= 3:
            raise Exception("Fail")
        return "success"
    
    breaker = CircuitBreaker(
        name="test",
        failure_threshold=3,
        recovery_timeout_seconds=0.1,  # Fast recovery for test
    )
    
    # Open breaker
    for _ in range(3):
        with pytest.raises(Exception):
            await breaker.call(sometimes_fails)
    assert breaker.metrics.state == CircuitState.OPEN
    
    # Wait for recovery
    await asyncio.sleep(0.2)
    
    # Try again - should transition to HALF_OPEN
    result = await breaker.call(sometimes_fails)
    assert result == "success"
    assert breaker.metrics.state == CircuitState.CLOSED
```

**Time Estimate**: 4 hours (implementation + testing)

---

## DAY 3: INPUT VALIDATION & ERROR HANDLING

### Task 3.1: Add Pydantic Response Validators

**File: `backend/app/core/api_validators.py`** (NEW)

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Any

class SatelliteProviderResponse(BaseModel):
    """Validate and normalize satellite provider API response."""
    degradation_rate: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    timestamp: datetime
    environmental_factors: dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = None
    caveat: Optional[str] = None

    @validator('degradation_rate')
    def check_realistic_degradation(cls, v):
        """Alert on physically unrealistic values."""
        if v > 50:
            logger.warning(f"Unusual degradation rate: {v}")
        return v

class NvidiaApiResponse(BaseModel):
    """Validate NVIDIA copilot API response."""
    choices: list[dict] = Field(...)
    model: str
    usage: dict = Field(default_factory=dict)

    @validator('choices')
    def validate_choices(cls, v):
        if not v or not isinstance(v[0].get('message'), dict):
            raise ValueError("Invalid choices format")
        return v
```

**File: `backend/app/services/satellite_provider_client_service.py`** (UPDATE)

```python
from app.core.api_validators import SatelliteProviderResponse

async def _fetch_satellite_internal(self, material_id, env_id):
    """Fetch and validate satellite response."""
    response = await self.client.request(...)
    
    # Parse and validate response
    try:
        validated = SatelliteProviderResponse(**response.json())
        return {
            "status": "ok",
            "degradation_rate": validated.degradation_rate,
            "confidence": validated.confidence,
        }
    except ValueError as exc:
        logger.error(f"Satellite response validation failed: {exc}")
        raise  # Circuit breaker will handle
```

**Time Estimate**: 2 hours

---

## DAY 4: DATABASE CONNECTION LIFECYCLE

### Task 4.1: Add Engine Shutdown

**File: `backend/app/main.py`** (UPDATE)

```python
from app.database.session import engine

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Gracefully shut down all services."""
    logger.info("Shutting down application")
    
    # Stop audit batch processor
    await audit_batch_processor.stop()
    
    # NEW: Dispose of database engine
    await engine.dispose()
    
    logger.info("Application shutdown complete")
```

**File: `backend/app/database/session.py`** (ADD)

```python
# Add helper for disposal
async def close_engine():
    """Close all database connections."""
    await engine.dispose()
```

**Testing**:
```bash
# Start server
python -m uvicorn app.main:app

# In another terminal, send shutdown signal
kill -TERM <pid>

# Verify no hanging connections
lsof -i :8000  # Should show no connections after 5 seconds
```

**Time Estimate**: 1 hour

---

## DAY 5: AUTHORIZATION ENFORCEMENT & INTEGRATION TESTING

### Task 5.1: Audit Authorization

```bash
# Find all API endpoints
grep -r "@router\." backend/app/api/ | grep "def " | wc -l
# Expected: 50+ endpoints

# Count endpoints with auth checks
grep -r "Depends(get_current_user)" backend/app/api/ | grep "def " | wc -l
# Current: maybe 30

# Missing auth: 50 - 30 = 20 endpoints need fixing
```

### Task 5.2: Add Missing Auth Checks

**File: `backend/app/api/demo_routes.py`** (UPDATE - ADD AUTH)

```python
from fastapi import Depends
from app.services.auth_service import get_current_user
from app.database.models import UserModel

@router.get("/api/v1/demo/simulations")
async def get_demo_simulations(
    current_user: UserModel = Depends(get_current_user),  # ADD THIS
):
    """Get demo simulations (auth required)."""
    # ...
```

**Run validation**:
```bash
# Script to check all endpoints
python scripts/audit_authorization.py

# Expected output:
# ✓ /api/v1/simulation - requires auth
# ✓ /api/v1/projects - requires auth
# ✗ /api/v1/demo - MISSING AUTH CHECK
```

### Task 5.3: Integration Test Phase 1 Fixes

**File: `backend/tests/integration/test_phase1_security_hardening.py`** (NEW)

```python
async def test_exposed_credentials_removed_from_git():
    """Verify no credentials in git history."""
    result = subprocess.run(
        ["git", "log", "-p", "--all", "-S", "change-me-in-production"],
        capture_output=True,
        cwd="."
    )
    assert result.stdout == b"", "Found hardcoded secrets in git history"

async def test_circuit_breaker_blocks_failed_calls(client):
    """Verify circuit breaker protects against cascade failures."""
    # Simulate NVIDIA API down
    with monkeypatch.setattr("aiohttp.ClientSession.post", fail_fixture):
        response = client.post("/api/v1/copilot/query", json={...})
        # Should get graceful fallback, not 500 error
        assert response.status_code == 200
        assert response.json()["source"] != "nvidia"  # Using fallback

async def test_all_protected_endpoints_require_auth(client):
    """Verify auth enforcement."""
    protected_paths = [
        "/api/v1/simulation",
        "/api/v1/projects",
        "/api/v1/reports",
        "/api/v1/predictions",
    ]
    
    for path in protected_paths:
        # Request without token should fail
        response = client.get(path)
        assert response.status_code == 401

async def test_input_validation_rejects_invalid_responses(client):
    """Verify satellite response validation."""
    # Mock satellite provider with bad response
    bad_response = {"degradation_rate": -100}  # Invalid
    
    with monkeypatch.setattr("satellite_client.request", return_value=bad_response):
        response = client.post("/api/v1/simulation", json={...})
        # Should validate and reject
        assert response.status_code == 422
```

**Time Estimate**: 2 days (writing and running comprehensive tests)

---

## PHASE 1 COMPLETION CHECKLIST

```
DONE Daily:
✅ 1.1 Found all exposed credentials
✅ 1.2 Generated new API keys (all services rotated)
✅ 1.3 Removed secrets from git history
✅ 1.4 Updated .env template and .gitignore
✅ 1.5 Deployed to staging with new credentials

DONE Daily 2:
✅ 2.1 Implemented CircuitBreaker class
✅ 2.2 Integrated with copilot and satellite services
✅ 2.3 Unit tests for circuit breaker logic

DONE Daily 3:
✅ 3.1 Added Pydantic validators for external API responses

DONE Daily 4:
✅ 4.1 Added engine.dispose() to shutdown

DONE Daily 5:
✅ 5.1 Audited all endpoints for auth
✅ 5.2 Added missing auth decorators
✅ 5.3 Integration tests for Phase 1 fixes
```

---

## PHASE 1 EXIT CRITERIA

| Criterion | Verification |
|-----------|--------------|
| No secrets in git | `git log -p -S "API_KEY" --all` returns no matches |
| Circuit breaker working | Circuit blocks requests when external API fails |
| Auth enforced| All protected endpoints return 401 without token |
| Input validation | Invalid API responses rejected with 422 |
| Engine disposal | No hanging connections after shutdown |
| Tests pass | `pytest tests/ -v` = 100% pass |

---

## PHASE 1 RISKS & MITIGATION

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| New credentials not deployed consistently | Medium | High | Use infrastructure as code (Terraform secrets) |
| Force push breaks developer workflow | High | Medium | Communicate clearly, provide re-clone instructions |
| Circuit breaker timeouts too aggressive | Medium | Low | Configure recovery_timeout_seconds = 60 (adjustable) |
| Auth enforcement breaks existing integrations | Low | High | Grandfathered in old API keys (deprecated path) |

---

## SIGN-OFF

**Phase 1 Owner**: [Backend Lead]
**Security Review**: [Security Lead]
**Date Started**: 2026-04-10
**Target Completion**: 2026-04-14

After Phase 1 completion, conduct security audit before proceeding to Phase 2 (test coverage).
