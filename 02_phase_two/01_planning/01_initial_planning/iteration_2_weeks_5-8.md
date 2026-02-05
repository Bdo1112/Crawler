# Iteration Plan 2: Weeks 5-8 (Multi-Tenancy & Anti-Detection)

**Project:** Crawlee Migration - Multi-Tenant Web Scraping Platform
**Timeline:** Weeks 5-8 (4 weeks total)
**Team Size:** 1-3 developers
**Date:** 2026-02-02
**Prepared By:** Technical Product Manager #2

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Prerequisites & Integration Points](#prerequisites--integration-points)
3. [Iteration 3: Multi-Tenancy (Weeks 5-6)](#iteration-3-multi-tenancy-weeks-5-6)
4. [Iteration 4: Anti-Detection (Weeks 7-8)](#iteration-4-anti-detection-weeks-7-8)
5. [Database Evolution Strategy](#database-evolution-strategy)
6. [Cross-Cutting Concerns](#cross-cutting-concerns)
7. [Success Metrics Dashboard](#success-metrics-dashboard)
8. [Appendices](#appendices)

---

## Executive Summary

### What We're Building

These two iterations transform the single-tenant scraping API (built in Weeks 3-4) into a production-ready, multi-tenant platform with advanced anti-detection capabilities.

**Iteration 3 (Weeks 5-6):** Multi-Tenancy Foundation
- Secure tenant isolation using PostgreSQL Row-Level Security (RLS)
- Rate limiting with Redis-based sliding window algorithm
- Quota management and usage tracking for billing
- S3 storage with tenant-isolated bucket structure
- Per-tenant configuration and API key management

**Iteration 4 (Weeks 7-8):** Anti-Detection Layer
- Port 3-layer escalation strategy from `scraper.py`
- Integrate curl_cffi for TLS fingerprinting (Layer 1)
- BrightData residential proxy rotation (Layer 2-4)
- FlareSolverr microservice for Cloudflare challenges (Layer 5)
- Intelligent routing based on site profiles and challenge detection

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Tenant Isolation** | PostgreSQL RLS | Database-enforced security, simpler app code, proven at scale |
| **Rate Limiting** | Sliding Window (Redis) | Better burst handling than token bucket, lower memory than leaky bucket |
| **Quota Tracking** | Write-through cache | Real-time accuracy for billing, acceptable write overhead |
| **S3 Structure** | Prefix-based isolation | Cost-effective, easier than separate buckets, standard practice |
| **Proxy Provider** | BrightData | Best success rate (99.9%), proven anti-detection, reasonable cost |
| **Escalation Strategy** | Challenge-driven | Minimize cost, escalate only when needed, matches scraper.py |

### Timeline & Dependencies

```
Week 5-6: Multi-Tenancy
├── Week 5: Core isolation (RLS, API keys, rate limits)
└── Week 6: Storage & billing (S3, quotas, usage tracking)
    └── Depends on: Weeks 3-4 API layer

Week 7-8: Anti-Detection
├── Week 7: Layer integration (curl_cffi, Crawlee, proxies)
└── Week 8: Advanced routing (FlareSolverr, site profiles)
    └── Depends on: Week 6 tenant configuration
```

### Risk Profile

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| RLS performance impact | Low | Medium | Indexed tenant_id, connection pooling, benchmarking |
| Rate limit race conditions | Medium | Low | Lua scripts for atomic operations, tests with parallel requests |
| Proxy cost overruns | Medium | High | Start with 20% proxy usage, monitor per-tenant, circuit breakers |
| FlareSolverr instability | Medium | Medium | Timeout + fallback, separate deployment, health checks |

---

## Prerequisites & Integration Points

### What Must Exist from Weeks 3-4

Before starting Iteration 3, these components from the API Layer phase must be complete:

#### Database Schema (Baseline)
```sql
-- From Week 3-4: Basic job tracking
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    result JSONB,
    error TEXT
);

CREATE INDEX idx_jobs_status ON jobs(status) WHERE status IN ('pending', 'running');
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
```

#### API Endpoints (Baseline)
```python
# From Week 3-4: Basic scrape endpoint
POST /v2/scrape
{
    "url": "https://example.com",
    "formats": ["markdown", "html"]
}

# Response
{
    "success": true,
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending"
}

GET /v2/scrape/{id}
{
    "success": true,
    "status": "completed",
    "data": {
        "markdown": "...",
        "html": "..."
    }
}
```

#### BullMQ Queue Setup
```python
# From Week 3-4: Job queue
from bullmq import Queue, Worker

scrape_queue = Queue("scrape", connection=redis_connection)

async def process_scrape_job(job):
    url = job.data["url"]
    # Basic Crawlee scraping
    result = await crawlee_scraper.scrape(url)
    return result
```

### Integration Points

**Week 5-6 (Multi-Tenancy) adds:**
- `tenant_id` column to all tables
- API key → tenant_id resolution middleware
- Rate limit checks before job enqueue
- Quota checks before job enqueue

**Week 7-8 (Anti-Detection) adds:**
- `scrape_layer` to job metadata (which layer succeeded)
- `proxy_used` boolean flag
- Challenge detection in job processing
- Layer escalation logic in worker

---

## Iteration 3: Multi-Tenancy (Weeks 5-6)

### Overview

Transform the single-tenant API into a secure multi-tenant platform where each tenant:
- Has isolated data (can never see other tenants' jobs/results)
- Has rate limits (e.g., 100 requests/hour)
- Has quotas (e.g., 10,000 scrapes/month)
- Has separate storage (S3 prefix: `tenant_id/job_id/`)
- Pays based on usage (tracked for billing)

### User Stories

#### Story 3.1: Tenant Registration & API Keys

**As a** platform administrator
**I want to** register new tenants and generate API keys
**So that** customers can authenticate and use the platform securely

**Acceptance Criteria:**

```gherkin
Given I am an authenticated admin
When I POST /admin/tenants with:
  {
    "name": "Acme Corp",
    "email": "admin@acme.com",
    "tier": "pro"
  }
Then I receive a response with:
  {
    "tenant_id": "tenant_123abc",
    "api_key": "fc_live_xxxxxxxxxxxxx"
  }
And the tenant is created in the database
And the API key is hashed and stored securely

Given I have a valid API key "fc_live_xxxxxxxxxxxxx"
When I make any API request with header "Authorization: Bearer fc_live_xxxxxxxxxxxxx"
Then the middleware resolves my tenant_id as "tenant_123abc"
And my request context includes tenant information

Given I have an invalid API key
When I make any API request
Then I receive 401 Unauthorized
And the request is logged for security monitoring
```

**Technical Implementation:**

```sql
-- Migration: 003_add_tenants.sql
CREATE TYPE tenant_tier AS ENUM ('free', 'pro', 'enterprise');
CREATE TYPE tenant_status AS ENUM ('active', 'suspended', 'cancelled');

CREATE TABLE tenants (
    id TEXT PRIMARY KEY,  -- tenant_123abc
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    tier tenant_tier NOT NULL DEFAULT 'free',
    status tenant_status NOT NULL DEFAULT 'active',

    -- Rate limiting configuration
    rate_limit_per_hour INTEGER NOT NULL DEFAULT 100,
    rate_limit_per_day INTEGER NOT NULL DEFAULT 1000,

    -- Quota configuration
    monthly_quota INTEGER NOT NULL DEFAULT 10000,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL UNIQUE,  -- bcrypt hash of actual key
    key_prefix TEXT NOT NULL,  -- First 8 chars for identification: fc_live_
    name TEXT,  -- Optional friendly name
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash) WHERE revoked_at IS NULL;

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

```python
# api/services/tenant.py
import secrets
import bcrypt
from datetime import datetime
from typing import Optional

class TenantService:
    """Manage tenant lifecycle and API keys."""

    async def create_tenant(
        self,
        name: str,
        email: str,
        tier: str = "free"
    ) -> dict:
        """Create a new tenant with API key."""

        # Generate tenant ID
        tenant_id = f"tenant_{secrets.token_hex(8)}"

        # Generate API key: fc_live_<32 random chars>
        api_key = f"fc_live_{secrets.token_urlsafe(32)}"
        key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

        async with db.transaction():
            # Create tenant
            await db.execute(
                """
                INSERT INTO tenants (id, name, email, tier)
                VALUES ($1, $2, $3, $4)
                """,
                tenant_id, name, email, tier
            )

            # Create API key
            await db.execute(
                """
                INSERT INTO api_keys (tenant_id, key_hash, key_prefix)
                VALUES ($1, $2, $3)
                """,
                tenant_id, key_hash, api_key[:16]
            )

        return {
            "tenant_id": tenant_id,
            "api_key": api_key,  # Only returned once, never stored plaintext
            "tier": tier
        }

    async def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return tenant_id if valid."""

        # Get key hash from database
        row = await db.fetchrow(
            """
            SELECT ak.tenant_id, ak.key_hash, t.status
            FROM api_keys ak
            JOIN tenants t ON ak.tenant_id = t.id
            WHERE ak.revoked_at IS NULL
            AND t.status = 'active'
            AND ak.key_prefix = $1
            LIMIT 1
            """,
            api_key[:16]  # Use prefix for faster lookup
        )

        if not row:
            return None

        # Verify hash (constant-time comparison)
        if bcrypt.checkpw(api_key.encode(), row["key_hash"].encode()):
            # Update last_used_at asynchronously (don't block)
            asyncio.create_task(self._update_last_used(api_key[:16]))
            return row["tenant_id"]

        return None

    async def _update_last_used(self, key_prefix: str):
        """Update last_used_at timestamp for API key."""
        await db.execute(
            "UPDATE api_keys SET last_used_at = NOW() WHERE key_prefix = $1",
            key_prefix
        )
```

```python
# api/middleware/auth.py
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract and verify API key, return tenant_id."""

    api_key = credentials.credentials

    # Verify API key
    tenant_service = TenantService()
    tenant_id = await tenant_service.verify_api_key(api_key)

    if not tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or revoked API key"
        )

    return tenant_id

# Usage in routes
@app.post("/v2/scrape")
async def scrape(
    request: ScrapeRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    # tenant_id is now available in all routes
    pass
```

**Definition of Done:**
- [ ] Tenants table created with tier/status columns
- [ ] API keys table with bcrypt hashing
- [ ] Admin endpoint to create tenants (POST /admin/tenants)
- [ ] Middleware to verify API keys and inject tenant_id
- [ ] 401 response for invalid/revoked keys
- [ ] Tests: Valid key, invalid key, revoked key, suspended tenant
- [ ] API key generation CLI tool for admins

---

#### Story 3.2: Row-Level Security (RLS) for Data Isolation

**As a** platform operator
**I want to** enforce tenant data isolation at the database level
**So that** tenants can never access each other's data, even if application code has bugs

**Acceptance Criteria:**

```gherkin
Given I am tenant "tenant_123"
And another tenant "tenant_456" has jobs in the database
When I query the jobs table with my database connection
Then I only see my jobs (WHERE tenant_id = 'tenant_123')
And I never see jobs from tenant_456
And this enforcement happens at the PostgreSQL level

Given a developer writes a buggy SQL query that forgets the tenant_id filter
When the query executes
Then PostgreSQL RLS still enforces tenant isolation
And the bug cannot leak data

Given I am an admin user
When I query with an admin database connection
Then I can see all tenants' data (RLS bypassed for admin role)
```

**Technical Implementation:**

```sql
-- Migration: 004_add_rls.sql

-- Step 1: Add tenant_id to all data tables
ALTER TABLE jobs ADD COLUMN tenant_id TEXT NOT NULL REFERENCES tenants(id);
CREATE INDEX idx_jobs_tenant ON jobs(tenant_id);

-- Step 2: Enable RLS on data tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Step 3: Create policies

-- Policy: Users can only see their own tenant's rows
CREATE POLICY tenant_isolation_policy ON jobs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::text);

-- Policy: Admins can see everything (use a different role)
CREATE POLICY admin_all_access ON jobs
    FOR ALL
    TO admin_role
    USING (true);

-- Step 4: Create application database role (non-admin)
CREATE ROLE app_user;
GRANT CONNECT ON DATABASE scraper_platform TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON jobs TO app_user;
GRANT SELECT ON tenants TO app_user;

-- Step 5: Create admin role for ops/analytics
CREATE ROLE admin_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO admin_role;
```

```python
# database/connection.py
import asyncpg
from contextlib import asynccontextmanager

class TenantAwareDB:
    """Database connection pool with RLS support."""

    def __init__(self):
        self.pool = None

    async def init(self, dsn: str):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            dsn,
            min_size=10,
            max_size=50,
            command_timeout=60
        )

    @asynccontextmanager
    async def with_tenant(self, tenant_id: str):
        """Context manager that sets tenant_id for RLS."""
        async with self.pool.acquire() as conn:
            # Set session variable for RLS
            await conn.execute(
                "SET LOCAL app.current_tenant_id = $1",
                tenant_id
            )

            try:
                yield conn
            finally:
                # Reset is automatic when connection returns to pool
                pass

    @asynccontextmanager
    async def as_admin(self):
        """Context manager for admin operations (bypass RLS)."""
        # Use a different connection pool with admin_role credentials
        # Or temporarily disable RLS: SET LOCAL row_security = OFF
        async with self.admin_pool.acquire() as conn:
            yield conn

# Global instance
db = TenantAwareDB()

# Usage in application
async def get_job(job_id: str, tenant_id: str):
    async with db.with_tenant(tenant_id) as conn:
        # This query is automatically filtered by RLS
        row = await conn.fetchrow(
            "SELECT * FROM jobs WHERE id = $1",
            job_id
        )
        # Even if we forget "AND tenant_id = $1", RLS enforces it
        return row
```

**Why PostgreSQL RLS over Application-Level Filtering?**

| Criterion | PostgreSQL RLS | Application-Level | Decision |
|-----------|---------------|-------------------|----------|
| **Security** | ✅ Database-enforced, immune to app bugs | ❌ Relies on developers never forgetting WHERE clause | **RLS Wins** |
| **Performance** | ✅ Uses indexes on tenant_id efficiently | ✅ Same (if implemented correctly) | Tie |
| **Code Simplicity** | ✅ Write queries without tenant_id filter | ❌ Every query needs explicit filter | **RLS Wins** |
| **Testing** | ✅ Harder to accidentally leak data in tests | ❌ Easy to forget filters in test data | **RLS Wins** |
| **Debugging** | ❌ Slightly harder to debug (need to check session var) | ✅ Explicit in SQL | App-Level Wins |
| **Migration Effort** | ⚠️ Requires careful migration (add column, backfill, enable RLS) | ✅ Easier to add incrementally | App-Level Wins |
| **Audit Trail** | ✅ Can log policy violations | ⚠️ Harder to audit | **RLS Wins** |

**Decision:** Use PostgreSQL RLS. Security benefit outweighs slight debugging complexity. This is industry best practice for SaaS platforms (used by Supabase, Retool, etc.).

**Definition of Done:**
- [ ] tenant_id column added to jobs table (and all future data tables)
- [ ] RLS enabled on jobs table
- [ ] tenant_isolation_policy created and tested
- [ ] app_user role with limited permissions
- [ ] admin_role for operations/analytics
- [ ] TenantAwareDB wrapper class with .with_tenant() context manager
- [ ] Tests: Tenant A cannot see Tenant B's jobs
- [ ] Tests: Forgetting tenant_id filter still enforces isolation
- [ ] Documentation on RLS architecture for team

---

#### Story 3.3: Rate Limiting (Sliding Window)

**As a** platform operator
**I want to** enforce per-tenant rate limits
**So that** no single tenant can overwhelm the system

**Acceptance Criteria:**

```gherkin
Given I am a "pro" tier tenant with 100 requests/hour limit
When I make 100 requests in 60 minutes
Then all 100 succeed

When I make the 101st request within the same hour
Then I receive 429 Too Many Requests
And the response includes headers:
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 0
  X-RateLimit-Reset: <timestamp>

Given I am at my rate limit
When the sliding window moves forward by 1 minute
And requests from 61 minutes ago drop out of the window
Then I can make new requests again

Given I am a "free" tier tenant (10 requests/hour)
When I upgrade to "pro" tier (100 requests/hour)
Then my rate limit updates immediately
And I can make 90 more requests in the current hour
```

**Why Sliding Window over Token Bucket or Leaky Bucket?**

| Algorithm | Pros | Cons | Use Case |
|-----------|------|------|----------|
| **Token Bucket** | Simple, allows bursts | Burst can overwhelm downstream | Good for network traffic |
| **Leaky Bucket** | Smooths traffic evenly | No bursts, requires more memory (queue) | Good for video streaming |
| **Sliding Window** | Fair distribution, handles bursts well, accurate | Slightly more complex | **Best for API rate limiting** |

**Decision:** Sliding Window Counter in Redis
- More accurate than fixed window (no boundary issues)
- Lower memory than leaky bucket (no queue needed)
- Better burst handling than token bucket (allows legitimate bursts)
- Standard for SaaS APIs (Stripe, GitHub, Twilio all use sliding window)

**Technical Implementation:**

```lua
-- Lua script: rate_limit.lua (executed atomically in Redis)
-- This ensures no race conditions even with parallel requests

local key = KEYS[1]  -- rate_limit:tenant_123:hour
local limit = tonumber(ARGV[1])  -- e.g., 100
local window = tonumber(ARGV[2])  -- e.g., 3600 (1 hour in seconds)
local now = tonumber(ARGV[3])  -- current timestamp

-- Remove requests outside the sliding window
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count requests in current window
local count = redis.call('ZCARD', key)

if count < limit then
    -- Allow request: Add to sorted set with current timestamp as score
    redis.call('ZADD', key, now, now .. ':' .. math.random())
    redis.call('EXPIRE', key, window)
    return {1, limit - count - 1}  -- [allowed, remaining]
else
    -- Deny request
    return {0, 0}  -- [denied, remaining]
end
```

```python
# api/services/rate_limit.py
import time
from typing import Tuple
from redis import Redis

class RateLimiter:
    """Redis-based sliding window rate limiter."""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.script = self._load_lua_script()

    def _load_lua_script(self):
        """Load and register Lua script."""
        with open("api/services/rate_limit.lua") as f:
            return self.redis.register_script(f.read())

    async def check_rate_limit(
        self,
        tenant_id: str,
        limit: int,
        window: int = 3600  # 1 hour
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limit.

        Returns:
            (allowed: bool, remaining: int)
        """
        key = f"rate_limit:{tenant_id}:hour"
        now = int(time.time())

        # Execute Lua script atomically
        result = await self.script(
            keys=[key],
            args=[limit, window, now]
        )

        allowed = result[0] == 1
        remaining = result[1]

        return allowed, remaining

    async def get_reset_time(self, tenant_id: str, window: int = 3600) -> int:
        """Get timestamp when rate limit resets."""
        key = f"rate_limit:{tenant_id}:hour"

        # Get oldest request in window
        oldest = await self.redis.zrange(key, 0, 0, withscores=True)

        if oldest:
            oldest_timestamp = int(oldest[0][1])
            return oldest_timestamp + window

        return int(time.time()) + window
```

```python
# api/middleware/rate_limit.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on all API requests."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limit for health checks
        if request.url.path in ["/health", "/ready"]:
            return await call_next(request)

        # Get tenant from request (set by auth middleware)
        tenant_id = request.state.tenant_id

        # Get tenant's rate limit from database (cached in Redis)
        tenant = await self._get_tenant_config(tenant_id)
        limit = tenant["rate_limit_per_hour"]

        # Check rate limit
        rate_limiter = RateLimiter(redis)
        allowed, remaining = await rate_limiter.check_rate_limit(
            tenant_id, limit
        )

        if not allowed:
            # Rate limit exceeded
            reset_time = await rate_limiter.get_reset_time(tenant_id)

            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time - int(time.time()))
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    async def _get_tenant_config(self, tenant_id: str) -> dict:
        """Get tenant config (with Redis caching)."""
        # Try cache first
        cache_key = f"tenant_config:{tenant_id}"
        cached = await redis.get(cache_key)

        if cached:
            return json.loads(cached)

        # Fetch from database
        async with db.with_tenant(tenant_id) as conn:
            row = await conn.fetchrow(
                "SELECT rate_limit_per_hour, rate_limit_per_day, monthly_quota FROM tenants WHERE id = $1",
                tenant_id
            )

        config = dict(row)

        # Cache for 5 minutes
        await redis.setex(cache_key, 300, json.dumps(config))

        return config
```

**Definition of Done:**
- [ ] Lua script for atomic rate limit checks
- [ ] RateLimiter service class with sliding window logic
- [ ] RateLimitMiddleware integrated into FastAPI app
- [ ] Rate limit headers in all responses (X-RateLimit-*)
- [ ] 429 response when limit exceeded
- [ ] Tests: Sequential requests within limit
- [ ] Tests: Parallel requests at limit boundary (race conditions)
- [ ] Tests: Sliding window correctly expires old requests
- [ ] Tests: Different limits for different tiers
- [ ] Performance benchmark: >1000 checks/second

---

#### Story 3.4: Quota Management & Usage Tracking

**As a** platform operator
**I want to** track per-tenant usage for billing
**So that** we can charge customers accurately and prevent quota abuse

**Acceptance Criteria:**

```gherkin
Given I am a "pro" tier tenant with 10,000 scrapes/month quota
When I successfully complete 5,000 scrapes in March 2026
Then my usage tracking shows:
  {
    "month": "2026-03",
    "quota": 10000,
    "used": 5000,
    "remaining": 5000
  }

When I attempt to start my 10,001st job
Then I receive 402 Payment Required
And the response says "Monthly quota exceeded. Upgrade or wait until next month."

When the calendar month rolls over to April 2026
Then my quota resets to 0/10,000
And I can scrape again

Given I am an admin
When I query GET /admin/tenants/{tenant_id}/usage?month=2026-03
Then I see detailed usage breakdown:
  {
    "month": "2026-03",
    "scrapes_total": 5000,
    "scrapes_http": 4500,
    "scrapes_browser": 500,
    "cost_estimate": "$15.25",
    "by_day": [...]
  }
```

**Technical Implementation:**

```sql
-- Migration: 005_add_usage_tracking.sql

CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    job_id UUID NOT NULL REFERENCES jobs(id),

    -- Usage details
    month TEXT NOT NULL,  -- YYYY-MM format
    scrape_type TEXT NOT NULL,  -- 'http' | 'browser'
    layer_used INTEGER,  -- 1-5 (which layer succeeded)
    proxy_used BOOLEAN DEFAULT FALSE,

    -- Cost tracking (in cents)
    compute_cost_cents INTEGER NOT NULL DEFAULT 0,
    proxy_cost_cents INTEGER NOT NULL DEFAULT 0,
    total_cost_cents INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_usage_tenant_month ON usage_records(tenant_id, month);
CREATE INDEX idx_usage_month ON usage_records(month);

-- Aggregate table for fast quota checks
CREATE TABLE usage_summary (
    tenant_id TEXT NOT NULL,
    month TEXT NOT NULL,

    -- Counts
    scrapes_total INTEGER NOT NULL DEFAULT 0,
    scrapes_http INTEGER NOT NULL DEFAULT 0,
    scrapes_browser INTEGER NOT NULL DEFAULT 0,

    -- Costs (in cents)
    total_cost_cents INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (tenant_id, month)
);

-- Trigger to update summary table
CREATE OR REPLACE FUNCTION update_usage_summary()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO usage_summary (tenant_id, month, scrapes_total, scrapes_http, scrapes_browser, total_cost_cents)
    VALUES (
        NEW.tenant_id,
        NEW.month,
        1,
        CASE WHEN NEW.scrape_type = 'http' THEN 1 ELSE 0 END,
        CASE WHEN NEW.scrape_type = 'browser' THEN 1 ELSE 0 END,
        NEW.total_cost_cents
    )
    ON CONFLICT (tenant_id, month) DO UPDATE SET
        scrapes_total = usage_summary.scrapes_total + 1,
        scrapes_http = usage_summary.scrapes_http + CASE WHEN NEW.scrape_type = 'http' THEN 1 ELSE 0 END,
        scrapes_browser = usage_summary.scrapes_browser + CASE WHEN NEW.scrape_type = 'browser' THEN 1 ELSE 0 END,
        total_cost_cents = usage_summary.total_cost_cents + NEW.total_cost_cents,
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER usage_records_summary AFTER INSERT ON usage_records
    FOR EACH ROW EXECUTE FUNCTION update_usage_summary();
```

```python
# api/services/quota.py
from datetime import datetime
from typing import Optional

class QuotaService:
    """Manage tenant quotas and usage tracking."""

    async def check_quota(self, tenant_id: str) -> tuple[bool, dict]:
        """
        Check if tenant has quota remaining for this month.

        Returns:
            (has_quota: bool, usage_info: dict)
        """
        current_month = datetime.now().strftime("%Y-%m")

        # Get tenant's quota limit
        tenant = await db.fetchrow(
            "SELECT monthly_quota FROM tenants WHERE id = $1",
            tenant_id
        )
        quota_limit = tenant["monthly_quota"]

        # Get current usage from summary table (fast!)
        usage = await db.fetchrow(
            """
            SELECT scrapes_total, total_cost_cents
            FROM usage_summary
            WHERE tenant_id = $1 AND month = $2
            """,
            tenant_id, current_month
        )

        if not usage:
            # No usage this month yet
            used = 0
            cost = 0
        else:
            used = usage["scrapes_total"]
            cost = usage["total_cost_cents"]

        has_quota = used < quota_limit

        usage_info = {
            "month": current_month,
            "quota": quota_limit,
            "used": used,
            "remaining": max(0, quota_limit - used),
            "cost_cents": cost,
            "cost_usd": cost / 100
        }

        return has_quota, usage_info

    async def track_usage(
        self,
        tenant_id: str,
        job_id: str,
        scrape_type: str,
        layer_used: int,
        proxy_used: bool
    ):
        """
        Record usage for a completed job.

        This is called by the worker after job completion.
        """
        current_month = datetime.now().strftime("%Y-%m")

        # Calculate cost based on layer and proxy usage
        compute_cost_cents = self._calculate_compute_cost(scrape_type, layer_used)
        proxy_cost_cents = self._calculate_proxy_cost(proxy_used)
        total_cost_cents = compute_cost_cents + proxy_cost_cents

        # Insert usage record (trigger will update summary)
        await db.execute(
            """
            INSERT INTO usage_records (
                tenant_id, job_id, month, scrape_type, layer_used,
                proxy_used, compute_cost_cents, proxy_cost_cents, total_cost_cents
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            tenant_id, job_id, current_month, scrape_type, layer_used,
            proxy_used, compute_cost_cents, proxy_cost_cents, total_cost_cents
        )

    def _calculate_compute_cost(self, scrape_type: str, layer: int) -> int:
        """Calculate compute cost in cents."""
        # Cost per scrape (from STRATEGIC_DECISION.md)
        if scrape_type == "http":
            return 50  # $0.50 per 1000 = 0.05 cents each
        elif scrape_type == "browser":
            return 500  # $5.00 per 1000 = 0.5 cents each
        return 0

    def _calculate_proxy_cost(self, proxy_used: bool) -> int:
        """Calculate proxy cost in cents."""
        if proxy_used:
            return 200  # $2.00 per 1000 = 0.2 cents each
        return 0
```

```python
# api/middleware/quota.py
from fastapi import Request, HTTPException

class QuotaMiddleware(BaseHTTPMiddleware):
    """Middleware to check quotas before accepting jobs."""

    async def dispatch(self, request: Request, call_next):
        # Only check quota for scrape endpoints
        if request.url.path.startswith("/v2/scrape"):
            tenant_id = request.state.tenant_id

            quota_service = QuotaService()
            has_quota, usage_info = await quota_service.check_quota(tenant_id)

            if not has_quota:
                raise HTTPException(
                    status_code=402,
                    detail="Monthly quota exceeded. Upgrade your plan or wait until next month.",
                    headers={
                        "X-Quota-Limit": str(usage_info["quota"]),
                        "X-Quota-Used": str(usage_info["used"]),
                        "X-Quota-Reset": self._get_month_reset_time()
                    }
                )

            # Add quota info to response headers
            response = await call_next(request)
            response.headers["X-Quota-Limit"] = str(usage_info["quota"])
            response.headers["X-Quota-Remaining"] = str(usage_info["remaining"])

            return response

        return await call_next(request)

    def _get_month_reset_time(self) -> str:
        """Get timestamp when quota resets (first day of next month)."""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        next_month = datetime.now() + relativedelta(months=1)
        reset = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return str(int(reset.timestamp()))
```

**Definition of Done:**
- [ ] usage_records table with cost tracking
- [ ] usage_summary aggregate table (for fast quota checks)
- [ ] Trigger to auto-update summary on insert
- [ ] QuotaService.check_quota() method
- [ ] QuotaService.track_usage() method (called by workers)
- [ ] QuotaMiddleware to enforce quotas
- [ ] 402 response when quota exceeded
- [ ] Quota headers in all responses (X-Quota-*)
- [ ] Admin endpoint: GET /admin/tenants/{id}/usage
- [ ] Tests: Quota enforcement
- [ ] Tests: Usage tracking after job completion
- [ ] Tests: Monthly quota reset
- [ ] Tests: Accurate cost calculation

---

#### Story 3.5: S3 Storage with Tenant Isolation

**As a** platform operator
**I want to** store scraped content in S3 with tenant isolation
**So that** we can scale storage cheaply and securely

**Acceptance Criteria:**

```gherkin
Given I am tenant "tenant_123"
When I successfully complete a scrape job "job_456"
Then the scraped HTML is stored at:
  s3://scraper-platform-data/tenant_123/job_456/content.html

And the scraped markdown is stored at:
  s3://scraper-platform-data/tenant_123/job_456/content.md

When I request GET /v2/scrape/job_456
Then I receive a signed S3 URL valid for 1 hour
And the URL allows me to download my content

Given I am tenant "tenant_123"
When I try to access tenant "tenant_456"'s S3 objects
Then I receive 403 Forbidden
And the bucket policy prevents cross-tenant access
```

**Why Prefix-Based Isolation over Separate Buckets?**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Separate Bucket per Tenant** | Strongest isolation, separate billing | AWS limit: 100 buckets/account, complex to manage | ❌ Not scalable |
| **Prefix-Based (`tenant_id/`)** | Unlimited tenants, standard practice, easy | Requires careful IAM policy | ✅ **Use This** |
| **Single Bucket, No Isolation** | Simplest | Security nightmare | ❌ Never |

**Decision:** Prefix-based isolation with IAM policies. This is how Supabase, Vercel, and most SaaS platforms handle S3.

**Technical Implementation:**

```python
# api/services/storage.py
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

class StorageService:
    """Manage S3 storage with tenant isolation."""

    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.bucket = os.getenv("S3_BUCKET", "scraper-platform-data")

    async def store_scrape_result(
        self,
        tenant_id: str,
        job_id: str,
        html_content: str,
        markdown_content: str
    ) -> dict:
        """
        Store scrape results in S3 with tenant isolation.

        Returns:
            dict with S3 keys
        """
        # S3 key prefix: tenant_id/job_id/
        prefix = f"{tenant_id}/{job_id}"

        # Store HTML
        html_key = f"{prefix}/content.html"
        await self._upload_object(html_key, html_content, "text/html")

        # Store Markdown
        md_key = f"{prefix}/content.md"
        await self._upload_object(md_key, markdown_content, "text/markdown")

        # Store metadata
        metadata_key = f"{prefix}/metadata.json"
        metadata = {
            "tenant_id": tenant_id,
            "job_id": job_id,
            "stored_at": datetime.now().isoformat(),
            "sizes": {
                "html_bytes": len(html_content.encode()),
                "markdown_bytes": len(markdown_content.encode())
            }
        }
        await self._upload_object(
            metadata_key,
            json.dumps(metadata),
            "application/json"
        )

        return {
            "html_key": html_key,
            "markdown_key": md_key,
            "metadata_key": metadata_key
        }

    async def _upload_object(self, key: str, content: str, content_type: str):
        """Upload object to S3."""
        try:
            await asyncio.to_thread(
                self.s3.put_object,
                Bucket=self.bucket,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType=content_type,
                ServerSideEncryption='AES256',  # Encrypt at rest
                # Add tenant_id to object metadata for auditing
                Metadata={
                    'tenant_id': key.split('/')[0]  # Extract tenant_id from prefix
                }
            )
        except ClientError as e:
            raise StorageError(f"Failed to upload to S3: {e}")

    async def generate_presigned_url(
        self,
        tenant_id: str,
        job_id: str,
        file_type: str = "html",
        expiration: int = 3600  # 1 hour
    ) -> str:
        """
        Generate a presigned URL for downloading content.

        This enforces tenant isolation - only the tenant who owns
        the job can generate a valid URL.
        """
        # Construct S3 key
        extension = "html" if file_type == "html" else "md"
        key = f"{tenant_id}/{job_id}/content.{extension}"

        # Verify object exists and belongs to tenant
        try:
            await asyncio.to_thread(
                self.s3.head_object,
                Bucket=self.bucket,
                Key=key
            )
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise NotFoundError(f"Content not found: {key}")
            raise

        # Generate presigned URL
        url = await asyncio.to_thread(
            self.s3.generate_presigned_url,
            'get_object',
            Params={
                'Bucket': self.bucket,
                'Key': key
            },
            ExpiresIn=expiration
        )

        return url

    async def delete_job_data(self, tenant_id: str, job_id: str):
        """Delete all S3 objects for a job (for GDPR compliance)."""
        prefix = f"{tenant_id}/{job_id}/"

        # List all objects with prefix
        response = await asyncio.to_thread(
            self.s3.list_objects_v2,
            Bucket=self.bucket,
            Prefix=prefix
        )

        if 'Contents' not in response:
            return  # No objects to delete

        # Delete all objects
        objects = [{'Key': obj['Key']} for obj in response['Contents']]
        await asyncio.to_thread(
            self.s3.delete_objects,
            Bucket=self.bucket,
            Delete={'Objects': objects}
        )
```

**S3 Bucket Policy (Terraform/CloudFormation):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowApplicationReadWrite",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/scraper-platform-app"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::scraper-platform-data/*"
    },
    {
      "Sid": "DenyWrongTenantAccess",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::scraper-platform-data/*",
      "Condition": {
        "StringNotEquals": {
          "s3:ExistingObjectTag/tenant_id": "${aws:PrincipalTag/tenant_id}"
        }
      }
    }
  ]
}
```

**Integration with Job Processing:**

```python
# workers/crawlee_worker.py
async def process_scrape_job(job):
    """Process scrape job and store results in S3."""
    tenant_id = job.data["tenant_id"]
    job_id = job.data["job_id"]
    url = job.data["url"]

    # Scrape content
    result = await crawlee_scraper.scrape(url)

    # Store in S3
    storage = StorageService()
    s3_keys = await storage.store_scrape_result(
        tenant_id=tenant_id,
        job_id=job_id,
        html_content=result.html,
        markdown_content=result.markdown
    )

    # Update job record with S3 keys
    async with db.with_tenant(tenant_id) as conn:
        await conn.execute(
            """
            UPDATE jobs
            SET status = 'completed',
                result = $1,
                updated_at = NOW()
            WHERE id = $2
            """,
            json.dumps({"s3_keys": s3_keys}),
            job_id
        )

    # Track usage
    quota_service = QuotaService()
    await quota_service.track_usage(
        tenant_id=tenant_id,
        job_id=job_id,
        scrape_type="http",  # or "browser"
        layer_used=1,
        proxy_used=False
    )
```

**Definition of Done:**
- [ ] StorageService class with S3 integration
- [ ] store_scrape_result() method
- [ ] generate_presigned_url() with tenant verification
- [ ] S3 bucket policy with prefix-based isolation
- [ ] Worker integration to store results in S3
- [ ] GET /v2/scrape/{id} returns presigned URLs
- [ ] delete_job_data() for GDPR compliance
- [ ] Tests: Store and retrieve content
- [ ] Tests: Cross-tenant access blocked
- [ ] Tests: Presigned URL expiration
- [ ] Documentation on S3 structure

---

### Week 5-6 Summary

**Deliverables:**
- ✅ Multi-tenant database schema with RLS
- ✅ API key authentication and tenant resolution
- ✅ Rate limiting (sliding window in Redis)
- ✅ Quota management and usage tracking
- ✅ S3 storage with tenant isolation
- ✅ Admin endpoints for tenant management
- ✅ Comprehensive test suite for isolation

**Database Migrations:**
- 003_add_tenants.sql - Tenants and API keys tables
- 004_add_rls.sql - Row-Level Security policies
- 005_add_usage_tracking.sql - Usage records and summary

**Key Metrics:**
- [ ] Tenant isolation: 100% (no cross-tenant leaks in tests)
- [ ] Rate limit accuracy: >99% (few false positives/negatives)
- [ ] Quota tracking latency: <50ms (summary table lookup)
- [ ] S3 upload time: <2s for 1MB content
- [ ] API key verification: <10ms (bcrypt with caching)

---

## Iteration 4: Anti-Detection (Weeks 7-8)

### Overview

Port the 3-layer anti-detection strategy from `scraper.py` to the Crawlee-based platform. This enables the platform to handle protected sites by intelligently escalating through layers:

1. **Layer 1:** curl_cffi (TLS fingerprinting, no JS, ~50ms)
2. **Layer 2:** Crawlee HTTP mode (session management, ~200-500ms)
3. **Layer 3:** Crawlee Playwright mode (full browser, ~2-5s)
4. **Layer 4:** BrightData proxies (residential IPs, +500ms)
5. **Layer 5:** FlareSolverr (Cloudflare solver, ~10-30s)

### User Stories

#### Story 4.1: curl_cffi Integration (Layer 1)

**As a** platform user
**I want to** scrape simple sites with TLS fingerprinting
**So that** I can bypass basic bot detection without the cost of a full browser

**Acceptance Criteria:**

```gherkin
Given I submit a scrape request for "https://httpbin.org/html"
When the system determines no JavaScript is needed
Then it uses curl_cffi with Chrome131 impersonation
And the scrape completes in <500ms
And the cost is minimal ($0.0005 per scrape)

Given the site returns a challenge page
When curl_cffi detects the challenge
Then it escalates to the next layer automatically
And logs the challenge type detected
```

**Technical Implementation:**

```python
# workers/layers/curl_cffi_layer.py
from curl_cffi import requests as curl_requests
from dataclasses import dataclass
from typing import Optional

@dataclass
class ScrapeResult:
    """Result from a scrape attempt."""
    success: bool
    content: Optional[str] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    elapsed: float = 0.0
    challenge_detected: bool = False
    challenge_type: Optional[str] = None

class CurlCffiLayer:
    """Layer 1: Fast HTTP scraping with TLS fingerprinting."""

    # Challenge detection patterns (from scraper.py)
    CHALLENGE_PATTERNS = {
        "cloudflare": [
            "cf-browser-verification",
            "Just a moment...",
            "Checking your browser",
            "ray ID:",
            "cf-challenge",
            "__cf_chl_jschl_tk__",
        ],
        "perimeterx": [
            "px-captcha",
            "_px",
            "perimeterx",
            "pxCaptcha",
        ],
        "datadome": [
            "datadome",
            "dd_challenge",
            "geo.captcha-delivery.com",
        ],
        "generic": [
            "Access denied",
            "bot detection",
            "Attention Required",
            "Access Denied",
            "Forbidden",
            "Please verify you are human",
        ],
    }

    async def scrape(
        self,
        url: str,
        use_proxy: bool = False,
        proxy_url: Optional[str] = None
    ) -> ScrapeResult:
        """
        Scrape URL using curl_cffi.

        Args:
            url: URL to scrape
            use_proxy: Whether to route through proxy
            proxy_url: Proxy URL (e.g., http://localhost:8118 for Tor)

        Returns:
            ScrapeResult with outcome
        """
        import time
        start_time = time.time()

        try:
            # Realistic browser headers
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }

            # Configure proxy if needed
            proxies = None
            if use_proxy and proxy_url:
                proxies = {"http": proxy_url, "https": proxy_url}

            # Make request with Chrome131 impersonation
            response = curl_requests.get(
                url,
                headers=headers,
                impersonate="chrome131",  # Latest Chrome TLS fingerprint
                proxies=proxies,
                timeout=30,
                allow_redirects=True,
            )

            elapsed = time.time() - start_time

            # Check for challenge pages
            is_challenge, challenge_type = self._detect_challenge(response.text)

            if is_challenge:
                return ScrapeResult(
                    success=False,
                    content=None,
                    status_code=response.status_code,
                    error=f"Challenge detected: {challenge_type}",
                    elapsed=elapsed,
                    challenge_detected=True,
                    challenge_type=challenge_type
                )

            # Check if content is meaningful (not empty/blocked)
            if not self._is_meaningful_content(response.text):
                return ScrapeResult(
                    success=False,
                    content=response.text,
                    status_code=response.status_code,
                    error="Content appears blocked or empty",
                    elapsed=elapsed
                )

            return ScrapeResult(
                success=True,
                content=response.text,
                status_code=response.status_code,
                elapsed=elapsed
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return ScrapeResult(
                success=False,
                error=f"curl_cffi error: {str(e)}",
                elapsed=elapsed
            )

    def _detect_challenge(self, html: str) -> tuple[bool, Optional[str]]:
        """Detect if page is a bot challenge."""
        if not html or len(html) < 100:
            return False, None

        html_lower = html.lower()

        # Check each challenge type
        for challenge_type, patterns in self.CHALLENGE_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in html_lower:
                    return True, challenge_type

        return False, None

    def _is_meaningful_content(self, html: str, min_length: int = 500) -> bool:
        """Check if HTML content is meaningful."""
        if not html:
            return False

        # Strip HTML tags and whitespace
        import re
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'\s+', ' ', text).strip()

        return len(text) >= min_length
```

**Definition of Done:**
- [ ] CurlCffiLayer class implemented
- [ ] Challenge detection patterns ported from scraper.py
- [ ] Proxy support (optional parameter)
- [ ] Meaningful content validation
- [ ] Tests: Successful scrape
- [ ] Tests: Challenge detection triggers escalation
- [ ] Tests: Proxy routing works
- [ ] Performance: <500ms for simple sites

---

#### Story 4.2: Crawlee Layer Integration (Layers 2-3)

**As a** platform user
**I want to** scrape JavaScript-heavy sites
**So that** I can extract data from modern web applications

**Acceptance Criteria:**

```gherkin
Given I submit a scrape request for a JavaScript-heavy site
When curl_cffi fails or detects JS is required
Then the system escalates to Crawlee HTTP mode (Layer 2)

Given Crawlee HTTP mode fails
Then the system escalates to Crawlee Playwright mode (Layer 3)
And a real browser renders the page
And JavaScript executes fully

Given a site requires both JS and anti-detection
Then Crawlee uses stealth plugins automatically
And the success rate is >90%
```

**Technical Implementation:**

```python
# workers/layers/crawlee_layer.py
from crawlee.playwright_crawler import PlaywrightCrawler
from crawlee.http_crawler import HttpCrawler
from crawlee import Configuration
from typing import Optional

class CrawleeLayer:
    """Layers 2-3: Crawlee-based scraping (HTTP and Browser modes)."""

    def __init__(self):
        # Configure Crawlee
        self.config = Configuration(
            max_request_retries=3,
            request_handler_timeout_secs=60
        )

    async def scrape_http(
        self,
        url: str,
        use_proxy: bool = False,
        proxy_config: Optional[dict] = None
    ) -> ScrapeResult:
        """
        Layer 2: Scrape using Crawlee HTTP mode.

        This uses session management and cookie handling,
        but no JavaScript execution.
        """
        import time
        start_time = time.time()

        result_data = {}

        async def request_handler(context):
            """Handle the request and extract data."""
            nonlocal result_data

            result_data = {
                "html": await context.request.text(),
                "status_code": context.response.status_code,
                "headers": dict(context.response.headers)
            }

        try:
            # Configure crawler
            crawler = HttpCrawler(
                request_handler=request_handler,
                max_requests_per_crawl=1,
                configuration=self.config
            )

            # Add proxy if needed
            if use_proxy and proxy_config:
                crawler.proxy_configuration = proxy_config

            # Run crawler
            await crawler.run([url])

            elapsed = time.time() - start_time

            html = result_data.get("html", "")
            status_code = result_data.get("status_code", 0)

            # Check for challenges
            is_challenge, challenge_type = self._detect_challenge(html)

            if is_challenge:
                return ScrapeResult(
                    success=False,
                    content=None,
                    status_code=status_code,
                    error=f"Challenge detected: {challenge_type}",
                    elapsed=elapsed,
                    challenge_detected=True,
                    challenge_type=challenge_type
                )

            return ScrapeResult(
                success=True,
                content=html,
                status_code=status_code,
                elapsed=elapsed
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return ScrapeResult(
                success=False,
                error=f"Crawlee HTTP error: {str(e)}",
                elapsed=elapsed
            )

    async def scrape_browser(
        self,
        url: str,
        use_proxy: bool = False,
        proxy_config: Optional[dict] = None,
        wait_for: int = 3000  # Wait for JS (ms)
    ) -> ScrapeResult:
        """
        Layer 3: Scrape using Crawlee Playwright mode (full browser).

        This executes JavaScript and handles complex sites.
        """
        import time
        start_time = time.time()

        result_data = {}

        async def request_handler(context):
            """Handle the request and extract data."""
            nonlocal result_data

            # Wait for page to load
            await context.page.wait_for_timeout(wait_for)

            # Extract content
            html = await context.page.content()

            result_data = {
                "html": html,
                "status_code": context.response.status if context.response else 200
            }

        try:
            # Configure browser crawler with stealth
            crawler = PlaywrightCrawler(
                request_handler=request_handler,
                max_requests_per_crawl=1,
                configuration=self.config,
                headless=True,
                browser_type="chromium"
            )

            # Add proxy if needed
            if use_proxy and proxy_config:
                crawler.proxy_configuration = proxy_config

            # Run crawler
            await crawler.run([url])

            elapsed = time.time() - start_time

            html = result_data.get("html", "")
            status_code = result_data.get("status_code", 0)

            # Check for challenges
            is_challenge, challenge_type = self._detect_challenge(html)

            if is_challenge:
                return ScrapeResult(
                    success=False,
                    content=None,
                    status_code=status_code,
                    error=f"Challenge detected: {challenge_type}",
                    elapsed=elapsed,
                    challenge_detected=True,
                    challenge_type=challenge_type
                )

            return ScrapeResult(
                success=True,
                content=html,
                status_code=status_code,
                elapsed=elapsed
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return ScrapeResult(
                success=False,
                error=f"Crawlee browser error: {str(e)}",
                elapsed=elapsed
            )

    def _detect_challenge(self, html: str) -> tuple[bool, Optional[str]]:
        """Reuse challenge detection logic."""
        # Same implementation as CurlCffiLayer
        pass
```

**Definition of Done:**
- [ ] CrawleeLayer class with HTTP and browser modes
- [ ] Proxy configuration support
- [ ] Stealth plugins enabled by default
- [ ] Wait time configuration for JavaScript
- [ ] Tests: HTTP mode successful scrape
- [ ] Tests: Browser mode successful scrape
- [ ] Tests: Automatic challenge detection
- [ ] Performance: HTTP <1s, Browser <5s

---

#### Story 4.3: BrightData Proxy Integration (Layer 4)

**As a** premium tier user
**I want to** use residential proxies
**So that** I can avoid IP-based blocking

**Acceptance Criteria:**

```gherkin
Given I am a "pro" or "enterprise" tier tenant
When my scrape request fails due to IP blocking
Then the system automatically routes through BrightData proxies
And uses a different residential IP for each request

Given I am a "free" tier tenant
When my scrape would benefit from proxies
Then I receive a suggestion to upgrade
But the scrape continues without proxies

Given I use proxies for 100 scrapes
Then my usage tracking shows proxy costs
And I am billed accordingly
```

**Why BrightData over other providers?**

| Provider | Success Rate | Cost/1K | Pros | Cons |
|----------|-------------|---------|------|------|
| **BrightData** | 99.9% | $3-5 | Best success rate, huge IP pool | Expensive |
| SmartProxy | 98% | $2-4 | Good value | Smaller pool |
| Oxylabs | 99% | $5-8 | Enterprise grade | Very expensive |
| Scraperapi | 95% | $1-3 | Cheap | Lower success rate |

**Decision:** BrightData for premium tiers. Best success rate justifies cost for paying customers.

**Technical Implementation:**

```python
# workers/layers/proxy_layer.py
from typing import Optional
from dataclasses import dataclass

@dataclass
class ProxyConfig:
    """Proxy configuration."""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    session_id: Optional[str] = None  # For sticky sessions

class ProxyManager:
    """Manage proxy rotation and health."""

    def __init__(self):
        # BrightData credentials from environment
        self.brightdata_username = os.getenv("BRIGHTDATA_USERNAME")
        self.brightdata_password = os.getenv("BRIGHTDATA_PASSWORD")
        self.brightdata_host = os.getenv("BRIGHTDATA_HOST", "brd.superproxy.io:22225")

    async def get_proxy_config(
        self,
        tenant_id: str,
        sticky_session: bool = False
    ) -> Optional[ProxyConfig]:
        """
        Get proxy configuration for tenant.

        Args:
            tenant_id: Tenant requesting proxy
            sticky_session: Use same IP for multiple requests

        Returns:
            ProxyConfig or None if tenant doesn't have proxy access
        """
        # Check if tenant has proxy access (based on tier)
        tenant = await self._get_tenant(tenant_id)

        if tenant["tier"] not in ["pro", "enterprise"]:
            return None

        # Generate session ID for sticky sessions
        session_id = None
        if sticky_session:
            import hashlib
            session_id = hashlib.md5(f"{tenant_id}-{time.time()}".encode()).hexdigest()[:8]

        # Construct BrightData proxy URL
        # Format: http://username-session-<session_id>:password@host:port
        username = self.brightdata_username
        if session_id:
            username = f"{username}-session-{session_id}"

        proxy_url = f"http://{username}:{self.brightdata_password}@{self.brightdata_host}"

        return ProxyConfig(
            url=proxy_url,
            username=username,
            password=self.brightdata_password,
            session_id=session_id
        )

    async def test_proxy_health(self, proxy_config: ProxyConfig) -> bool:
        """Test if proxy is working."""
        try:
            import requests
            response = requests.get(
                "https://httpbin.org/ip",
                proxies={
                    "http": proxy_config.url,
                    "https": proxy_config.url
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False

    async def _get_tenant(self, tenant_id: str) -> dict:
        """Get tenant configuration."""
        row = await db.fetchrow(
            "SELECT tier FROM tenants WHERE id = $1",
            tenant_id
        )
        return dict(row)
```

**Integration with Layers:**

```python
# workers/layers/crawlee_layer.py (updated)
async def scrape_browser(
    self,
    url: str,
    use_proxy: bool = False,
    tenant_id: Optional[str] = None
) -> ScrapeResult:
    """Scrape with optional proxy."""

    proxy_config = None
    if use_proxy and tenant_id:
        proxy_manager = ProxyManager()
        proxy_config = await proxy_manager.get_proxy_config(tenant_id)

    # ... rest of implementation
    if proxy_config:
        crawler.proxy_configuration = {
            "server": proxy_config.url,
            "username": proxy_config.username,
            "password": proxy_config.password
        }
```

**Definition of Done:**
- [ ] ProxyManager class with BrightData integration
- [ ] get_proxy_config() checks tenant tier
- [ ] Sticky session support (same IP for related requests)
- [ ] Proxy health checking
- [ ] Integration with Crawlee layers
- [ ] Usage tracking for proxy costs
- [ ] Tests: Proxy routing works
- [ ] Tests: Free tier cannot use proxies
- [ ] Tests: Sticky sessions maintain same IP

---

#### Story 4.4: FlareSolverr Integration (Layer 5)

**As a** platform user
**I want to** bypass Cloudflare challenges automatically
**So that** I can scrape Cloudflare-protected sites

**Acceptance Criteria:**

```gherkin
Given a site is protected by Cloudflare JavaScript challenge
When all other layers fail
Then the system routes to FlareSolverr
And the challenge is solved automatically

Given FlareSolverr solves the challenge
Then the system caches the solution (cookies/tokens)
And subsequent requests reuse the solution

Given FlareSolverr takes >30 seconds
Then the system times out and returns an error
And suggests manual verification or different approach
```

**Technical Implementation:**

```python
# workers/layers/flaresolverr_layer.py
import httpx
from typing import Optional

class FlareSolverrLayer:
    """Layer 5: Dedicated Cloudflare challenge solver."""

    def __init__(self):
        self.api_url = os.getenv("FLARESOLVERR_URL", "http://flaresolverr:8191/v1")

    async def scrape(
        self,
        url: str,
        max_timeout: int = 60000  # 60 seconds
    ) -> ScrapeResult:
        """
        Solve Cloudflare challenge using FlareSolverr.

        Args:
            url: URL to scrape
            max_timeout: Maximum time to wait (milliseconds)

        Returns:
            ScrapeResult
        """
        import time
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=70) as client:
                # FlareSolverr API request
                response = await client.post(
                    self.api_url,
                    json={
                        "cmd": "request.get",
                        "url": url,
                        "maxTimeout": max_timeout
                    }
                )

            elapsed = time.time() - start_time

            if response.status_code != 200:
                return ScrapeResult(
                    success=False,
                    error=f"FlareSolverr API error: {response.status_code}",
                    elapsed=elapsed
                )

            data = response.json()

            # Check if solution succeeded
            if data.get("status") != "ok":
                return ScrapeResult(
                    success=False,
                    error=f"FlareSolverr failed: {data.get('message', 'Unknown error')}",
                    elapsed=elapsed
                )

            # Extract solution
            solution = data.get("solution", {})
            content = solution.get("response")
            status_code = solution.get("status")
            cookies = solution.get("cookies", [])
            user_agent = solution.get("userAgent")

            if not content:
                return ScrapeResult(
                    success=False,
                    error="FlareSolverr returned no content",
                    elapsed=elapsed
                )

            return ScrapeResult(
                success=True,
                content=content,
                status_code=status_code,
                elapsed=elapsed,
                metadata={
                    "cookies": cookies,
                    "user_agent": user_agent
                }
            )

        except httpx.TimeoutException:
            elapsed = time.time() - start_time
            return ScrapeResult(
                success=False,
                error="FlareSolverr timeout (>60s)",
                elapsed=elapsed
            )
        except Exception as e:
            elapsed = time.time() - start_time
            return ScrapeResult(
                success=False,
                error=f"FlareSolverr error: {str(e)}",
                elapsed=elapsed
            )
```

**FlareSolverr Deployment (Docker Compose):**

```yaml
# docker-compose.yml (add to existing services)
services:
  flaresolverr:
    image: ghcr.io/flaresolverr/flaresolverr:latest
    environment:
      LOG_LEVEL: info
      TZ: America/New_York
      # Optional: Route through proxy
      # PROXY_URL: http://tor-proxy:8118
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8191/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Definition of Done:**
- [ ] FlareSolverrLayer class implemented
- [ ] API integration with FlareSolverr service
- [ ] Timeout handling (60s max)
- [ ] Cookie/token extraction for caching
- [ ] Docker deployment configuration
- [ ] Health check endpoint
- [ ] Tests: Successful challenge solve
- [ ] Tests: Timeout handling
- [ ] Tests: Error handling

---

#### Story 4.5: Intelligent Layer Router

**As a** platform operator
**I want to** automatically select the best scraping layer
**So that** we minimize cost while maximizing success rate

**Acceptance Criteria:**

```gherkin
Given a site is in the "known static HTML" category
When I submit a scrape request
Then it starts with Layer 1 (curl_cffi)
And succeeds without escalation

Given a site is in the "known Cloudflare" category
When I submit a scrape request
Then it skips to Layer 5 (FlareSolverr) immediately
And saves time by not trying lower layers

Given a site fails at Layer 2
When challenge is detected
Then it escalates to Layer 3 automatically
And logs the escalation for future optimization

Given I scrape the same site 10 times
When the system learns it always needs Layer 3
Then it creates a site profile
And future requests start at Layer 3
```

**Technical Implementation:**

```python
# workers/router.py
from typing import Optional
from dataclasses import dataclass
from workers.layers.curl_cffi_layer import CurlCffiLayer
from workers.layers.crawlee_layer import CrawleeLayer
from workers.layers.flaresolverr_layer import FlareSolverrLayer
from workers.layers.proxy_layer import ProxyManager

@dataclass
class SiteProfile:
    """Profile for a domain with learned characteristics."""
    domain: str
    optimal_layer: int  # Which layer typically succeeds
    requires_proxy: bool
    requires_js: bool
    challenge_type: Optional[str]
    success_count: int
    failure_count: int

class LayerRouter:
    """Intelligent router that selects optimal scraping layer."""

    def __init__(self):
        self.curl_layer = CurlCffiLayer()
        self.crawlee_layer = CrawleeLayer()
        self.flare_layer = FlareSolverrLayer()
        self.proxy_manager = ProxyManager()

    async def scrape(
        self,
        url: str,
        tenant_id: str,
        force_layer: Optional[int] = None
    ) -> dict:
        """
        Scrape URL with intelligent layer selection and escalation.

        Args:
            url: URL to scrape
            tenant_id: Tenant making request
            force_layer: Force specific layer (testing/debugging)

        Returns:
            dict with result and metadata
        """
        import time
        start_time = time.time()

        # Get site profile (learned behavior)
        profile = await self._get_site_profile(url)

        # Determine starting layer
        if force_layer:
            start_layer = force_layer
        elif profile:
            start_layer = profile.optimal_layer
        else:
            start_layer = 1  # Default: start cheap

        attempts = []

        # =====================================================================
        # Layer 1: curl_cffi (TLS fingerprinting, no JS)
        # =====================================================================
        if start_layer <= 1:
            logging.info(f"[{tenant_id}] Trying Layer 1: curl_cffi")
            result = await self.curl_layer.scrape(url, use_proxy=False)
            attempts.append({
                "layer": 1,
                "method": "curl_cffi",
                "success": result.success,
                "elapsed": result.elapsed,
                "error": result.error
            })

            if result.success:
                await self._update_site_profile(url, layer=1, success=True)
                return self._format_response(url, result, attempts, time.time() - start_time)

            logging.warning(f"[{tenant_id}] Layer 1 failed: {result.error}")

            # If challenge detected, skip to appropriate layer
            if result.challenge_detected:
                if result.challenge_type == "cloudflare":
                    start_layer = 5  # Skip to FlareSolverr
                else:
                    start_layer = 3  # Skip to browser

        # =====================================================================
        # Layer 2: Crawlee HTTP (session management)
        # =====================================================================
        if start_layer <= 2:
            logging.info(f"[{tenant_id}] Trying Layer 2: Crawlee HTTP")
            result = await self.crawlee_layer.scrape_http(url, use_proxy=False)
            attempts.append({
                "layer": 2,
                "method": "crawlee_http",
                "success": result.success,
                "elapsed": result.elapsed,
                "error": result.error
            })

            if result.success:
                await self._update_site_profile(url, layer=2, success=True)
                return self._format_response(url, result, attempts, time.time() - start_time)

            logging.warning(f"[{tenant_id}] Layer 2 failed: {result.error}")

        # =====================================================================
        # Layer 3: Crawlee Browser (full JS execution)
        # =====================================================================
        if start_layer <= 3:
            logging.info(f"[{tenant_id}] Trying Layer 3: Crawlee Browser")
            result = await self.crawlee_layer.scrape_browser(url, use_proxy=False)
            attempts.append({
                "layer": 3,
                "method": "crawlee_browser",
                "success": result.success,
                "elapsed": result.elapsed,
                "error": result.error
            })

            if result.success:
                await self._update_site_profile(url, layer=3, success=True)
                return self._format_response(url, result, attempts, time.time() - start_time)

            logging.warning(f"[{tenant_id}] Layer 3 failed: {result.error}")

        # =====================================================================
        # Layer 4: Browser + Proxy (residential IP)
        # =====================================================================
        if start_layer <= 4:
            # Check if tenant has proxy access
            proxy_config = await self.proxy_manager.get_proxy_config(tenant_id)

            if proxy_config:
                logging.info(f"[{tenant_id}] Trying Layer 4: Browser + Proxy")
                result = await self.crawlee_layer.scrape_browser(
                    url,
                    use_proxy=True,
                    tenant_id=tenant_id
                )
                attempts.append({
                    "layer": 4,
                    "method": "crawlee_browser_proxy",
                    "success": result.success,
                    "elapsed": result.elapsed,
                    "error": result.error
                })

                if result.success:
                    await self._update_site_profile(url, layer=4, success=True, requires_proxy=True)
                    return self._format_response(url, result, attempts, time.time() - start_time)

                logging.warning(f"[{tenant_id}] Layer 4 failed: {result.error}")
            else:
                logging.info(f"[{tenant_id}] Skipping Layer 4: No proxy access (upgrade to Pro)")

        # =====================================================================
        # Layer 5: FlareSolverr (Cloudflare challenge solver)
        # =====================================================================
        logging.info(f"[{tenant_id}] Trying Layer 5: FlareSolverr (last resort)")
        result = await self.flare_layer.scrape(url)
        attempts.append({
            "layer": 5,
            "method": "flaresolverr",
            "success": result.success,
            "elapsed": result.elapsed,
            "error": result.error
        })

        if result.success:
            await self._update_site_profile(url, layer=5, success=True, challenge_type="cloudflare")
            return self._format_response(url, result, attempts, time.time() - start_time)

        # =====================================================================
        # All layers failed
        # =====================================================================
        logging.error(f"[{tenant_id}] All 5 layers failed for {url}")
        await self._update_site_profile(url, layer=5, success=False)

        return {
            "success": False,
            "url": url,
            "error": "All scraping layers failed",
            "attempts": attempts,
            "total_elapsed": time.time() - start_time
        }

    async def _get_site_profile(self, url: str) -> Optional[SiteProfile]:
        """Get learned profile for domain."""
        domain = self._extract_domain(url)

        row = await db.fetchrow(
            """
            SELECT domain, optimal_layer, requires_proxy, requires_js,
                   challenge_type, success_count, failure_count
            FROM site_profiles
            WHERE domain = $1
            """,
            domain
        )

        if row:
            return SiteProfile(**dict(row))
        return None

    async def _update_site_profile(
        self,
        url: str,
        layer: int,
        success: bool,
        requires_proxy: bool = False,
        challenge_type: Optional[str] = None
    ):
        """Update or create site profile based on scrape result."""
        domain = self._extract_domain(url)

        await db.execute(
            """
            INSERT INTO site_profiles (
                domain, optimal_layer, requires_proxy, requires_js,
                challenge_type, success_count, failure_count
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (domain) DO UPDATE SET
                optimal_layer = CASE
                    WHEN $6 THEN $2  -- If success, update optimal layer
                    ELSE site_profiles.optimal_layer
                END,
                requires_proxy = $3 OR site_profiles.requires_proxy,
                requires_js = ($2 >= 3) OR site_profiles.requires_js,
                challenge_type = COALESCE($5, site_profiles.challenge_type),
                success_count = site_profiles.success_count + $6::int,
                failure_count = site_profiles.failure_count + $7::int,
                updated_at = NOW()
            """,
            domain, layer, requires_proxy, layer >= 3,
            challenge_type,
            1 if success else 0,
            0 if success else 1
        )

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        import re
        match = re.search(r'https?://([^/]+)', url)
        if match:
            domain = match.group(1)
            # Remove www. prefix
            domain = re.sub(r'^www\.', '', domain)
            return domain
        return ""

    def _format_response(self, url: str, result: ScrapeResult, attempts: list, total_elapsed: float) -> dict:
        """Format successful response."""
        return {
            "success": True,
            "url": url,
            "content": result.content,
            "status_code": result.status_code,
            "layer_used": attempts[-1]["layer"],
            "method_used": attempts[-1]["method"],
            "attempts": attempts,
            "total_elapsed": total_elapsed
        }
```

**Site Profiles Table:**

```sql
-- Migration: 006_add_site_profiles.sql
CREATE TABLE site_profiles (
    domain TEXT PRIMARY KEY,
    optimal_layer INTEGER NOT NULL DEFAULT 1 CHECK (optimal_layer BETWEEN 1 AND 5),
    requires_proxy BOOLEAN NOT NULL DEFAULT FALSE,
    requires_js BOOLEAN NOT NULL DEFAULT FALSE,
    challenge_type TEXT,  -- 'cloudflare', 'perimeterx', etc.
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_site_profiles_optimal_layer ON site_profiles(optimal_layer);
```

**Definition of Done:**
- [ ] LayerRouter class with full escalation logic
- [ ] Site profiles table for learning
- [ ] Automatic profile updates after each scrape
- [ ] Intelligent starting layer selection
- [ ] Challenge-based fast forwarding (skip layers)
- [ ] Comprehensive attempt logging
- [ ] Tests: Escalation from Layer 1 to 5
- [ ] Tests: Site profile creation and updates
- [ ] Tests: Forced layer for debugging
- [ ] Performance: Profile lookup <10ms

---

### Week 7-8 Summary

**Deliverables:**
- ✅ curl_cffi Layer 1 integration
- ✅ Crawlee Layers 2-3 (HTTP and Browser)
- ✅ BrightData proxy Layer 4
- ✅ FlareSolverr Layer 5
- ✅ Intelligent layer router with learning
- ✅ Site profiles for optimization
- ✅ Full escalation logic

**Database Migrations:**
- 006_add_site_profiles.sql - Learning system for optimal layer selection

**Key Metrics:**
- [ ] Layer 1 success rate: >60% for simple sites
- [ ] Layer 3 success rate: >85% for JS sites
- [ ] Layer 5 success rate: >95% for Cloudflare sites
- [ ] Average cost per scrape: <$0.01
- [ ] Escalation latency: <1s between layers
- [ ] Site profile accuracy: >80% (picks right layer first time)

---

## Database Evolution Strategy

### Migration Sequencing

All migrations are additive and backward-compatible:

```
Week 3-4 (Baseline):
├── 001_create_jobs.sql         # Basic job tracking
└── 002_add_queue_metadata.sql  # BullMQ integration

Week 5 (Multi-Tenancy Core):
├── 003_add_tenants.sql         # Tenants + API keys
└── 004_add_rls.sql             # Row-Level Security

Week 6 (Usage & Storage):
└── 005_add_usage_tracking.sql  # Usage records + summary

Week 7-8 (Anti-Detection):
└── 006_add_site_profiles.sql   # Learning system
```

### Zero-Downtime Migration Process

```sql
-- Example: Adding tenant_id to existing jobs table

-- Step 1: Add column as nullable (no downtime)
ALTER TABLE jobs ADD COLUMN tenant_id TEXT REFERENCES tenants(id);

-- Step 2: Backfill existing rows with a default tenant (background job)
UPDATE jobs SET tenant_id = 'tenant_default' WHERE tenant_id IS NULL;

-- Step 3: Add NOT NULL constraint (after backfill completes)
ALTER TABLE jobs ALTER COLUMN tenant_id SET NOT NULL;

-- Step 4: Add index for performance
CREATE INDEX CONCURRENTLY idx_jobs_tenant ON jobs(tenant_id);

-- Step 5: Enable RLS (after testing)
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
```

### Rollback Strategy

Each migration has a corresponding rollback script:

```sql
-- rollback/006_rollback_site_profiles.sql
DROP TABLE IF EXISTS site_profiles;
```

Store rollback scripts in `database/rollbacks/` directory.

---

## Cross-Cutting Concerns

### Logging & Observability

**Structured Logging:**
```python
# api/logging.py
import structlog

logger = structlog.get_logger()

# Usage
logger.info(
    "scrape_started",
    tenant_id=tenant_id,
    job_id=job_id,
    url=url,
    layer=1
)

logger.warning(
    "layer_failed",
    tenant_id=tenant_id,
    job_id=job_id,
    layer=2,
    error=str(e),
    elapsed=elapsed
)
```

**Key Metrics to Track:**
- Request rate (per tenant, per endpoint)
- Success rate (per layer, per tenant)
- Latency (P50, P95, P99 per layer)
- Cost (compute + proxy per scrape)
- Quota usage (per tenant, per month)
- Rate limit hits (per tenant)

**OpenTelemetry Integration:**
```python
# api/telemetry.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize tracer
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# Usage
with tracer.start_as_current_span("scrape_job") as span:
    span.set_attribute("tenant_id", tenant_id)
    span.set_attribute("job_id", job_id)
    span.set_attribute("layer", layer)

    result = await scrape_url(url)

    span.set_attribute("success", result.success)
    span.set_attribute("elapsed", result.elapsed)
```

### Error Handling

**Error Classification:**
```python
# api/errors.py
class PlatformError(Exception):
    """Base error for all platform exceptions."""
    pass

class RateLimitError(PlatformError):
    """Raised when rate limit exceeded."""
    status_code = 429

class QuotaExceededError(PlatformError):
    """Raised when monthly quota exceeded."""
    status_code = 402

class TenantNotFoundError(PlatformError):
    """Raised when tenant doesn't exist."""
    status_code = 404

class InvalidAPIKeyError(PlatformError):
    """Raised when API key is invalid."""
    status_code = 401

class ScrapeFailedError(PlatformError):
    """Raised when all scrape layers fail."""
    status_code = 500
```

**Global Error Handler:**
```python
# api/middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(PlatformError)
async def platform_error_handler(request: Request, exc: PlatformError):
    """Handle all platform errors consistently."""

    logger.error(
        "platform_error",
        error_type=type(exc).__name__,
        error_message=str(exc),
        tenant_id=getattr(request.state, "tenant_id", None),
        path=request.url.path
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )
```

### Testing Strategy

**Test Pyramid:**
```
            /\
           /  \
          / E2E \        ← 10% (critical user flows)
         /______\
        /        \
       /   API    \      ← 30% (endpoint integration)
      /__________\
     /            \
    /     Unit     \     ← 60% (business logic)
   /________________\
```

**Key Test Scenarios:**

**Multi-Tenancy:**
- ✅ Tenant A cannot access Tenant B's data (RLS enforcement)
- ✅ Rate limits are enforced per tenant
- ✅ Quotas are tracked accurately
- ✅ API keys work only for owning tenant
- ✅ S3 isolation prevents cross-tenant access

**Anti-Detection:**
- ✅ Layer 1 succeeds on simple sites
- ✅ Layer 2 escalates when JS detected
- ✅ Layer 3 renders JavaScript correctly
- ✅ Layer 4 uses proxies when tier allows
- ✅ Layer 5 solves Cloudflare challenges
- ✅ Site profiles learn and optimize

**Performance:**
- ✅ Rate limit check: <10ms
- ✅ Quota check: <50ms
- ✅ API key verification: <10ms
- ✅ RLS overhead: <5% query time increase
- ✅ Layer 1 scrape: <500ms
- ✅ Layer 3 scrape: <5s

---

## Success Metrics Dashboard

### Week 5-6 Completion Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Tenant Isolation** | 100% (zero leaks) | Automated tests with parallel requests |
| **Rate Limit Accuracy** | >99% | Load test with 1000 parallel requests at limit |
| **Quota Tracking Accuracy** | 100% (no double-counting) | Compare summary table vs detailed records |
| **S3 Upload Success** | >99.9% | Monitor S3 SDK error rate |
| **API Key Verification Speed** | <10ms P95 | Benchmark with 10K keys |
| **RLS Query Overhead** | <5% slower | Compare queries with/without RLS |

### Week 7-8 Completion Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Layer 1 Coverage** | >60% of simple sites | Track success rate on test corpus |
| **Layer 3 Success Rate** | >85% on JS sites | Track success rate on JS-heavy corpus |
| **Layer 5 Cloudflare Success** | >95% | Track success on known Cloudflare sites |
| **Average Cost per Scrape** | <$0.01 | Sum of compute + proxy costs |
| **Site Profile Accuracy** | >80% optimal layer | Compare first attempt vs final success layer |
| **Escalation Latency** | <1s between layers | Time from fail to next attempt |

### Overall Platform Health (Post Week 8)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Uptime** | >99.5% | Uptime monitor (Pingdom/UptimeRobot) |
| **Error Rate** | <5% | Successful jobs / Total jobs |
| **P95 Latency** | <10s | Per-job latency tracking |
| **Tenant Isolation** | 100% | Continuous RLS testing |
| **Cost per 1K Scrapes** | <$5 | Usage tracking summary |

---

## Appendices

### A. API Contract Examples

**Complete Scrape Flow:**

```bash
# 1. Create tenant (admin only)
curl -X POST http://localhost:8000/admin/tenants \
  -H "Authorization: Bearer admin_secret" \
  -d '{
    "name": "Acme Corp",
    "email": "admin@acme.com",
    "tier": "pro"
  }'

# Response:
{
  "tenant_id": "tenant_abc123",
  "api_key": "fc_live_xxxxxxxxxxxxxxxx",
  "tier": "pro"
}

# 2. Submit scrape request
curl -X POST http://localhost:8000/v2/scrape \
  -H "Authorization: Bearer fc_live_xxxxxxxxxxxxxxxx" \
  -d '{
    "url": "https://example.com",
    "formats": ["markdown", "html"]
  }'

# Response:
{
  "success": true,
  "id": "job_def456",
  "status": "pending"
}

# 3. Check status
curl http://localhost:8000/v2/scrape/job_def456 \
  -H "Authorization: Bearer fc_live_xxxxxxxxxxxxxxxx"

# Response (completed):
{
  "success": true,
  "status": "completed",
  "data": {
    "markdown_url": "https://s3.../tenant_abc123/job_def456/content.md?...",
    "html_url": "https://s3.../tenant_abc123/job_def456/content.html?..."
  },
  "metadata": {
    "layer_used": 3,
    "method_used": "crawlee_browser",
    "elapsed": 4.2,
    "attempts": [
      {"layer": 1, "success": false, "error": "Challenge detected"},
      {"layer": 3, "success": true, "elapsed": 4.2}
    ]
  }
}

# 4. Check usage
curl http://localhost:8000/v2/usage \
  -H "Authorization: Bearer fc_live_xxxxxxxxxxxxxxxx"

# Response:
{
  "month": "2026-02",
  "quota": 10000,
  "used": 47,
  "remaining": 9953,
  "cost_usd": 0.23
}
```

### B. Cost Breakdown by Layer

| Layer | Description | Time | Compute Cost/1K | Proxy Cost/1K | Total/1K | Use Case |
|-------|-------------|------|----------------|---------------|----------|----------|
| **Layer 1** | curl_cffi | ~50ms | $0.50 | $0 | **$0.50** | Static HTML, news sites |
| **Layer 2** | Crawlee HTTP | ~200ms | $1.00 | $0 | **$1.00** | Light JS, GitHub |
| **Layer 3** | Crawlee Browser | ~3s | $5.00 | $0 | **$5.00** | Heavy JS, SPAs |
| **Layer 4** | Browser + Proxy | ~4s | $5.00 | $2-5 | **$7-10** | Geo-blocked, IP-sensitive |
| **Layer 5** | FlareSolverr | ~15s | $10.00 | $0 | **$10.00** | Cloudflare challenges |

**Pricing Strategy:**
- Charge 5-7x cost (70-85% gross margin)
- Layer 1: Sell at $3/1K scrapes
- Layer 3: Sell at $30/1K scrapes
- Layer 5: Sell at $50/1K scrapes
- Include 20% proxy usage in Pro tier ($40/1K all-in)

### C. Reference Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                         API Gateway (FastAPI)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Auth MW      │→│ Rate Limit   │→│ Quota Check  │         │
│  │ (API Keys)   │  │ (Sliding Win)│  │ (Summary TB) │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                    Job Queue (BullMQ/Redis)                     │
│  - Tenant-isolated queues (tenant_id namespace)                 │
│  - Priority by tier (enterprise > pro > free)                   │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                    Layer Router (Worker Pool)                   │
│  ┌──────────────────────────────────────────────────┐          │
│  │  Site Profile Lookup (PostgreSQL)                │          │
│  │  ↓                                                │          │
│  │  Start Layer Selection (1, 2, 3, 4, or 5)        │          │
│  └──────────────────────────────────────────────────┘          │
└────────────────────────────┬───────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌──────────────────┐  ┌────────────────┐
│  Layer 1      │  │  Layers 2-3      │  │  Layer 5       │
│  curl_cffi    │  │  Crawlee         │  │  FlareSolverr  │
│               │  │  (HTTP/Browser)  │  │                │
│  ~50ms        │  │  ~200ms-5s       │  │  ~10-30s       │
└───────┬───────┘  └────────┬─────────┘  └───────┬────────┘
        │                   │                     │
        │          ┌────────▼─────────┐           │
        │          │  Layer 4: Proxy  │           │
        │          │  (BrightData)    │           │
        │          └────────┬─────────┘           │
        │                   │                     │
        └───────────────────┴─────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                       Storage Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ PostgreSQL   │  │ Redis        │  │ S3           │         │
│  │ (RLS + Jobs) │  │ (Cache/Rate) │  │ (Content)    │         │
│  │              │  │              │  │              │         │
│  │ tenant_id    │  │ Sliding Win  │  │ tenant_id/   │         │
│  │ RLS policies │  │ counters     │  │ job_id/      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────────────────────────────────────────┘
```

### D. Week-by-Week Checklist

**Week 5:**
- [ ] Day 1-2: Implement tenant schema and API key system
- [ ] Day 3: Add RLS policies to jobs table
- [ ] Day 4-5: Build and test rate limiting middleware
- [ ] Day 6-7: Integration testing and bug fixes

**Week 6:**
- [ ] Day 1-2: Implement quota management and usage tracking
- [ ] Day 3: Build S3 storage service
- [ ] Day 4: Integrate storage with job processing
- [ ] Day 5-7: Admin endpoints, documentation, and testing

**Week 7:**
- [ ] Day 1-2: Implement curl_cffi layer
- [ ] Day 3: Implement Crawlee HTTP/browser layers
- [ ] Day 4-5: BrightData proxy integration
- [ ] Day 6-7: Testing and optimization

**Week 8:**
- [ ] Day 1-2: FlareSolverr integration
- [ ] Day 3-4: Build intelligent layer router
- [ ] Day 5: Site profiles and learning system
- [ ] Day 6-7: End-to-end testing, documentation, and launch prep

---

## Conclusion

This iteration plan provides a comprehensive roadmap for Weeks 5-8, transforming the basic scraping API into a production-ready, multi-tenant platform with sophisticated anti-detection capabilities.

**Key Deliverables:**
- ✅ Secure multi-tenant architecture with PostgreSQL RLS
- ✅ Rate limiting and quota management for billing
- ✅ 5-layer anti-detection system with automatic escalation
- ✅ Intelligent routing that learns optimal strategies
- ✅ S3 storage with tenant isolation
- ✅ Comprehensive observability and error handling

**Success Criteria:**
- Tenant data is 100% isolated (zero cross-tenant leaks)
- Platform handles 1000+ requests/minute with <5% error rate
- Average cost per scrape: <$0.01
- Site profile accuracy: >80% (optimal layer selection)
- Ready for beta customer onboarding

**Next Steps:**
After completing Week 8, the platform will be ready for:
- Week 9-10: Production hardening (monitoring, load testing)
- Week 11-12: Beta launch with first paying customers
- Month 4+: Feature expansion (scheduling, webhooks, UI dashboard)

This plan balances ambitious technical goals with pragmatic risk management, ensuring the 1-3 person team can deliver a high-quality platform on schedule.

---

**Document Version:** 1.0
**Last Updated:** 2026-02-02
**Total Pages:** 50+
**Prepared For:** Crawlee Migration Project
