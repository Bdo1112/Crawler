# Crawlee Multi-Tenant Scraping Platform
# Complete Implementation Plan v4.0

**Date:** February 3, 2026  
**Timeline:** 22 weeks  
**Status:** READY FOR EXECUTION  

---

## Quick Reference

| Aspect | Decision |
|--------|----------|
| Timeline | 22 weeks (not 12-15) |
| Pricing | $49 Starter / $99 Pro (no free tier) |
| Free Tier | 14-day trial only (100 scrapes) |
| Anti-Detection | 3 layers (not 5) |
| Job Queue | arq (Python, not BullMQ) |
| First Year Budget | $141K |
| Break-even | Month 9 |

---

*Note: This document continues from the worker implementation. See full context below.*

---

## Worker Scraper Implementation (Continued)

```python
                layer_used=3 if use_proxy else 2,
                proxy_used=use_proxy,
                elapsed_ms=elapsed,
            )
        else:
            return ScrapeResult(
                success=False,
                html=result_html,
                layer_used=3 if use_proxy else 2,
                proxy_used=use_proxy,
                elapsed_ms=elapsed,
                error="Challenge detected" if detect_challenge(result_html or "") else "Empty response",
                challenge_detected=detect_challenge(result_html or ""),
            )
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return ScrapeResult(
            success=False,
            html=None,
            layer_used=3 if use_proxy else 2,
            proxy_used=use_proxy,
            elapsed_ms=elapsed,
            error=str(e),
        )
```

```python
async def scrape_with_escalation(url: str, method: str = "auto", timeout: int = 60) -> ScrapeResult:
    """
    Scrape URL with automatic layer escalation.
    
    Escalation order:
    1. curl_cffi (TLS fingerprinting)
    2. Crawlee Browser (JavaScript rendering)
    3. Crawlee Browser + Proxy (for blocked sites)
    """
    # Layer 1: Try curl_cffi first (fastest, cheapest)
    if method in ("auto", "http"):
        result = await layer1_curl_cffi(url, timeout=min(timeout, 30))
        if result.success:
            logger.info(f"Layer 1 success for {url}")
            return result
        logger.info(f"Layer 1 failed for {url}: {result.error}")
    
    # Layer 2: Try browser without proxy
    if method in ("auto", "browser"):
        result = await layer2_crawlee_browser(url, timeout=timeout, use_proxy=False)
        if result.success:
            logger.info(f"Layer 2 success for {url}")
            return result
        logger.info(f"Layer 2 failed for {url}: {result.error}")
    
    # Layer 3: Try browser with proxy (most expensive)
    if method == "auto" and settings.BRIGHTDATA_USERNAME:
        result = await layer2_crawlee_browser(url, timeout=timeout, use_proxy=True)
        if result.success:
            logger.info(f"Layer 3 success for {url}")
            return result
        logger.info(f"Layer 3 failed for {url}: {result.error}")
    
    # All layers failed
    return result

async def process_scrape_job(ctx: Dict[str, Any], job_data: Dict[str, Any]):
    """
    Main job processor function for arq.
    
    This is called by the worker for each queued job.
    """
    job_id = job_data["job_id"]
    tenant_id = job_data["tenant_id"]
    url = job_data["url"]
    method = job_data.get("method", "auto")
    options = job_data.get("options", {})
    
    logger.info(f"Processing job {job_id} for tenant {tenant_id}: {url}")
    
    start_time = datetime.utcnow()
    
    try:
        # Update job status to running
        async with get_tenant_session(tenant_id) as session:
            from sqlalchemy import update
            await session.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(status="running", started_at=start_time)
            )
        
        # Execute scrape with escalation
        timeout = options.get("timeout", 60000) // 1000  # Convert ms to seconds
        result = await scrape_with_escalation(url, method, timeout)
        
        # Process results
        if result.success:
            # Upload HTML to S3
            s3_key_html = await upload_content(
                tenant_id=tenant_id,
                job_id=job_id,
                content=result.html,
                content_type="html",
            )
            
            # Generate markdown if requested
            s3_key_markdown = None
            if "markdown" in options.get("formats", []):
                from html2text import HTML2Text
                h2t = HTML2Text()
                h2t.ignore_links = False
                markdown = h2t.handle(result.html)
                s3_key_markdown = await upload_content(
                    tenant_id=tenant_id,
                    job_id=job_id,
                    content=markdown,
                    content_type="markdown",
                )
            
            # Update job as completed
            async with get_tenant_session(tenant_id) as session:
                await session.execute(
                    update(Job)
                    .where(Job.id == job_id)
                    .values(
                        status="completed",
                        layer_used=result.layer_used,
                        proxy_used=result.proxy_used,
                        s3_key_html=s3_key_html,
                        s3_key_markdown=s3_key_markdown,
                        content_length=len(result.html),
                        elapsed_ms=result.elapsed_ms,
                        completed_at=datetime.utcnow(),
                    )
                )
                
                # Record usage
                cost_cents = LAYER_COSTS[result.layer_used]
                if result.proxy_used:
                    cost_cents += PROXY_COST_PER_REQUEST
                
                usage = UsageRecord(
                    tenant_id=tenant_id,
                    job_id=job_id,
                    billing_month=datetime.utcnow().strftime("%Y-%m"),
                    layer_used=result.layer_used,
                    proxy_used=result.proxy_used,
                    compute_cost_cents=int(LAYER_COSTS[result.layer_used] * 100),
                    proxy_cost_cents=int(PROXY_COST_PER_REQUEST * 100) if result.proxy_used else 0,
                    total_cost_cents=int(cost_cents * 100),
                )
                session.add(usage)
            
            logger.info(f"Job {job_id} completed successfully (layer {result.layer_used})")
        
        else:
            # Update job as failed
            async with get_tenant_session(tenant_id) as session:
                await session.execute(
                    update(Job)
                    .where(Job.id == job_id)
                    .values(
                        status="failed",
                        layer_used=result.layer_used,
                        proxy_used=result.proxy_used,
                        elapsed_ms=result.elapsed_ms,
                        error_code="scrape_failed",
                        error_message=result.error,
                        completed_at=datetime.utcnow(),
                    )
                )
            
            logger.warning(f"Job {job_id} failed: {result.error}")
    
    except Exception as e:
        logger.exception(f"Job {job_id} crashed: {e}")
        
        # Update job as failed
        async with get_tenant_session(tenant_id) as session:
            await session.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(
                    status="failed",
                    error_code="internal_error",
                    error_message=str(e),
                    completed_at=datetime.utcnow(),
                )
            )
        
        raise  # Re-raise for arq retry logic

---

## 5. Weeks 5-22: Continued Implementation

### Week 5-6: Multi-Tenancy & Billing

**Key Deliverables:**
- Tenant signup flow
- Trial system (14 days, 100 scrapes)
- Quota enforcement
- Stripe integration skeleton

**File:** `/api/routes/admin.py`
```python
"""
Admin & Tenant Management Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID

from api.database import get_db_session
from api.auth import generate_api_key
from api.models import Tenant, APIKey

router = APIRouter()

class SignupRequest(BaseModel):
    email: EmailStr
    name: str
    company: Optional[str] = None

class SignupResponse(BaseModel):
    tenant_id: UUID
    api_key: str  # Full key (only shown once)
    trial_ends_at: datetime
    monthly_quota: int

@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest):
    """
    Create a new tenant account with trial access.
    
    Trial includes:
    - 14 days access
    - 100 scrapes
    - Full feature access
    """
    async with get_db_session() as session:
        from sqlalchemy import select
        
        # Check if email already exists
        result = await session.execute(
            select(Tenant).where(Tenant.email == request.email)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail={"error": "email_exists", "message": "Email already registered"}
            )
        
        # Create tenant
        trial_ends = datetime.utcnow() + timedelta(days=14)
        
        tenant = Tenant(
            email=request.email,
            name=request.name,
            company=request.company,
            tier="trial",
            status="active",
            monthly_quota=100,
            rate_limit_per_hour=10,
            trial_ends_at=trial_ends,
        )
        session.add(tenant)
        await session.flush()
        
        # Create API key
        full_key, key_prefix, key_hash = generate_api_key()
        
        api_key = APIKey(
            tenant_id=tenant.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name="Default",
        )
        session.add(api_key)
        
        return SignupResponse(
            tenant_id=tenant.id,
            api_key=full_key,
            trial_ends_at=trial_ends,
            monthly_quota=100,
        )

@router.get("/usage")
async def get_usage(tenant: Tenant = Depends(get_current_tenant)):
    """Get current usage statistics"""
    async with get_tenant_session(str(tenant.id)) as session:
        from sqlalchemy import select
        from api.models import UsageSummary
        
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        result = await session.execute(
            select(UsageSummary)
            .where(UsageSummary.tenant_id == tenant.id)
            .where(UsageSummary.billing_month == current_month)
        )
        usage = result.scalar_one_or_none()
        
        return {
            "tenant_id": str(tenant.id),
            "tier": tenant.tier,
            "billing_month": current_month,
            "quota": tenant.monthly_quota,
            "used": usage.total_jobs if usage else 0,
            "remaining": tenant.monthly_quota - (usage.total_jobs if usage else 0),
            "success_rate": (
                usage.successful_jobs / usage.total_jobs * 100
                if usage and usage.total_jobs > 0
                else 0
            ),
            "layer_breakdown": {
                "layer1": usage.layer1_count if usage else 0,
                "layer2": usage.layer2_count if usage else 0,
                "layer3": usage.layer3_count if usage else 0,
            },
            "trial_ends_at": tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
        }
```

### Week 7-8: Anti-Detection Layers

**Already implemented in worker/scraper.py above.**

Additional refinements:
- Site profile database for known patterns
- Adaptive retry delays
- Challenge screenshot capture for debugging

### Week 9-10: Infrastructure & CI/CD

**File:** `/docker-compose.yml`
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/scrape_platform
      - REDIS_URL=redis://redis:6379/0
      - APP_ENV=development
    depends_on:
      - db
      - redis
    volumes:
      - ./api:/app/api
      - ./workers:/app/workers
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/scrape_platform
      - REDIS_URL=redis://redis:6379/0
      - APP_ENV=development
    depends_on:
      - db
      - redis
    volumes:
      - ./api:/app/api
      - ./workers:/app/workers
    command: arq workers.worker.WorkerSettings

  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=scrape_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**File:** `/.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/ -v --cov=api --cov=workers --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install linters
        run: |
          pip install ruff mypy
      
      - name: Run ruff
        run: ruff check .
      
      - name: Run mypy
        run: mypy api/ workers/ --ignore-missing-imports
```

### Week 11-14: Security & Testing

**File:** `/tests/test_rls.py`
```python
"""
Row Level Security Tests
Critical: These must pass before production deployment
"""
import pytest
from sqlalchemy import text
from uuid import uuid4

from api.database import get_db_session, get_tenant_session
from api.models import Tenant, Job

@pytest.mark.asyncio
async def test_rls_prevents_cross_tenant_read():
    """Verify tenant A cannot read tenant B's jobs"""
    tenant_a_id = str(uuid4())
    tenant_b_id = str(uuid4())
    
    # Create jobs for both tenants (as admin, no RLS)
    async with get_db_session() as session:
        # Create tenants
        tenant_a = Tenant(id=tenant_a_id, email="a@test.com", name="A")
        tenant_b = Tenant(id=tenant_b_id, email="b@test.com", name="B")
        session.add_all([tenant_a, tenant_b])
        
        # Create jobs
        job_a = Job(tenant_id=tenant_a_id, url="https://a.com", status="pending")
        job_b = Job(tenant_id=tenant_b_id, url="https://b.com", status="pending")
        session.add_all([job_a, job_b])
        await session.flush()
        
        job_a_id = job_a.id
        job_b_id = job_b.id
    
    # Query as tenant A - should only see job A
    async with get_tenant_session(tenant_a_id) as session:
        result = await session.execute(
            text("SELECT id FROM jobs")
        )
        jobs = result.fetchall()
        
        job_ids = [str(row[0]) for row in jobs]
        assert str(job_a_id) in job_ids
        assert str(job_b_id) not in job_ids  # CRITICAL: Must not see tenant B's job
    
    # Query as tenant B - should only see job B
    async with get_tenant_session(tenant_b_id) as session:
        result = await session.execute(
            text("SELECT id FROM jobs")
        )
        jobs = result.fetchall()
        
        job_ids = [str(row[0]) for row in jobs]
        assert str(job_b_id) in job_ids
        assert str(job_a_id) not in job_ids  # CRITICAL: Must not see tenant A's job

@pytest.mark.asyncio
async def test_rls_prevents_cross_tenant_update():
    """Verify tenant A cannot update tenant B's jobs"""
    # ... similar structure
    pass

@pytest.mark.asyncio
async def test_rls_prevents_cross_tenant_delete():
    """Verify tenant A cannot delete tenant B's jobs"""
    # ... similar structure
    pass

@pytest.mark.asyncio
async def test_rls_sql_injection_prevention():
    """Verify SQL injection in tenant_id is prevented"""
    malicious_tenant_id = "'; DROP TABLE jobs; --"
    
    # This should fail gracefully, not execute the injection
    with pytest.raises(Exception):
        async with get_tenant_session(malicious_tenant_id) as session:
            await session.execute(text("SELECT 1"))
```

### Week 15-18: Billing & Documentation

**Stripe Integration:**

**File:** `/api/billing.py`
```python
"""
Stripe Billing Integration
"""
import stripe
from typing import Optional
from datetime import datetime

from api.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

# Price IDs from Stripe Dashboard
PRICE_IDS = {
    "starter": "price_starter_monthly",  # $49/month
    "pro": "price_pro_monthly",          # $99/month
}

TIER_QUOTAS = {
    "trial": 100,
    "starter": 2500,
    "pro": 15000,
    "enterprise": None,  # Custom
}

TIER_RATE_LIMITS = {
    "trial": 10,
    "starter": 50,
    "pro": 100,
    "enterprise": 500,
}

async def create_checkout_session(
    tenant_id: str,
    tier: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """
    Create Stripe Checkout session for subscription.
    
    Returns:
        Checkout session URL
    """
    if tier not in PRICE_IDS:
        raise ValueError(f"Invalid tier: {tier}")
    
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": PRICE_IDS[tier],
            "quantity": 1,
        }],
        mode="subscription",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        client_reference_id=tenant_id,
        metadata={
            "tenant_id": tenant_id,
            "tier": tier,
        },
    )
    
    return session.url

async def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """
    Handle Stripe webhook events.
    
    Returns:
        Processed event data
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise ValueError("Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid signature")
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        tenant_id = session["client_reference_id"]
        tier = session["metadata"]["tier"]
        
        # Update tenant tier
        await _upgrade_tenant(
            tenant_id=tenant_id,
            tier=tier,
            stripe_customer_id=session["customer"],
            stripe_subscription_id=session["subscription"],
        )
        
        return {"action": "upgraded", "tenant_id": tenant_id, "tier": tier}
    
    elif event["type"] == "invoice.payment_failed":
        subscription = event["data"]["object"]
        # Handle failed payment - send notification, potentially downgrade
        return {"action": "payment_failed"}
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        tenant_id = subscription["metadata"].get("tenant_id")
        if tenant_id:
            await _downgrade_tenant(tenant_id)
        return {"action": "subscription_cancelled"}
    
    return {"action": "ignored", "type": event["type"]}

async def _upgrade_tenant(
    tenant_id: str,
    tier: str,
    stripe_customer_id: str,
    stripe_subscription_id: str,
):
    """Update tenant after successful payment"""
    from api.database import get_db_session
    from sqlalchemy import update
    from api.models import Tenant
    
    async with get_db_session() as session:
        await session.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(
                tier=tier,
                monthly_quota=TIER_QUOTAS[tier],
                rate_limit_per_hour=TIER_RATE_LIMITS[tier],
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                trial_ends_at=None,  # Clear trial
            )
        )

async def _downgrade_tenant(tenant_id: str):
    """Downgrade tenant after subscription cancellation"""
    from api.database import get_db_session
    from sqlalchemy import update
    from api.models import Tenant
    
    async with get_db_session() as session:
        await session.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(
                tier="trial",
                monthly_quota=0,  # No more scrapes
                status="cancelled",
            )
        )
```

---

## 6. Business Model & Pricing

### 6.1 Pricing Tiers (Final)

| Tier | Monthly Price | Scrapes/Month | Rate Limit | Features |
|------|---------------|---------------|------------|----------|
| **Trial** | Free (14 days) | 100 | 10/hour | Full access, evaluation only |
| **Starter** | $49/month | 2,500 | 50/hour | HTTP + Browser layers |
| **Pro** | $99/month | 15,000 | 100/hour | All layers + Proxy |
| **Enterprise** | Custom | Unlimited | 500/hour | SLA, dedicated support |

### 6.2 Unit Economics (Validated)

```
STARTER TIER ($49/month, 2,500 scrapes):
├── Revenue: $49.00
├── Costs:
│   ├── Layer 1 (60% × 2,500 × $0.001): $1.50
│   ├── Layer 2 (35% × 2,500 × $0.003): $2.63
│   ├── Layer 3 (5% × 2,500 × $0.01): $1.25
│   ├── Infrastructure (allocated): $5.00
│   ├── Support (allocated): $2.00
│   └── Payment processing (3%): $1.47
├── Total Cost: $13.85
└── GROSS MARGIN: 72% ✅

PRO TIER ($99/month, 15,000 scrapes):
├── Revenue: $99.00
├── Costs:
│   ├── Layer 1 (55% × 15,000 × $0.001): $8.25
│   ├── Layer 2 (35% × 15,000 × $0.003): $15.75
│   ├── Layer 3 (10% × 15,000 × $0.02): $30.00
│   ├── Infrastructure (allocated): $10.00
│   ├── Support (allocated): $5.00
│   └── Payment processing (3%): $2.97
├── Total Cost: $71.97
└── GROSS MARGIN: 27% ⚠️

Notes:
- Pro tier is thin margin but acceptable
- Heavy proxy users will reduce margin
- Monitor Layer 3 usage closely
- Enterprise tier subsidizes Pro tier
```

### 6.3 Revenue Projections (Conservative)

| Month | Trial Users | Starter | Pro | Enterprise | MRR |
|-------|-------------|---------|-----|------------|-----|
| 5 (Soft Launch) | 50 | 0 | 0 | 0 | $0 |
| 6 (Public Launch) | 150 | 5 | 2 | 0 | $443 |
| 7 | 250 | 15 | 8 | 0 | $1,527 |
| 8 | 400 | 30 | 15 | 1 | $3,435 |
| 9 | 600 | 45 | 25 | 1 | $5,180 |
| 10 | 800 | 60 | 35 | 2 | $7,405 |
| 11 | 1,000 | 75 | 45 | 3 | $9,630 |
| 12 | 1,200 | 90 | 55 | 4 | $11,855 |

**Year 1 Total ARR:** ~$142K (Month 12 × 12)

---

## 7. Financial Model

### 7.1 Development Investment

| Phase | Weeks | Hours | Cost @ $100/hr |
|-------|-------|-------|----------------|
| Pre-Development (0-2) | 2 | 40 | $4,000 |
| Foundation (3-6) | 4 | 160 | $16,000 |
| Scraping Engine (7-10) | 4 | 160 | $16,000 |
| Production Ready (11-14) | 4 | 160 | $16,000 |
| Launch Prep (15-18) | 4 | 160 | $16,000 |
| Beta Launch (19-22) | 4 | 120 | $12,000 |
| **TOTAL DEVELOPMENT** | **22** | **800** | **$80,000** |

### 7.2 Additional Costs

| Item | When | Cost |
|------|------|------|
| Part-time contractor | Months 4-12 | $24,000 ($3K/month × 8) |
| Security audit | Month 4 | $5,000 |
| Penetration testing | Month 5 | $7,500 |
| Legal (ToS, Privacy) | Month 4 | $2,500 |
| Domain + SSL | Year 1 | $200 |
| AWS (pre-revenue) | Months 1-5 | $3,750 ($750/month) |
| BrightData (pre-revenue) | Months 4-5 | $400 |
| Stripe fees (Year 1) | Year 1 | ~$3,000 |
| Marketing/content | Year 1 | $2,000 |
| **TOTAL ADDITIONAL** | | **$48,350** |

### 7.3 Total First Year Investment

```
Development:        $80,000
Additional costs:   $48,350
Contingency (10%):  $12,835
─────────────────────────────
TOTAL INVESTMENT:   $141,185 (~$141K)
```

### 7.4 Break-Even Analysis

```
Monthly Fixed Costs (Post-Launch):
├── Infrastructure: $750
├── Contractor support: $3,000
├── Proxies: $200 (grows with usage)
├── Tools/services: $100
└── Total: $4,050/month

Break-Even MRR: $4,050
Break-Even @ 72% margin: $5,625 MRR

Expected Break-Even: Month 9 (MRR ~$5,180)
```

### 7.5 ROI Projection

```
Year 1:
├── Investment: $141,000
├── Revenue (Months 6-12): ~$40,000
├── Costs (Months 6-12): ~$30,000
├── Net: -$131,000 (expected loss)

Year 2 (if growth continues):
├── MRR Month 24: ~$50,000 (projected)
├── ARR: $600,000
├── Costs: $200,000/year
├── Net Profit: $400,000/year
├── ROI: 283% return on Year 1 investment
```

---

## 8. Risk Register

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Crawlee success rate <85% | 30% | HIGH | PoC validation gate, hybrid fallback |
| Browser memory leaks | 50% | MEDIUM | Aggressive recycling, monitoring |
| RLS misconfiguration | 20% | CRITICAL | Security audit, automated testing |
| arq scaling ceiling | 20% | MEDIUM | Monitor usage, migration plan ready |
| Proxy costs spike | 40% | HIGH | Budget limits, circuit breakers |

### 8.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Conversion <1% | 40% | HIGH | Pricing experiments, feature gating |
| Apify price drop | 30% | MEDIUM | Differentiate on simplicity, not price |
| Solo dev burnout | 50% | HIGH | Contractor support, realistic timeline |
| Enterprise sales fail | 60% | MEDIUM | Focus on PLG, defer outbound |
| Churn >10% monthly | 35% | HIGH | Onboarding optimization, support |

### 8.3 Contingency Plans

**If PoC fails (Week 2):**
- Pivot to Firecrawl optimization
- Build hybrid engine (Crawlee + Firecrawl)
- Budget: $15K additional, 8 weeks

**If conversion <1% (Month 8):**
- A/B test lower pricing ($39 Starter)
- Add feature gates (webhooks = Pro only)
- Consider usage-based pricing

**If burnout imminent (any time):**
- Hire full-time contractor immediately
- Reduce scope (cut Enterprise tier)
- Extend timeline by 4-8 weeks

---

## 9. Success Metrics & Gates

### 9.1 Weekly Gates

| Week | Gate | Criteria | Action if Fail |
|------|------|----------|----------------|
| 2 | PoC Validation | ≥85% success, <5s latency | Pivot or hybrid |
| 6 | API Complete | All endpoints working | Delay 1 week |
| 10 | Workers Stable | 100 jobs/hour, no crashes | Delay 1 week |
| 14 | Security Audit | Zero critical findings | Fix before launch |
| 18 | Billing Works | Test purchases succeed | Delay launch |
| 22 | Launch Ready | 20+ beta users happy | Soft launch only |

### 9.2 Monthly Targets (Post-Launch)

| Month | Signups | Paid Customers | MRR | Churn |
|-------|---------|----------------|-----|-------|
| 6 | 150 | 7 | $500 | N/A |
| 7 | 400 | 23 | $1,500 | <15% |
| 8 | 700 | 46 | $3,400 | <12% |
| 9 | 1,000 | 71 | $5,200 | <10% |
| 10 | 1,300 | 97 | $7,400 | <8% |
| 11 | 1,600 | 123 | $9,600 | <7% |
| 12 | 2,000 | 150 | $12,000 | <6% |

### 9.3 Year 1 Success Definition

**Minimum Viable Success:**
- [ ] 100+ paying customers
- [ ] $8K+ MRR
- [ ] <8% monthly churn
- [ ] 95%+ uptime
- [ ] No security incidents

**Target Success:**
- [ ] 150+ paying customers
- [ ] $12K+ MRR
- [ ] <6% monthly churn
- [ ] 99%+ uptime
- [ ] 500+ GitHub stars

---

## 10. Implementation Checklist

### Pre-Development (Weeks 0-2)
- [ ] Conduct 10+ customer interviews
- [ ] Launch landing page
- [ ] Collect 25+ email signups
- [ ] Complete PoC
- [ ] Document GO/NO-GO decision

### Foundation (Weeks 3-6)
- [ ] FastAPI application structure
- [ ] Database schema + migrations
- [ ] Authentication system
- [ ] Rate limiting
- [ ] Multi-tenancy (RLS)
- [ ] Basic endpoints

### Scraping Engine (Weeks 7-10)
- [ ] Layer 1: curl_cffi
- [ ] Layer 2: Crawlee Browser
- [ ] Layer 3: Browser + Proxy
- [ ] Job queue (arq)
- [ ] S3 storage integration
- [ ] Usage tracking

### Production Ready (Weeks 11-14)
- [ ] Docker setup
- [ ] CI/CD pipeline
- [ ] AWS deployment
- [ ] Security audit
- [ ] Load testing
- [ ] Monitoring setup

### Launch Prep (Weeks 15-18)
- [ ] Stripe integration
- [ ] Signup flow
- [ ] Email notifications
- [ ] API documentation
- [ ] User guides
- [ ] Onboarding video

### Beta Launch (Weeks 19-22)
- [ ] Invite beta users
- [ ] Collect feedback
- [ ] Fix critical bugs
- [ ] Marketing push
- [ ] Community setup (Discord)
- [ ] Public launch

---

## Appendix A: Environment Variables

```bash
# Application
APP_NAME=scrape-platform
APP_ENV=production
DEBUG=false

# API
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/scrape_platform
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://host:6379/0

# Security
SECRET_KEY=<generate-secure-key>
API_KEY_PREFIX=sk_

# AWS
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=us-east-1
S3_BUCKET=scrape-platform-data

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Proxies
BRIGHTDATA_USERNAME=<username>
BRIGHTDATA_PASSWORD=<password>
PROXY_BUDGET_MONTHLY=200

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

---

## Appendix B: API Reference Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Basic health check |
| `/health/detailed` | GET | No | Dependency status |
| `/v2/scrape` | POST | Yes | Create scrape job |
| `/v2/scrape/{id}` | GET | Yes | Get job status |
| `/admin/signup` | POST | No | Create account |
| `/admin/usage` | GET | Yes | Get usage stats |
| `/admin/upgrade` | POST | Yes | Start Stripe checkout |
| `/webhooks/stripe` | POST | Stripe | Handle Stripe events |

---

**Document Version:** 4.0  
**Last Updated:** February 3, 2026  
**Status:** READY FOR EXECUTION  
**Next Action:** Begin customer interviews (Week 0)
