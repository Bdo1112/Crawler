# Crawlee Multi-Tenant Scraping Platform: Comprehensive Implementation Plan

**Date:** 2026-02-03
**Project:** Phase 2 Migration - Firecrawl to Crawlee-based Platform
**Timeline:** 14-15 weeks (adjusted from 12 weeks)
**Team:** Solo developer (full-time)
**Status:** APPROVED WITH CRITICAL ADJUSTMENTS ✅⚠️

---

## Executive Summary

This plan details the migration from the current Firecrawl-based system (Phase 1) to a production-ready Crawlee-based multi-tenant SaaS platform. Based on comprehensive product and architectural reviews, **the project is viable but requires 8 mandatory changes** to avoid critical failures.

### Success Probability
- **Original plan**: 55-60%
- **With adjustments**: 75-80%

### Key Adjustments from Reviews

| Area | Original Plan | Adjusted Plan | Rationale |
|------|---------------|---------------|-----------|
| **Timeline** | 12 weeks | **14-15 weeks** | Realistic buffer for multi-tenancy security |
| **Budget** | $68K | **$106K** | Includes support hire ($32K) + security audit ($6K) |
| **Pro Pricing** | $50/month | **$75/month** | Fixes underwater unit economics (50% margin) |
| **Free Tier** | 1,000 scrapes | **500 scrapes** | Reduces cost per free user from $1.64 → $0.82 |
| **Job Queue** | arq | **BullMQ** | Prevents Month 18 ceiling crisis ($20K migration) |
| **Security Audit** | Month 9 | **Week 6** | Prevents breach risk before production data |
| **PoC Test Sites** | 20 sites | **50 sites** | Thorough validation before commitment |
| **Month 6 Target** | 500 signups | **150 signups** | Realistic organic growth |

### Critical Success Factors

**Week 2 PoC Gate (GO/NO-GO):**
- ✅ ≥90% success rate across **50 representative sites** (not 20)
- ✅ P99 latency ≤2x Firecrawl (<60s)
- ✅ Code complexity <500 LoC (simpler than current scraper.py)
- ✅ Team confidence: High

**IF PoC FAILS**: Pivot to Firecrawl optimization or hybrid model.

---

## Table of Contents

1. [Critical Adjustments & Risk Mitigations](#1-critical-adjustments--risk-mitigations)
2. [Project Overview & Context](#2-project-overview--context)
3. [Technical Architecture](#3-technical-architecture)
4. [Implementation Timeline](#4-implementation-timeline)
5. [Week-by-Week Breakdown](#5-week-by-week-breakdown)
6. [Code Examples & Templates](#6-code-examples--templates)
7. [Testing Strategy](#7-testing-strategy)
8. [Operational Playbook](#8-operational-playbook)
9. [Financial Model (Adjusted)](#9-financial-model-adjusted)
10. [Success Metrics & Gates](#10-success-metrics--gates)

---

## 1. Critical Adjustments & Risk Mitigations

### 🔴 MANDATORY Changes (Before Production)

Based on architect and product manager reviews, these **8 changes are non-negotiable**:

#### 1.1 Security Audit (Week 6, not Month 9)

**Problem:** Data breach before audit = catastrophic ($100K-1M cost)
**Solution:** External security audit in Week 6 (before production data)

**Implementation:**
- **Cost:** $5K security audit + $7.5K penetration test = $12.5K
- **Timeline:** Week 6 (after multi-tenancy complete)
- **Vendor:** Hire via Upwork/BugCrowd
- **Scope:** RLS policies, SQL injection, authentication, tenant isolation

**Acceptance Criteria:**
- [ ] Zero critical or high-severity findings
- [ ] RLS policies validated by independent auditor
- [ ] SQL injection testing passed (100+ payloads)
- [ ] Timing attack tests passed

---

#### 1.2 Fix Unit Economics (Pricing Adjustment)

**Problem:** Pro tier has -2% margin (underwater), free tier loses $1.64/month per user

**Solution A (RECOMMENDED):** Increase Pro pricing to $75/month
```
Pro Tier ($75/month, 10K scrapes):
- Revenue: $75/month
- Cost: $37.50/month (50% browser usage assumption)
- Margin: $37.50 (50% gross margin) ✅

Break-even: 30 Pro customers (Month 6-7) ✅
```

**Solution B (ALTERNATIVE):** Reduce free tier to 500 scrapes/month
```
Free Tier (500 scrapes/month):
- Revenue: $0
- Cost: $0.82/month (vs $1.64 for 1K scrapes)
- Loss per user: -$0.82 (acceptable as CAC)

At 500 free users: -$410/month loss (vs -$820)
```

**Solution C (HYBRID):** Both A + B
- $75/month Pro tier + 500 free scrapes
- **Best margins**: 55-60%
- **Best CAC efficiency**: 50% reduction in free tier costs

**DECISION REQUIRED:** Choose solution before Week 3 (API pricing hardcoded)

---

#### 1.3 Switch from arq to BullMQ (Job Queue)

**Problem:** arq ceiling at 1000 jobs/sec = crisis at Month 18 (10M jobs/day)
**Migration cost at scale:** $20K + 4 weeks + data loss risk

**Solution:** Use BullMQ from Day 1

**Trade-offs:**
| Aspect | arq (Original) | BullMQ (Adjusted) |
|--------|---------------|-------------------|
| Language | Python | Node.js |
| Throughput | 1,000 jobs/sec | 10,000+ jobs/sec |
| Memory | 50MB | 150MB |
| Cost | $0 | +$50/month (Node.js container) |
| Complexity | Simple | Moderate |

**RATIONALE:** +$50/month now prevents $20K crisis later = **400x ROI**

**Implementation Impact:**
- **Week 3 (Day 18):** Set up BullMQ instead of arq
- **Week 3 (Day 19):** Write Python→Node.js bridge (HTTP API)
- **Extra effort:** +1 day (Day 18-19 becomes 3 days instead of 2)

---

#### 1.4 Proxy Cost Controls (Circuit Breaker)

**Problem:** Proxy costs could spike to $5K/month (vs $382 budget) = bankruptcy

**Solution:** Multi-tier circuit breaker

```python
# /workers/layers/proxy_manager.py
PROXY_BUDGETS = {
    'free': 0,           # No proxy access
    'pro': 50,           # $50/month proxy budget
    'enterprise': None   # Unlimited
}

class ProxyCircuitBreaker:
    def check_budget(self, tenant_id: str) -> bool:
        """Reject if monthly proxy spend exceeded"""
        monthly_spend = get_proxy_spend(tenant_id)
        tier = get_tenant_tier(tenant_id)
        budget = PROXY_BUDGETS[tier]

        if budget and monthly_spend >= budget:
            log_event('proxy_budget_exceeded', tenant_id)
            return False  # Reject Layer 4-5
        return True
```

**Acceptance Criteria:**
- [ ] Platform-wide limit: $500/month (circuit breaks at $450)
- [ ] Per-tenant limit: $50/month Pro tier
- [ ] Alerts fire at 80% budget consumed
- [ ] Graceful degradation (use Layer 3 instead)

---

#### 1.5 Browser Memory Leak Prevention

**Problem:** 100 browser instances × 500MB/hour = workers crash after 8 hours

**Solution:** Aggressive browser lifecycle management

```python
# /workers/layers/browser_pool.py
BROWSER_LIMITS = {
    'max_lifetime_minutes': 30,  # Kill after 30 min (was 60s idle)
    'max_requests_per_instance': 100,  # Recycle after 100 requests
    'max_concurrent_browsers': 10,  # Pool size limit
    'idle_timeout_seconds': 30  # Close if idle 30s
}

class BrowserPool:
    def get_browser(self):
        browser = self.pool.get()
        if browser.request_count >= 100:
            browser.close()
            browser = self.launch_new()
        if (time.now() - browser.start_time) > 30 * 60:
            browser.close()
            browser = self.launch_new()
        return browser
```

**Acceptance Criteria:**
- [ ] No browser lives >30 minutes
- [ ] No browser handles >100 requests
- [ ] Memory usage stays <8GB per worker
- [ ] 1000 scrapes run without worker crash

---

#### 1.6 PostgreSQL Connection Pooling (PgBouncer)

**Problem:** 500 max connections exhausted → new connections rejected → API errors

**Solution:** PgBouncer connection pooler (10,000 → 50 connections)

```yaml
# /infra/docker-compose.yml
pgbouncer:
  image: pgbouncer/pgbouncer:1.21
  environment:
    DATABASES_HOST: postgres
    DATABASES_PORT: 5432
    PGBOUNCER_POOL_MODE: transaction
    PGBOUNCER_MAX_CLIENT_CONN: 10000
    PGBOUNCER_DEFAULT_POOL_SIZE: 50
  ports:
    - "6432:6432"  # API/Workers connect here, not postgres:5432
```

**Acceptance Criteria:**
- [ ] API connects to pgbouncer:6432 (not postgres:5432)
- [ ] 1000 concurrent API requests succeed
- [ ] Connection pool never exceeds 50
- [ ] Query latency <5ms overhead

---

#### 1.7 Async Job Pattern for Layers 4-5

**Problem:** 30s P99 latency violates UX expectations → 20-30% churn

**Solution:** Return job ID immediately for >10s requests

```python
# /api/app/routes/scrape.py
@app.post("/v2/scrape")
async def scrape(request: ScrapeRequest):
    # Always return job ID immediately (async pattern)
    job_id = create_job(request)
    enqueue_job(job_id)

    return {
        "id": job_id,
        "status": "pending",
        "status_url": f"/v2/scrape/{job_id}",
        "estimated_time": "2-30s"  # Set expectations
    }

# Client polls /v2/scrape/{job_id} for results
```

**Acceptance Criteria:**
- [ ] POST /v2/scrape returns <100ms
- [ ] All jobs async (no blocking >5s)
- [ ] Client SDK has built-in polling (5s interval)
- [ ] Webhook support for completion (optional)

---

#### 1.8 Hire Support by Month 8

**Problem:** Solo dev at 55% ops time (22 hours/week) → burnout → growth stalls

**Solution:** Part-time support engineer ($4K/month)

**Budget Impact:**
```
Original plan: $0 support costs (unrealistic)
Adjusted plan:
  - Month 8-11: $4K/month part-time (20 hours/week)
  - Month 12+: $8K/month full-time
  - First year total: +$32K support costs
```

**Responsibilities:**
- Customer support (email, Discord)
- Incident response (on-call rotation)
- Runbook maintenance
- Basic bug triage

**Hiring Timeline:**
- Week 12: Post job (Upwork, AngelList)
- Week 13: Interview 5 candidates
- Week 14: Hire and onboard
- Month 8: Support engineer operational

---

### 1.9 Updated Financial Model

**Original Document Claims:**
- First-year investment: $68K
- Break-even: Month 7
- Month 8 profit: $3,445 (69% margin)

**ADJUSTED (Realistic):**
```
First-Year Investment:
  - Development: $68K (unchanged)
  - Support: $32K (8 months × $4K)
  - Security: $6K (audit + pentest)
  Total: $106K

Break-Even: Month 10 (not Month 7)

Month 8 Reality:
  - Revenue: $5,000 MRR (80 Pro × $62.50 avg + 1 Enterprise × $1K)
  - Infrastructure: $1,155
  - Support: $4,000
  - Proxy: $1,387 (40% usage, not 20%)
  - Total costs: $6,542
  - LOSS: -$1,542 (-31% margin) ❌

Month 10 Break-Even:
  - Revenue: $10,500 MRR (150 Pro × $70 avg + 3 Enterprise × $1K)
  - Total costs: $9,842
  - Profit: $658 (6% margin) ✅
```

**ROI:** 1.7x (not 2.6x) - still viable, but less aggressive

---

## 2. Project Overview & Context

### 2.1 Why This Migration?

**Current State (Phase 1):**
- ✅ **Operational:** Firecrawl + Patchright + Tor + FlareSolverr working
- ❌ **Complex:** 7 services, 18GB RAM, 50% team time on ops
- ❌ **Cost:** $1,500-3,000/month at 300K jobs
- ❌ **Not production-ready:** Per official Firecrawl docs

**Target State (Phase 2):**
- ✅ **Simpler:** 4 services, 12GB RAM, 20% team time
- ✅ **Cheaper:** $965/month (35-50% savings)
- ✅ **Multi-tenant:** SaaS platform (not single-use tool)
- ✅ **Production-proven:** Apify runs billions of jobs on Crawlee

### 2.2 Product Vision

**Not building:** Another web scraping tool
**Building:** Multi-tenant Apify-like platform

**Target Users:**
1. **David** (Data Engineer at Series A startup) - $600 LTV
2. **Sarah** (ML Researcher, budget-constrained) - $100 LTV
3. **Alex** (CTO building internal platform) - $10K+ LTV

**Pricing Tiers (ADJUSTED):**
- **Free:** 500 scrapes/month (was 1,000)
- **Pro:** $75/month for 10K scrapes (was $50)
- **Enterprise:** Custom ($1,000-5,000+/month)

### 2.3 Market Positioning

**Phase 1 (Months 4-8):** "Open-Source Apify Alternative with Transparent Pricing"
**Differentiation:** 50% cheaper, no vendor lock-in, simpler operations

**Competitors:**
- **Apify:** $200+/month, closed-source, complex
- **Firecrawl:** API-only, custom pricing, operational burden
- **Our advantage:** Open-source + Python-native + transparent pricing

---

## 3. Technical Architecture

### 3.1 System Architecture Diagram

```
                                INTERNET
                                    |
                            [CloudFlare CDN]
                                    |
                                    v
            +=============================================+
            |         AWS ALB (Load Balancer)            |
            |         SSL Termination, Health Checks      |
            +=============================================+
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
    +=========================+     +=========================+
    |   FastAPI Gateway (×2)  |     |   FastAPI Gateway (×2)  |
    |   Port 8000             |     |   Port 8000             |
    |   Fargate: 2 vCPU, 4GB  |     |   Fargate: 2 vCPU, 4GB  |
    |                         |     |                         |
    |   Middleware Stack:     |     |   Middleware Stack:     |
    |   1. Auth (API key)     |     |   1. Auth (API key)     |
    |   2. Rate limit (Redis) |     |   2. Rate limit (Redis) |
    |   3. Quota check (PG)   |     |   3. Quota check (PG)   |
    |   4. Logging (JSON)     |     |   4. Logging (JSON)     |
    +=========================+     +=========================+
                    |                               |
                    +---------------+---------------+
                                    |
                                    v
                +=======================================+
                |         BullMQ Queue (Redis)          |
                |         Tenant-Isolated Queues        |
                |         Priority: Ent > Pro > Free    |
                +=======================================+
                                    |
        +---------------+-----------+-----------+---------------+
        |               |           |           |               |
        v               v           v           v               v
    +-------+       +-------+   +-------+   +-------+       +-------+
    |Worker |       |Worker |   |Worker |   |Worker |       |Worker |
    | (×5)  |       | (×5)  |   | (×5)  |   | (×5)  |       | (×5)  |
    |Node.js|       |Node.js|   |Node.js|   |Node.js|       |Node.js|
    +-------+       +-------+   +-------+   +-------+       +-------+
        |               |           |           |               |
        +---------------+-----------+-----------+---------------+
                                    |
                                    v
                +=======================================+
                |      5-Layer Anti-Detection           |
                |                                       |
                |  L1: curl_cffi (60% success, ~50ms)  |
                |  L2: Crawlee HTTP (70%, ~300ms)      |
                |  L3: Crawlee Browser (85%, ~3s)      |
                |  L4: Proxy + Browser (92%, ~4s)      |
                |  L5: FlareSolverr (95%, ~20s)        |
                +=======================================+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+================+     +====================+     +================+
|  PostgreSQL    |     |    Amazon S3       |     |  Redis Cache   |
|  (RDS Multi-AZ)|     |    (Content)       |     |  (Sessions)    |
|                |     |                    |     |                |
|  - Jobs        |     |  - HTML files      |     |  - Rate limits |
|  - Tenants     |     |  - Markdown        |     |  - Job state   |
|  - API keys    |     |  - Screenshots     |     |  - Config      |
|  - Usage       |     |                    |     |                |
|                |     |  Structure:        |     |  TTL: 1hr      |
|  RLS enabled   |     |  {tenant}/{job}/   |     |  (sessions)    |
+================+     +====================+     +================+
        |                           |                           |
        v                           v                           v
+================+     +====================+     +================+
|  PgBouncer     |     |    CloudWatch      |     |  Prometheus    |
|  Connection    |     |    Logs & Metrics  |     |  + Grafana     |
|  Pooler        |     |                    |     |                |
|  10K → 50      |     |  - API requests    |     |  - Dashboards  |
+================+     |  - Worker events   |     |  - Alerts      |
                       |  - Error tracking  |     |                |
                       +====================+     +================+
```

### 3.2 Data Flow

**1. Request Flow:**
```
1. Client → POST /v2/scrape {"url": "https://example.com"}
2. ALB → FastAPI Gateway (round-robin)
3. Auth Middleware → Verify API key → Resolve tenant_id
4. Rate Limit → Check Redis counter (100/hour for Free)
5. Quota Check → Query PostgreSQL (500 scrapes/month remaining?)
6. Create Job → INSERT into jobs table (status: pending)
7. Enqueue → BullMQ with priority (Enterprise=1, Pro=2, Free=3)
8. Response → {"id": "job_123", "status": "pending"}
```

**2. Processing Flow:**
```
1. Worker → Dequeue from BullMQ (highest priority first)
2. Update Status → jobs.status = 'running'
3. Layer Selection → Start with Layer 1 (curl_cffi)
4. Execute → Scrape with TLS fingerprinting
5. Challenge Detection → Check for Cloudflare/PerimeterX/DataDome
6. Escalate if needed → Layer 1 → 2 → 3 → 4 → 5
7. Store Results → Upload HTML/Markdown to S3
8. Update Job → status = 'completed', s3_key = '{tenant}/{job}/content.html'
9. Track Usage → INSERT into usage_records (layer_used, cost_cents)
```

**3. Polling Flow:**
```
1. Client → GET /v2/scrape/{job_id} (poll every 5s)
2. Auth → Verify tenant owns this job (RLS)
3. Query → SELECT status, s3_key FROM jobs WHERE id = $1
4. If completed → Generate presigned S3 URL (1hr expiry)
5. Response → {
     "status": "completed",
     "data": {
       "html_url": "https://s3.../content.html?sig=...",
       "markdown_url": "https://s3.../content.md?sig=...",
       "metadata": {"layer_used": 3, "elapsed_ms": 2800}
     }
   }
```

### 3.3 Database Schema

```sql
-- /db/migrations/001_initial_schema.sql

-- 1. Tenants table
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  tier VARCHAR(20) DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'enterprise')),
  monthly_quota INTEGER DEFAULT 500,  -- Adjusted from 1000
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_tenants_email ON tenants(email);
CREATE INDEX idx_tenants_tier ON tenants(tier);

-- 2. API Keys table
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  key_hash VARCHAR(255) UNIQUE NOT NULL,  -- bcrypt hash
  key_prefix VARCHAR(20) NOT NULL,  -- fc_live_xxx (for UI display)
  name VARCHAR(255),  -- "Production", "Development"
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
  last_used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);  -- Auth lookup

-- 3. Jobs table (RLS enabled)
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  url VARCHAR(2048) NOT NULL,
  method VARCHAR(20) DEFAULT 'auto' CHECK (method IN ('http', 'browser', 'auto')),
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  layer_used INTEGER,  -- Which layer succeeded (1-5)
  s3_key_html VARCHAR(512),  -- S3 path: {tenant_id}/{job_id}/content.html
  s3_key_markdown VARCHAR(512),
  error_message TEXT,
  elapsed_ms INTEGER,
  created_at TIMESTAMP DEFAULT now(),
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE INDEX idx_jobs_tenant ON jobs(tenant_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created ON jobs(created_at DESC);

-- Row-Level Security for jobs
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_jobs ON jobs
  USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- 4. Usage tracking
CREATE TABLE usage_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  layer_used INTEGER NOT NULL,
  proxy_used BOOLEAN DEFAULT false,
  cost_cents INTEGER DEFAULT 0,  -- Cost in cents (1 cent = $0.01)
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_usage_tenant_date ON usage_records(tenant_id, created_at DESC);

-- Materialized view for monthly usage summary
CREATE MATERIALIZED VIEW usage_summary AS
SELECT
  tenant_id,
  DATE_TRUNC('month', created_at) AS month,
  COUNT(*) AS total_scrapes,
  SUM(cost_cents) AS total_cost_cents,
  AVG(CASE WHEN layer_used = 1 THEN 1 ELSE 0 END) AS layer1_pct,
  AVG(CASE WHEN layer_used = 2 THEN 1 ELSE 0 END) AS layer2_pct,
  AVG(CASE WHEN layer_used = 3 THEN 1 ELSE 0 END) AS layer3_pct,
  AVG(CASE WHEN layer_used >= 4 THEN 1 ELSE 0 END) AS proxy_pct
FROM usage_records
GROUP BY tenant_id, DATE_TRUNC('month', created_at);

CREATE UNIQUE INDEX idx_usage_summary_tenant_month ON usage_summary(tenant_id, month);

-- Refresh materialized view every hour
CREATE OR REPLACE FUNCTION refresh_usage_summary()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY usage_summary;
END;
$$ LANGUAGE plpgsql;

-- 5. Site profiles (for layer selection optimization)
CREATE TABLE site_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  domain VARCHAR(255) UNIQUE NOT NULL,
  start_layer INTEGER DEFAULT 1,  -- Which layer to try first
  success_rate_layer1 DECIMAL(5,2),
  success_rate_layer2 DECIMAL(5,2),
  success_rate_layer3 DECIMAL(5,2),
  last_updated TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_site_profiles_domain ON site_profiles(domain);
```

### 3.4 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **API Framework** | FastAPI (Python 3.11+) | 2x faster than Express, auto-generated OpenAPI docs |
| **Job Queue** | **BullMQ** (Node.js) | 10,000+ jobs/sec, prevents arq ceiling |
| **Scraping Engine** | Crawlee (Python) | Apify-proven, 60% simpler than Firecrawl |
| **Database** | PostgreSQL 16 + RLS | Multi-tenant isolation, ACID guarantees |
| **Connection Pool** | PgBouncer | 10K→50 connection pooling |
| **Cache** | Redis 7 | Rate limits, sessions, job state |
| **Storage** | Amazon S3 | 80% cheaper than JSONB, 30-day lifecycle |
| **Compute** | AWS Fargate | 3.5x cheaper than EC2 (with ops time) |
| **Monitoring** | Prometheus + Grafana | Self-hosted, flexible dashboards |
| **Logging** | CloudWatch Logs | Managed, searchable, retention |
| **Proxies** | BrightData (residential) | 99.9% uptime, global coverage |

---

## 4. Implementation Timeline

### 4.1 Overview (14-15 Weeks)

```
Weeks 1-3:  PoC Validation (Extended from 2 weeks)
Weeks 4-7:  API Layer (Extended from Weeks 3-4)
Weeks 8-10: Multi-Tenancy + Security (Extended from Weeks 5-6)
Weeks 11-12: Anti-Detection (Same as original Weeks 7-8)
Weeks 13-14: Monitoring + Observability (Same as Weeks 9-10)
Week 15:    Hardening, Documentation, Launch Prep (Compressed from Weeks 11-12)
```

### 4.2 Critical Path

```mermaid
graph TD
    A[Week 1-3: PoC] -->|GO Decision| B[Week 4-7: API]
    B --> C[Week 8-10: Multi-Tenant]
    C --> D[Week 6: Security Audit]
    D --> E[Week 11-12: Anti-Detection]
    E --> F[Week 13-14: Monitoring]
    F --> G[Week 15: Launch]
```

### 4.3 Go/No-Go Gates

| Gate | Week | Criteria | On Failure |
|------|------|----------|------------|
| **PoC Validation** | Week 3 | ≥90% success, ≤2x latency, <500 LoC | Pivot to Firecrawl optimization |
| **Security Audit** | Week 10 | Zero critical/high findings | Block production launch |
| **Load Test** | Week 14 | 1000 req/min, P99 <30s | Optimize or extend timeline |
| **Beta Soft Launch** | Week 15 | 10 beta users, 80% success rate | Fix critical bugs before public |

---

## 5. Week-by-Week Breakdown

### **Week 1-3: PoC Validation (Extended)**

**Goal:** Prove Crawlee can match Firecrawl's 90%+ success rate

#### Day 1-2: Environment Setup & Layer 1 (curl_cffi)

**Files to Create:**
- `/02_phase_two/poc/requirements.txt`
- `/02_phase_two/poc/layer1_curl_cffi.py`
- `/02_phase_two/poc/test_sites.json` (50 test URLs)

**Layer 1 Implementation:**
```python
# /02_phase_two/poc/layer1_curl_cffi.py
from curl_cffi import requests
import time

class Layer1CurlCffi:
    """Layer 1: TLS fingerprinting with curl_cffi (Chrome131)"""

    def __init__(self):
        self.session = requests.Session(impersonate="chrome131")

    def scrape(self, url: str, timeout: int = 30) -> dict:
        """Attempt scrape with curl_cffi"""
        start = time.time()

        try:
            response = self.session.get(
                url,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                }
            )

            elapsed_ms = int((time.time() - start) * 1000)

            # Check for challenges
            challenge_detected = self._detect_challenge(response.text)

            return {
                'success': not challenge_detected and response.status_code == 200,
                'status_code': response.status_code,
                'html': response.text,
                'elapsed_ms': elapsed_ms,
                'challenge_detected': challenge_detected,
                'layer': 1
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'elapsed_ms': int((time.time() - start) * 1000),
                'layer': 1
            }

    def _detect_challenge(self, html: str) -> bool:
        """Detect bot challenges"""
        patterns = [
            'Cloudflare',
            'cf-browser-verification',
            '__cf_chl_jschl_tk__',
            'PerimeterX',
            '_px',
            'DataDome',
            'dd-cid',
            'Access Denied',
            'Forbidden',
            'Ray ID'
        ]
        return any(pattern in html for pattern in patterns)
```

**Test Script:**
```python
# /02_phase_two/poc/test_layer1.py
import json
from layer1_curl_cffi import Layer1CurlCffi

def test_layer1():
    """Test Layer 1 on 50 sites"""
    with open('test_sites.json') as f:
        sites = json.load(f)

    layer1 = Layer1CurlCffi()
    results = []

    for site in sites:
        print(f"Testing {site['url']}...")
        result = layer1.scrape(site['url'])
        results.append({
            'url': site['url'],
            'category': site['category'],  # 'unprotected', 'basic', 'cloudflare'
            **result
        })

    # Calculate success rate
    success_rate = sum(1 for r in results if r['success']) / len(results) * 100
    avg_latency = sum(r['elapsed_ms'] for r in results) / len(results)

    print(f"\nLayer 1 Results:")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Avg Latency: {avg_latency:.0f}ms")
    print(f"  Challenges Detected: {sum(1 for r in results if r.get('challenge_detected'))}")

    # Save results
    with open('layer1_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    test_layer1()
```

**Acceptance Criteria:**
- [ ] 60%+ success rate on unprotected sites
- [ ] <100ms average latency
- [ ] Correctly detects Cloudflare challenges (100% accuracy)
- [ ] Code <100 LoC

**Time:** 14 hours

---

#### Day 3-5: Layer 2 (Crawlee HTTP) & Layer 3 (Crawlee Browser)

**Files to Create:**
- `/02_phase_two/poc/layer2_crawlee_http.py`
- `/02_phase_two/poc/layer3_crawlee_browser.py`
- `/02_phase_two/poc/orchestrator.py`

**Layer 2-3 Implementation:**
```python
# /02_phase_two/poc/layer2_crawlee_http.py
from crawlee.http_crawler import HttpCrawler
from crawlee.beautifulsoup_crawler import BeautifulSoupCrawler
import asyncio

class Layer2CrawleeHTTP:
    """Layer 2: Crawlee HTTP with session management"""

    async def scrape(self, url: str) -> dict:
        """Scrape with Crawlee HTTP crawler"""
        result = {'success': False, 'layer': 2}

        async def request_handler(context):
            nonlocal result
            response = context.http_response
            result = {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'html': response.read().decode('utf-8'),
                'layer': 2
            }

        crawler = HttpCrawler(
            request_handler=request_handler,
            max_requests_per_crawl=1
        )

        await crawler.run([url])
        return result

# /02_phase_two/poc/layer3_crawlee_browser.py
from crawlee.playwright_crawler import PlaywrightCrawler

class Layer3CrawleeBrowser:
    """Layer 3: Full browser with stealth plugins"""

    async def scrape(self, url: str) -> dict:
        """Scrape with Playwright browser"""
        result = {'success': False, 'layer': 3}

        async def request_handler(context):
            nonlocal result
            page = context.page
            html = await page.content()
            result = {
                'success': True,
                'html': html,
                'layer': 3
            }

        crawler = PlaywrightCrawler(
            request_handler=request_handler,
            max_requests_per_crawl=1,
            headless=True,
            browser_type='chromium'
        )

        await crawler.run([url])
        return result
```

**Orchestrator:**
```python
# /02_phase_two/poc/orchestrator.py
from layer1_curl_cffi import Layer1CurlCffi
from layer2_crawlee_http import Layer2CrawleeHTTP
from layer3_crawlee_browser import Layer3CrawleeBrowser
import asyncio

class ScrapeOrchestrator:
    """Manages layer escalation"""

    def __init__(self):
        self.layer1 = Layer1CurlCffi()
        self.layer2 = Layer2CrawleeHTTP()
        self.layer3 = Layer3CrawleeBrowser()

    async def scrape(self, url: str, max_layer: int = 3) -> dict:
        """Try layers in sequence until success"""

        # Try Layer 1 (curl_cffi)
        result = self.layer1.scrape(url)
        if result['success']:
            return result

        # Escalate to Layer 2 (HTTP)
        if max_layer >= 2:
            result = await self.layer2.scrape(url)
            if result['success']:
                return result

        # Escalate to Layer 3 (Browser)
        if max_layer >= 3:
            result = await self.layer3.scrape(url)
            return result

        return result  # Return last failure

# Usage
async def main():
    orchestrator = ScrapeOrchestrator()
    result = await orchestrator.scrape('https://example.com')
    print(f"Success: {result['success']}, Layer: {result['layer']}")

asyncio.run(main())
```

**Acceptance Criteria:**
- [ ] 85%+ success rate across all 50 sites (with escalation)
- [ ] Layer 2 <500ms, Layer 3 <5s
- [ ] Automatic escalation works
- [ ] Code <300 LoC total

**Time:** 20 hours

---

#### Day 6-10: Layers 4-5 (Proxies + FlareSolverr)

**Files to Create:**
- `/02_phase_two/poc/layer4_proxy.py`
- `/02_phase_two/poc/layer5_flaresolverr.py`
- `/02_phase_two/poc/benchmark_full.py`
- `/02_phase_two/poc/POC_REPORT.md`

**Layer 4-5 Implementation:**
```python
# /02_phase_two/poc/layer4_proxy.py
from crawlee.playwright_crawler import PlaywrightCrawler
from playwright.async_api import async_playwright

class Layer4Proxy:
    """Layer 4: Browser + BrightData residential proxy"""

    def __init__(self, proxy_url: str):
        self.proxy_url = proxy_url  # http://user:pass@brd.superproxy.io:22225

    async def scrape(self, url: str) -> dict:
        """Scrape with proxy"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                proxy={'server': self.proxy_url},
                headless=True
            )
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle')
            html = await page.content()
            await browser.close()

            return {
                'success': True,
                'html': html,
                'layer': 4
            }

# /02_phase_two/poc/layer5_flaresolverr.py
import httpx

class Layer5FlareSolverr:
    """Layer 5: Dedicated Cloudflare solver"""

    def __init__(self, flaresolverr_url: str = 'http://localhost:8191'):
        self.url = flaresolverr_url

    async def scrape(self, url: str) -> dict:
        """Solve challenge with FlareSolverr"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.url}/v1',
                json={
                    'cmd': 'request.get',
                    'url': url,
                    'maxTimeout': 30000
                },
                timeout=35
            )
            data = response.json()

            return {
                'success': data['status'] == 'ok',
                'html': data['solution']['response'],
                'layer': 5
            }
```

**Full Benchmark:**
```python
# /02_phase_two/poc/benchmark_full.py
import json
import asyncio
from orchestrator import ScrapeOrchestrator

async def benchmark():
    """Test all layers on 50 sites"""
    with open('test_sites.json') as f:
        sites = json.load(f)

    orchestrator = ScrapeOrchestrator()
    results = []

    for site in sites:
        print(f"Testing {site['url']}...")
        result = await orchestrator.scrape(site['url'], max_layer=5)
        results.append({
            'url': site['url'],
            'category': site['category'],
            **result
        })

    # Calculate metrics
    success_rate = sum(1 for r in results if r['success']) / len(results) * 100
    layer_distribution = {
        1: sum(1 for r in results if r.get('layer') == 1),
        2: sum(1 for r in results if r.get('layer') == 2),
        3: sum(1 for r in results if r.get('layer') == 3),
        4: sum(1 for r in results if r.get('layer') == 4),
        5: sum(1 for r in results if r.get('layer') == 5),
    }

    print(f"\n=== PoC RESULTS ===")
    print(f"Overall Success Rate: {success_rate:.1f}%")
    print(f"Layer Distribution:")
    for layer, count in layer_distribution.items():
        print(f"  Layer {layer}: {count} sites ({count/len(results)*100:.1f}%)")

    # Save results
    with open('poc_results_final.json', 'w') as f:
        json.dump(results, f, indent=2)

    # GO/NO-GO Decision
    if success_rate >= 90:
        print("\n✅ PoC PASSED - Proceed to Week 4 (API Development)")
    else:
        print(f"\n❌ PoC FAILED - Success rate {success_rate:.1f}% < 90%")
        print("RECOMMENDATION: Pivot to Firecrawl optimization")

asyncio.run(benchmark())
```

**GO/NO-GO Criteria:**
- [ ] **≥90% success rate across 50 sites** (MANDATORY)
- [ ] P99 latency ≤60s (2x Firecrawl's 30s)
- [ ] Code <500 LoC total
- [ ] Team confidence: High

**IF FAILED:** Hold Week 3 retrospective, decide: (A) Extend PoC 1 week, (B) Pivot to Firecrawl, (C) Hybrid model

**Time:** 30 hours

---

#### Day 11-15: PoC Documentation & Decision

**Deliverables:**
- `/02_phase_two/poc/POC_REPORT.md` - Full findings report
- `/02_phase_two/poc/DECISION.md` - GO/NO-GO rationale
- Presentation to stakeholders (if team > 1 person)

**Report Template:**
```markdown
# PoC Report: Crawlee Migration Validation

## Executive Summary
- **Success Rate:** XX.X%
- **Decision:** ✅ GO / ❌ NO-GO
- **Confidence:** High / Medium / Low

## Test Matrix
50 sites tested across 3 categories:
- Unprotected (30 sites): XX% success
- Basic protection (15 sites): XX% success
- Cloudflare (5 sites): XX% success

## Performance Comparison
| Metric | Firecrawl (Baseline) | Crawlee (PoC) | Delta |
|--------|---------------------|---------------|-------|
| Success Rate | 95% | XX% | ±X% |
| P99 Latency | 30s | XXs | XXx |
| Code Complexity | 862 LoC | XXX LoC | -XX% |

## Layer Distribution
- Layer 1 (curl_cffi): XX% of jobs
- Layer 2 (HTTP): XX%
- Layer 3 (Browser): XX%
- Layer 4 (Proxy): XX%
- Layer 5 (FlareSolverr): XX%

## Recommendation
[GO/NO-GO rationale...]

## Next Steps
Week 4: Begin API development
```

**Time:** 10 hours

**TOTAL WEEK 1-3:** 74 hours (~2.5 weeks at 30 hours/week)

---

### **Week 4-7: API Layer (Extended from Weeks 3-4)**

**Goal:** Production-ready FastAPI gateway with authentication, rate limiting, quotas

#### Day 16-18: Project Scaffolding & Database

**Files to Create:**
```
/02_phase_two/
├── api/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py
│   ├── requirements.txt
│   └── Dockerfile
├── db/
│   └── migrations/
│       └── 001_initial_schema.sql
└── docker-compose.yml
```

**FastAPI Skeleton:**
```python
# /api/app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import structlog

app = FastAPI(
    title="Scraping Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured logging
log = structlog.get_logger()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    """API root"""
    return {
        "message": "Scraping Platform API",
        "docs": "/docs",
        "version": "1.0.0"
    }
```

**Docker Compose:**
```yaml
# /docker-compose.yml
version: '3.9'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: scraping_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d

  pgbouncer:
    image: pgbouncer/pgbouncer:1.21
    environment:
      DATABASES_HOST: postgres
      DATABASES_PORT: 5432
      PGBOUNCER_POOL_MODE: transaction
      PGBOUNCER_MAX_CLIENT_CONN: 10000
      PGBOUNCER_DEFAULT_POOL_SIZE: 50
    ports:
      - "6432:6432"
    depends_on:
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru

  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@pgbouncer:6432/scraping_platform
      REDIS_URL: redis://redis:6379
    depends_on:
      - pgbouncer
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # BullMQ workers (Node.js)
  worker:
    build: ./workers
    environment:
      REDIS_URL: redis://redis:6379
      DATABASE_URL: postgresql://postgres:postgres@pgbouncer:6432/scraping_platform
    depends_on:
      - redis
      - pgbouncer
    deploy:
      replicas: 3  # 3 workers initially

volumes:
  postgres_data:
```

**Acceptance Criteria:**
- [ ] Docker Compose starts all services
- [ ] FastAPI serves at http://localhost:8000
- [ ] /docs shows OpenAPI UI
- [ ] Database schema created successfully
- [ ] PgBouncer connection pooling active

**Time:** 18 hours

---

#### Day 19-22: Authentication & Middleware Stack

**Files to Create:**
- `/api/app/middleware/auth.py`
- `/api/app/middleware/rate_limit.py`
- `/api/app/middleware/quota.py`
- `/api/app/middleware/logging.py`

**Authentication:**
```python
# /api/app/middleware/auth.py
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
import bcrypt
import structlog

log = structlog.get_logger()

async def verify_api_key(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> str:
    """Verify API key and return tenant_id"""

    # Extract key from "Bearer fc_live_xxxx"
    if not authorization.startswith('Bearer '):
        raise HTTPException(401, "Invalid authorization header")

    api_key = authorization[7:]  # Remove "Bearer "

    # Query database for key hash
    result = db.execute("""
        SELECT ak.tenant_id, ak.status, t.status AS tenant_status
        FROM api_keys ak
        JOIN tenants t ON ak.tenant_id = t.id
        WHERE ak.key_hash = $1
    """, [bcrypt.hashpw(api_key.encode(), bcrypt.gensalt())])

    row = result.fetchone()
    if not row:
        log.warn("invalid_api_key_attempt", key_prefix=api_key[:10])
        raise HTTPException(401, "Invalid API key")

    if row['status'] != 'active' or row['tenant_status'] != 'active':
        raise HTTPException(403, "API key or tenant suspended")

    tenant_id = row['tenant_id']

    # Set RLS context (CRITICAL FOR SECURITY)
    db.execute(f"SET LOCAL app.tenant_id = '{tenant_id}'")

    log.info("api_key_verified", tenant_id=tenant_id)
    return tenant_id
```

**Rate Limiting:**
```python
# /api/app/middleware/rate_limit.py
from fastapi import HTTPException, Depends
from redis import Redis
import time

redis_client = Redis.from_url('redis://localhost:6379')

RATE_LIMITS = {
    'free': 100,       # 100 requests per hour
    'pro': 1000,       # 1000 requests per hour
    'enterprise': 10000
}

async def check_rate_limit(
    tenant_id: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Sliding window rate limiter"""

    # Get tenant tier
    tier = db.execute(
        "SELECT tier FROM tenants WHERE id = $1",
        [tenant_id]
    ).fetchone()['tier']

    limit = RATE_LIMITS[tier]
    key = f"rate_limit:{tenant_id}:hour"

    # Lua script for atomic increment
    lua_script = """
    local current = redis.call('INCR', KEYS[1])
    if current == 1 then
        redis.call('EXPIRE', KEYS[1], 3600)
    end
    return current
    """

    current = redis_client.eval(lua_script, 1, key)

    if current > limit:
        raise HTTPException(
            429,
            f"Rate limit exceeded: {limit}/hour",
            headers={
                'X-RateLimit-Limit': str(limit),
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': str(int(time.time()) + 3600)
            }
        )

    # Add headers
    return {
        'X-RateLimit-Limit': str(limit),
        'X-RateLimit-Remaining': str(limit - current),
        'X-RateLimit-Reset': str(int(time.time()) + 3600)
    }
```

**Quota Enforcement:**
```python
# /api/app/middleware/quota.py
from fastapi import HTTPException, Depends

async def check_quota(
    tenant_id: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Check monthly quota"""

    result = db.execute("""
        SELECT t.monthly_quota, COALESCE(us.total_scrapes, 0) AS used
        FROM tenants t
        LEFT JOIN usage_summary us
          ON t.id = us.tenant_id
          AND us.month = DATE_TRUNC('month', NOW())
        WHERE t.id = $1
    """, [tenant_id]).fetchone()

    quota = result['monthly_quota']
    used = result['used']
    remaining = quota - used

    if remaining <= 0:
        raise HTTPException(
            402,
            f"Monthly quota exceeded: {used}/{quota} scrapes",
            headers={
                'X-Quota-Limit': str(quota),
                'X-Quota-Used': str(used),
                'X-Quota-Remaining': '0'
            }
        )

    return {
        'X-Quota-Limit': str(quota),
        'X-Quota-Used': str(used),
        'X-Quota-Remaining': str(remaining)
    }
```

**Acceptance Criteria:**
- [ ] Valid API key allows access
- [ ] Invalid API key returns 401
- [ ] Rate limit enforced (tested with 101 requests in 1 hour)
- [ ] Quota enforced (tested with exceeded quota)
- [ ] RLS context set correctly (tenant cannot see other's jobs)

**Time:** 24 hours

---

#### Day 23-26: Core API Endpoints

**Files to Create:**
- `/api/app/routes/scrape.py`
- `/api/app/services/job_service.py`
- `/api/app/models/requests.py`

**POST /v2/scrape Endpoint:**
```python
# /api/app/routes/scrape.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
import uuid

router = APIRouter(prefix="/v2", tags=["Scraping"])

class ScrapeRequest(BaseModel):
    url: HttpUrl
    method: str = 'auto'  # 'http', 'browser', 'auto'
    formats: list[str] = ['markdown']  # 'html', 'markdown', 'json'
    timeout: int = 30

class ScrapeResponse(BaseModel):
    id: str
    status: str  # 'pending'
    status_url: str

@router.post("/scrape", response_model=ScrapeResponse)
async def create_scrape_job(
    request: ScrapeRequest,
    tenant_id: str = Depends(verify_api_key),
    rate_limit: dict = Depends(check_rate_limit),
    quota: dict = Depends(check_quota),
    db: Session = Depends(get_db)
):
    """Create scraping job (async)"""

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Insert into database
    db.execute("""
        INSERT INTO jobs (id, tenant_id, url, method, status)
        VALUES ($1, $2, $3, $4, 'pending')
    """, [job_id, tenant_id, str(request.url), request.method])
    db.commit()

    # Enqueue to BullMQ
    await enqueue_job(job_id, tenant_id, request)

    log.info("job_created", job_id=job_id, tenant_id=tenant_id)

    return ScrapeResponse(
        id=job_id,
        status='pending',
        status_url=f"/v2/scrape/{job_id}"
    )
```

**GET /v2/scrape/{id} Endpoint:**
```python
@router.get("/scrape/{job_id}")
async def get_scrape_job(
    job_id: str,
    tenant_id: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get job status and results"""

    # RLS automatically filters by tenant_id
    result = db.execute("""
        SELECT id, status, layer_used, s3_key_html, s3_key_markdown,
               error_message, elapsed_ms, created_at, completed_at
        FROM jobs
        WHERE id = $1
    """, [job_id]).fetchone()

    if not result:
        raise HTTPException(404, "Job not found")

    response = {
        'id': result['id'],
        'status': result['status'],
        'created_at': result['created_at'],
    }

    if result['status'] == 'completed':
        # Generate presigned S3 URLs (1 hour expiry)
        response['data'] = {
            'html_url': generate_presigned_url(result['s3_key_html']),
            'markdown_url': generate_presigned_url(result['s3_key_markdown']),
            'metadata': {
                'layer_used': result['layer_used'],
                'elapsed_ms': result['elapsed_ms']
            }
        }
    elif result['status'] == 'failed':
        response['error'] = result['error_message']

    return response
```

**BullMQ Integration:**
```typescript
// /workers/queue.ts
import { Queue, Worker } from 'bullmq';
import { scrapeJob } from './scraper';

const scrapeQueue = new Queue('scrape-jobs', {
  connection: { host: 'redis', port: 6379 }
});

export async function enqueueJob(jobId: string, tenantId: string, request: any) {
  await scrapeQueue.add('scrape', {
    jobId,
    tenantId,
    url: request.url,
    method: request.method
  }, {
    jobId,  // Deduplicate
    priority: getPriority(tenantId)  // 1=Enterprise, 2=Pro, 3=Free
  });
}

function getPriority(tenantId: string): number {
  // Query tenant tier from database
  // Enterprise: 1, Pro: 2, Free: 3
  return 2;
}

// Worker process
const worker = new Worker('scrape-jobs', async (job) => {
  await scrapeJob(job.data);
}, {
  connection: { host: 'redis', port: 6379 },
  concurrency: 10  // 10 concurrent jobs per worker
});
```

**Acceptance Criteria:**
- [ ] POST /v2/scrape returns job ID in <100ms
- [ ] GET /v2/scrape/{id} returns correct status
- [ ] Job enqueued to BullMQ successfully
- [ ] RLS prevents cross-tenant access (tested)
- [ ] Presigned URLs work and expire after 1 hour

**Time:** 24 hours

---

#### Day 27-28: Worker Implementation

**Files to Create:**
- `/workers/scraper.ts`
- `/workers/layers/orchestrator.py`
- `/workers/services/s3_uploader.py`

**Worker Process:**
```typescript
// /workers/scraper.ts
import { createPool } from 'generic-pool';
import { PythonShell } from 'python-shell';
import { uploadToS3, updateJobStatus } from './services';

export async function scrapeJob(data: any) {
  const { jobId, tenantId, url, method } = data;

  try {
    // Update status to 'running'
    await updateJobStatus(jobId, 'running');

    // Call Python orchestrator
    const result = await PythonShell.run('orchestrator.py', {
      args: [url, method],
      pythonPath: 'python3',
      scriptPath: './layers'
    });

    const scrapeResult = JSON.parse(result[0]);

    if (scrapeResult.success) {
      // Upload to S3
      const htmlKey = `${tenantId}/${jobId}/content.html`;
      const markdownKey = `${tenantId}/${jobId}/content.md`;

      await uploadToS3(htmlKey, scrapeResult.html);
      await uploadToS3(markdownKey, scrapeResult.markdown);

      // Update job record
      await updateJobStatus(jobId, 'completed', {
        s3_key_html: htmlKey,
        s3_key_markdown: markdownKey,
        layer_used: scrapeResult.layer,
        elapsed_ms: scrapeResult.elapsed_ms
      });

      // Track usage
      await recordUsage(tenantId, jobId, scrapeResult.layer, scrapeResult.cost_cents);

    } else {
      await updateJobStatus(jobId, 'failed', {
        error_message: scrapeResult.error
      });
    }

  } catch (error) {
    await updateJobStatus(jobId, 'failed', {
      error_message: error.message
    });
  }
}
```

**Acceptance Criteria:**
- [ ] Worker dequeues jobs from BullMQ
- [ ] Calls Python orchestrator successfully
- [ ] Uploads results to S3
- [ ] Updates job status correctly
- [ ] Handles failures gracefully

**Time:** 12 hours

---

**TOTAL WEEK 4-7:** 78 hours (~2.6 weeks at 30 hours/week)

---

### **Week 8-10: Multi-Tenancy & Security (Extended)**

**Goal:** Production-grade tenant isolation, security audit, and operational readiness

#### Day 29-32: Tenant Management & API Key Rotation

**Files to Create:**
- `/api/app/routes/admin.py`
- `/api/app/services/tenant_service.py`
- `/api/app/utils/key_generator.py`

**Admin API:**
```python
# /api/app/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException
import secrets
import bcrypt

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/tenants")
async def create_tenant(
    name: str,
    email: str,
    tier: str = 'free',
    admin_key: str = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """Create new tenant"""

    tenant_id = str(uuid.uuid4())

    # Insert tenant
    db.execute("""
        INSERT INTO tenants (id, name, email, tier, monthly_quota)
        VALUES ($1, $2, $3, $4, $5)
    """, [tenant_id, name, email, tier, 500 if tier == 'free' else 10000])

    # Generate API key
    api_key = f"fc_live_{secrets.token_urlsafe(32)}"
    key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

    db.execute("""
        INSERT INTO api_keys (tenant_id, key_hash, key_prefix, name)
        VALUES ($1, $2, $3, 'Default')
    """, [tenant_id, key_hash, api_key[:10]])

    db.commit()

    return {
        'tenant_id': tenant_id,
        'api_key': api_key,  # SHOW ONLY ONCE
        'tier': tier
    }

@router.post("/tenants/{tenant_id}/api-keys")
async def rotate_api_key(
    tenant_id: str,
    admin_key: str = Depends(verify_admin_key),
    db: Session = Depends(get_db)
):
    """Generate new API key"""

    # Revoke old keys
    db.execute("""
        UPDATE api_keys
        SET status = 'revoked'
        WHERE tenant_id = $1
    """, [tenant_id])

    # Generate new key
    api_key = f"fc_live_{secrets.token_urlsafe(32)}"
    key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

    db.execute("""
        INSERT INTO api_keys (tenant_id, key_hash, key_prefix, name)
        VALUES ($1, $2, $3, 'Rotated')
    """, [tenant_id, key_hash, api_key[:10]])

    db.commit()

    return {'api_key': api_key}
```

**Acceptance Criteria:**
- [ ] Can create tenant via API
- [ ] API key generated in correct format (fc_live_xxx)
- [ ] Old keys revoked on rotation
- [ ] New keys work immediately

**Time:** 20 hours

---

#### Day 33-35: **CRITICAL - Security Audit (Week 10)**

**This is mandatory before production data. Do NOT defer to Month 9.**

**Audit Scope:**
1. PostgreSQL RLS policies
2. SQL injection testing (100+ payloads)
3. Authentication bypass attempts
4. Cross-tenant access attempts
5. Timing attack vulnerability
6. Resource exhaustion testing

**Hire External Auditor:**
- **Platform:** Upwork, BugCrowd, HackerOne
- **Cost:** $5,000 for RLS audit + $7,500 for penetration test = $12,500
- **Timeline:** 1 week audit + 3 days remediation
- **Deliverable:** Security report with remediation plan

**Internal Testing Checklist:**
```python
# /tests/security/test_rls.py
def test_cross_tenant_access():
    """Tenant A cannot access Tenant B's jobs"""

    # Create Tenant A job
    tenant_a_key = create_tenant('A')
    job_a = create_job(tenant_a_key, 'https://example.com')

    # Create Tenant B
    tenant_b_key = create_tenant('B')

    # Attempt access
    response = requests.get(
        f'/v2/scrape/{job_a}',
        headers={'Authorization': f'Bearer {tenant_b_key}'}
    )

    assert response.status_code == 404  # Not found (RLS filtered)

def test_sql_injection():
    """Test SQL injection in tenant_id parameter"""

    # Attempt SQL injection
    malicious_key = "'; DROP TABLE jobs; --"

    response = requests.get(
        '/v2/scrape/123',
        headers={'Authorization': f'Bearer {malicious_key}'}
    )

    assert response.status_code == 401  # Invalid key

    # Verify jobs table still exists
    db.execute("SELECT COUNT(*) FROM jobs")  # Should not error

def test_timing_attack():
    """Constant-time API key validation"""

    valid_key = 'fc_live_valid_key_here'
    invalid_key = 'fc_live_invalid_key_here'

    # Measure timing for valid key
    times_valid = []
    for _ in range(100):
        start = time.time()
        requests.get('/health', headers={'Authorization': f'Bearer {valid_key}'})
        times_valid.append(time.time() - start)

    # Measure timing for invalid key
    times_invalid = []
    for _ in range(100):
        start = time.time()
        requests.get('/health', headers={'Authorization': f'Bearer {invalid_key}'})
        times_invalid.append(time.time() - start)

    # Check if timing difference reveals validity
    avg_valid = sum(times_valid) / len(times_valid)
    avg_invalid = sum(times_invalid) / len(times_invalid)

    assert abs(avg_valid - avg_invalid) < 0.001  # <1ms difference
```

**Remediation:**
- Fix any critical/high findings within 3 days
- Retest with auditor
- Document all changes in security changelog

**Acceptance Criteria:**
- [ ] **Zero critical or high-severity findings**
- [ ] RLS policies validated by independent auditor
- [ ] SQL injection testing passed (100+ payloads)
- [ ] Timing attack tests passed
- [ ] Security report published internally

**Time:** 32 hours (including remediation)

---

**TOTAL WEEK 8-10:** 52 hours (~1.75 weeks at 30 hours/week)

---

### **Week 11-12: Anti-Detection Production**

**Goal:** Production-ready 5-layer system with site profiles and cost controls

#### Day 36-40: Production Layers + Proxy Controls

**Files to Create:**
- `/workers/layers/layer1_production.py`
- `/workers/layers/layer4_proxy.py`
- `/workers/layers/proxy_circuit_breaker.py`
- `/workers/layers/browser_pool.py`

**Proxy Circuit Breaker (CRITICAL):**
```python
# /workers/layers/proxy_circuit_breaker.py
class ProxyCircuitBreaker:
    """Prevent proxy cost explosions"""

    PLATFORM_LIMIT = 500  # $500/month platform-wide
    TENANT_LIMITS = {
        'free': 0,
        'pro': 50,
        'enterprise': None
    }

    def check_budget(self, tenant_id: str) -> bool:
        """Check if proxy budget allows request"""

        # Check platform-wide limit
        platform_spend = self.get_monthly_spend()
        if platform_spend >= self.PLATFORM_LIMIT:
            log.critical("proxy_budget_exceeded_platform", spend=platform_spend)
            return False  # Reject ALL proxy requests

        # Check tenant-specific limit
        tier = self.get_tenant_tier(tenant_id)
        tenant_limit = self.TENANT_LIMITS[tier]

        if tenant_limit is not None:
            tenant_spend = self.get_tenant_monthly_spend(tenant_id)
            if tenant_spend >= tenant_limit:
                log.warn("proxy_budget_exceeded_tenant",
                        tenant_id=tenant_id, spend=tenant_spend)
                return False  # Use Layer 3 instead

        return True  # Allow proxy

    def get_monthly_spend(self) -> float:
        """Query usage_records for proxy costs this month"""
        result = db.execute("""
            SELECT COALESCE(SUM(cost_cents), 0) AS total
            FROM usage_records
            WHERE proxy_used = true
              AND created_at >= DATE_TRUNC('month', NOW())
        """).fetchone()
        return result['total'] / 100  # Convert cents to dollars
```

**Browser Pool Manager:**
```python
# /workers/layers/browser_pool.py
from playwright.async_api import async_playwright
import asyncio
import time

class BrowserPool:
    """Aggressive browser lifecycle management"""

    def __init__(self, max_size: int = 10):
        self.pool = []
        self.max_size = max_size
        self.lock = asyncio.Lock()

    async def get_browser(self):
        """Get browser from pool or create new"""
        async with self.lock:
            # Remove expired browsers
            now = time.time()
            self.pool = [
                b for b in self.pool
                if (now - b['start_time']) < 1800  # 30 min max lifetime
                and b['request_count'] < 100  # 100 request max
            ]

            # Close idle browsers
            for browser_info in self.pool:
                if (now - browser_info['last_used']) > 30:  # 30s idle timeout
                    await browser_info['browser'].close()
                    self.pool.remove(browser_info)

            # Get existing or create new
            if self.pool:
                browser_info = self.pool.pop(0)
            else:
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(headless=True)
                browser_info = {
                    'browser': browser,
                    'start_time': now,
                    'request_count': 0,
                    'last_used': now
                }

            browser_info['request_count'] += 1
            browser_info['last_used'] = now

            return browser_info['browser']

    async def return_browser(self, browser):
        """Return browser to pool"""
        async with self.lock:
            if len(self.pool) < self.max_size:
                # Keep in pool
                pass
            else:
                await browser.close()
```

**Acceptance Criteria:**
- [ ] Proxy circuit breaker blocks at $450/month (90% of $500)
- [ ] Per-tenant limits enforced (Pro: $50/month)
- [ ] Browsers recycled every 30 minutes or 100 requests
- [ ] Memory usage stable over 1000 scrapes

**Time:** 28 hours

---

#### Day 41-45: Site Profiles & Challenge Detection

**Files to Create:**
- `/workers/layers/site_profiler.py`
- `/workers/layers/challenge_detector.py`
- `/api/app/routes/site_profiles.py`

**Site Profiler:**
```python
# /workers/layers/site_profiler.py
class SiteProfiler:
    """Auto-learning layer selection"""

    def get_start_layer(self, url: str) -> int:
        """Get optimal starting layer for domain"""

        domain = extract_domain(url)

        # Query database for profile
        result = db.execute("""
            SELECT start_layer, success_rate_layer1, success_rate_layer2, success_rate_layer3
            FROM site_profiles
            WHERE domain = $1
        """, [domain]).fetchone()

        if result:
            return result['start_layer']
        else:
            return 1  # Default to Layer 1 for new sites

    def learn_from_result(self, url: str, layer_used: int, success: bool):
        """Update site profile based on result"""

        domain = extract_domain(url)

        # Upsert profile
        db.execute("""
            INSERT INTO site_profiles (domain, start_layer)
            VALUES ($1, $2)
            ON CONFLICT (domain) DO UPDATE
            SET start_layer = CASE
                WHEN $3 = true THEN $2  -- Success: use this layer next time
                WHEN $2 < 3 THEN $2 + 1  -- Failure: try next layer
                ELSE $2
            END,
            last_updated = NOW()
        """, [domain, layer_used, success])
```

**Enhanced Challenge Detection:**
```python
# /workers/layers/challenge_detector.py
CHALLENGE_PATTERNS = {
    'cloudflare': [
        'Cloudflare',
        'cf-browser-verification',
        '__cf_chl_jschl_tk__',
        'cf-challenge',
        'Ray ID'
    ],
    'perimeterx': [
        'PerimeterX',
        '_px',
        'px-captcha',
        'px-block'
    ],
    'datadome': [
        'DataDome',
        'dd-cid',
        'datadome.co'
    ],
    'akamai': [
        'akamai',
        'akam-sw',
        '_abck'
    ],
    'incapsula': [
        'Incapsula',
        '_incap',
        'incap_ses'
    ],
    'recaptcha': [
        'recaptcha',
        'g-recaptcha',
        'grecaptcha'
    ],
    'hcaptcha': [
        'hcaptcha',
        'h-captcha'
    ],
    'kasada': [
        'kasada',
        'kpsdk'
    ]
}

def detect_challenge(html: str, status_code: int) -> dict:
    """Detect which protection is active"""

    for protection, patterns in CHALLENGE_PATTERNS.items():
        if any(pattern in html for pattern in patterns):
            return {
                'detected': True,
                'protection': protection,
                'recommended_layer': get_recommended_layer(protection)
            }

    # Check for generic blocks
    if status_code in [403, 503]:
        return {
            'detected': True,
            'protection': 'generic',
            'recommended_layer': 3
        }

    return {'detected': False}

def get_recommended_layer(protection: str) -> int:
    """Get recommended layer for protection type"""
    recommendations = {
        'cloudflare': 5,  # FlareSolverr
        'perimeterx': 4,  # Proxy + Browser
        'datadome': 4,
        'akamai': 3,      # Browser
        'incapsula': 3,
        'recaptcha': 5,   # FlareSolverr
        'hcaptcha': 5,
        'kasada': 5,
        'generic': 3
    }
    return recommendations.get(protection, 3)
```

**Acceptance Criteria:**
- [ ] Site profiles loaded from database
- [ ] Auto-learning updates start_layer after failures
- [ ] 8+ protections detected (was 3)
- [ ] Detection accuracy >95% on test suite

**Time:** 28 hours

---

**TOTAL WEEK 11-12:** 56 hours (~1.9 weeks at 30 hours/week)

---

### **Week 13-14: Monitoring & Observability**

**Goal:** Production-grade monitoring, alerting, and dashboards

#### Day 46-50: Prometheus + Grafana Setup

**Files to Create:**
- `/infra/prometheus/prometheus.yml`
- `/infra/grafana/dashboards/api_dashboard.json`
- `/infra/grafana/dashboards/worker_dashboard.json`
- `/infra/grafana/dashboards/business_dashboard.json`
- `/api/app/metrics.py`

**Prometheus Configuration:**
```yaml
# /infra/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics

  - job_name: 'workers'
    static_configs:
      - targets: ['worker:9090']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

**API Metrics:**
```python
# /api/app/metrics.py
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Job metrics
jobs_total = Counter(
    'jobs_total',
    'Total jobs created',
    ['tenant_tier', 'status']
)

jobs_by_layer = Counter(
    'jobs_by_layer_total',
    'Jobs by layer',
    ['layer', 'tenant_tier']
)

job_duration = Histogram(
    'job_duration_seconds',
    'Job processing duration',
    ['layer'],
    buckets=(1, 5, 10, 30, 60, 120)
)

# Business metrics
active_tenants = Gauge(
    'active_tenants_total',
    'Number of active tenants',
    ['tier']
)

monthly_revenue = Gauge(
    'monthly_revenue_dollars',
    'Estimated monthly revenue'
)

# Add to FastAPI app
from fastapi import FastAPI
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**Grafana Dashboards:**

**1. API Dashboard:**
```json
{
  "dashboard": {
    "title": "API Performance",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~'5..'}[5m])"
          }
        ]
      }
    ]
  }
}
```

**2. Worker Dashboard:**
```json
{
  "dashboard": {
    "title": "Worker Performance",
    "panels": [
      {
        "title": "Jobs by Layer",
        "targets": [
          {
            "expr": "jobs_by_layer_total"
          }
        ]
      },
      {
        "title": "Success Rate",
        "targets": [
          {
            "expr": "rate(jobs_total{status='completed'}[5m]) / rate(jobs_total[5m])"
          }
        ]
      },
      {
        "title": "Queue Depth",
        "targets": [
          {
            "expr": "bullmq_queue_waiting_total"
          }
        ]
      }
    ]
  }
}
```

**Alert Rules:**
```yaml
# /infra/prometheus/alerts.yml
groups:
  - name: platform_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Error rate >5% for 5 minutes"

      - alert: QueueBackup
        expr: bullmq_queue_waiting_total > 1000
        for: 10m
        annotations:
          summary: "Queue depth >1000 jobs"

      - alert: ProxyBudgetExceeded
        expr: proxy_monthly_spend_dollars > 450
        annotations:
          summary: "Proxy spend >$450/month"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends > 450
        annotations:
          summary: "PostgreSQL connections >450 (max 500)"
```

**Acceptance Criteria:**
- [ ] Prometheus scrapes all services
- [ ] 3 Grafana dashboards complete
- [ ] Alerts fire on test conditions
- [ ] Metrics retained 30 days

**Time:** 32 hours

---

**TOTAL WEEK 13-14:** 32 hours (~1.1 weeks at 30 hours/week)

---

### **Week 15: Hardening & Launch Prep (Compressed)**

**Goal:** Production deployment, documentation, soft launch to 10 beta users

#### Day 51-53: Load Testing & Optimization

**Files to Create:**
- `/tests/load/locust_test.py`
- `/docs/PERFORMANCE_REPORT.md`

**Load Test:**
```python
# /tests/load/locust_test.py
from locust import HttpUser, task, between

class ScrapingPlatformUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Authenticate"""
        self.api_key = 'fc_live_test_key_here'
        self.headers = {'Authorization': f'Bearer {self.api_key}'}

    @task(3)
    def create_job(self):
        """Create scraping job (most common)"""
        self.client.post('/v2/scrape', json={
            'url': 'https://example.com',
            'method': 'auto'
        }, headers=self.headers)

    @task(1)
    def check_status(self):
        """Poll job status"""
        self.client.get('/v2/scrape/test-job-id', headers=self.headers)
```

**Run Load Test:**
```bash
# Target: 1000 requests/min (16.7 req/sec)
locust -f tests/load/locust_test.py \
  --host http://localhost:8000 \
  --users 50 \
  --spawn-rate 10 \
  --run-time 10m \
  --html load_test_report.html
```

**Acceptance Criteria:**
- [ ] Handles 1000 req/min without errors
- [ ] P99 latency <100ms for POST /v2/scrape
- [ ] No worker crashes during test
- [ ] Database connections stay <50

**Time:** 16 hours

---

#### Day 54-55: Documentation & Launch

**Files to Create:**
- `/docs/README.md` - Getting started guide
- `/docs/API_REFERENCE.md` - Complete API docs
- `/docs/DEPLOYMENT.md` - Production deployment guide
- `/docs/TROUBLESHOOTING.md` - Common issues

**Documentation Template:**
```markdown
# Getting Started

## 1. Sign Up
POST /admin/tenants
{
  "name": "My Company",
  "email": "user@example.com",
  "tier": "free"
}

Response:
{
  "tenant_id": "...",
  "api_key": "fc_live_...",  # SAVE THIS
  "tier": "free"
}

## 2. Create Scrape Job
POST /v2/scrape
Authorization: Bearer fc_live_...
{
  "url": "https://example.com"
}

Response:
{
  "id": "job_123",
  "status": "pending",
  "status_url": "/v2/scrape/job_123"
}

## 3. Poll for Results
GET /v2/scrape/job_123
Authorization: Bearer fc_live_...

Response:
{
  "id": "job_123",
  "status": "completed",
  "data": {
    "html_url": "https://s3.../content.html?...",
    "markdown_url": "https://s3.../content.md?..."
  }
}

## Next Steps
- [API Reference](/docs/API_REFERENCE.md)
- [Python SDK](https://pypi.org/project/scraping-platform/)
- [Discord Community](https://discord.gg/...)
```

**Launch Checklist:**
- [ ] All documentation complete
- [ ] Python SDK published to PyPI (test)
- [ ] 10 beta users onboarded
- [ ] Monitoring dashboards shared with team
- [ ] Incident response runbook documented
- [ ] Soft launch announcement drafted

**Time:** 12 hours

---

**TOTAL WEEK 15:** 28 hours (~0.9 weeks at 30 hours/week)

---

## 6. Code Examples & Templates

### 6.1 Full Orchestrator (Production)

```python
# /workers/layers/orchestrator.py
from layer1_curl_cffi import Layer1CurlCffi
from layer2_crawlee_http import Layer2CrawleeHTTP
from layer3_crawlee_browser import Layer3CrawleeBrowser
from layer4_proxy import Layer4Proxy
from layer5_flaresolverr import Layer5FlareSolverr
from proxy_circuit_breaker import ProxyCircuitBreaker
from site_profiler import SiteProfiler
from challenge_detector import detect_challenge
import asyncio
import time
import structlog

log = structlog.get_logger()

class ProductionOrchestrator:
    """5-layer anti-detection orchestrator"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.layer1 = Layer1CurlCffi()
        self.layer2 = Layer2CrawleeHTTP()
        self.layer3 = Layer3CrawleeBrowser()
        self.layer4 = Layer4Proxy()
        self.layer5 = Layer5FlareSolverr()
        self.circuit_breaker = ProxyCircuitBreaker()
        self.profiler = SiteProfiler()

    async def scrape(self, url: str, method: str = 'auto') -> dict:
        """Orchestrate scraping with automatic escalation"""

        start_time = time.time()
        result = None

        # Get optimal starting layer
        start_layer = self.profiler.get_start_layer(url)
        log.info("scrape_start", url=url, tenant_id=self.tenant_id, start_layer=start_layer)

        # Try layers in sequence
        for layer_num in range(start_layer, 6):
            try:
                result = await self._try_layer(layer_num, url)

                if result['success']:
                    # Success! Record and return
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    result['elapsed_ms'] = elapsed_ms

                    # Learn from success
                    self.profiler.learn_from_result(url, layer_num, success=True)

                    log.info("scrape_success", url=url, layer=layer_num, elapsed_ms=elapsed_ms)
                    return result

                # Check for challenge
                challenge = detect_challenge(result.get('html', ''), result.get('status_code', 0))

                if challenge['detected']:
                    recommended_layer = challenge['recommended_layer']
                    log.info("challenge_detected",
                            protection=challenge['protection'],
                            recommended_layer=recommended_layer)

                    # Skip to recommended layer
                    if recommended_layer > layer_num:
                        layer_num = recommended_layer - 1  # Will increment to recommended_layer
                        continue

            except Exception as e:
                log.error("layer_failed", layer=layer_num, error=str(e))
                continue

        # All layers failed
        elapsed_ms = int((time.time() - start_time) * 1000)
        log.error("scrape_failed", url=url, elapsed_ms=elapsed_ms)

        return {
            'success': False,
            'error': 'All layers exhausted',
            'elapsed_ms': elapsed_ms
        }

    async def _try_layer(self, layer_num: int, url: str) -> dict:
        """Try specific layer"""

        if layer_num == 1:
            return self.layer1.scrape(url)
        elif layer_num == 2:
            return await self.layer2.scrape(url)
        elif layer_num == 3:
            return await self.layer3.scrape(url)
        elif layer_num == 4:
            # Check proxy budget
            if not self.circuit_breaker.check_budget(self.tenant_id):
                log.warn("proxy_budget_exceeded", tenant_id=self.tenant_id)
                return {'success': False, 'error': 'Proxy budget exceeded'}
            return await self.layer4.scrape(url)
        elif layer_num == 5:
            # Check proxy budget (FlareSolverr also uses proxies)
            if not self.circuit_breaker.check_budget(self.tenant_id):
                log.warn("proxy_budget_exceeded", tenant_id=self.tenant_id)
                return {'success': False, 'error': 'Proxy budget exceeded'}
            return await self.layer5.scrape(url)
        else:
            return {'success': False, 'error': 'Invalid layer'}
```

---

## 7. Testing Strategy

### 7.1 Unit Tests (80% coverage target)

**Location:** `/tests/unit/`

```python
# /tests/unit/test_auth.py
def test_valid_api_key():
    """Valid API key returns tenant_id"""
    tenant_id = verify_api_key("Bearer fc_live_valid_key")
    assert tenant_id == "expected_tenant_id"

def test_invalid_api_key():
    """Invalid API key returns 401"""
    with pytest.raises(HTTPException) as exc:
        verify_api_key("Bearer fc_live_invalid_key")
    assert exc.value.status_code == 401

# /tests/unit/test_rate_limit.py
def test_rate_limit_enforced():
    """Rate limit blocks after 100 requests"""
    for i in range(100):
        check_rate_limit("tenant_id")  # Should succeed

    with pytest.raises(HTTPException) as exc:
        check_rate_limit("tenant_id")  # 101st should fail
    assert exc.value.status_code == 429
```

### 7.2 Integration Tests

**Location:** `/tests/integration/`

```python
# /tests/integration/test_e2e_flow.py
@pytest.mark.asyncio
async def test_full_scrape_flow():
    """Test full flow: create job → process → get results"""

    # 1. Create tenant
    tenant = create_tenant('test@example.com')

    # 2. Create job
    response = requests.post('/v2/scrape', json={
        'url': 'https://example.com'
    }, headers={'Authorization': f'Bearer {tenant["api_key"]}'})

    assert response.status_code == 200
    job_id = response.json()['id']

    # 3. Wait for completion (poll)
    for _ in range(30):  # 30 seconds max
        status_response = requests.get(
            f'/v2/scrape/{job_id}',
            headers={'Authorization': f'Bearer {tenant["api_key"]}'}
        )

        if status_response.json()['status'] == 'completed':
            break

        await asyncio.sleep(1)

    # 4. Verify results
    assert status_response.json()['status'] == 'completed'
    assert 'data' in status_response.json()
    assert 'html_url' in status_response.json()['data']
```

### 7.3 Load Tests

**Location:** `/tests/load/`

**Run:**
```bash
locust -f tests/load/locust_test.py \
  --host http://localhost:8000 \
  --users 100 \
  --spawn-rate 20 \
  --run-time 10m
```

---

## 8. Operational Playbook

### 8.1 Deployment Process

**Production Deployment:**
```bash
# 1. Run migrations
docker exec -it api python -m alembic upgrade head

# 2. Deploy API (rolling update)
aws ecs update-service \
  --cluster scraping-platform \
  --service api \
  --force-new-deployment

# 3. Deploy workers (rolling update)
aws ecs update-service \
  --cluster scraping-platform \
  --service workers \
  --force-new-deployment

# 4. Smoke tests
curl https://api.scraping-platform.com/health
curl https://api.scraping-platform.com/metrics

# 5. Monitor for 30 minutes
# Watch Grafana dashboards for anomalies
```

### 8.2 Incident Response

**Runbook: High Error Rate (>5%)**

1. **Check Grafana Dashboard:**
   - Which endpoints are erroring?
   - Which tenants affected?
   - Error messages?

2. **Query CloudWatch Logs:**
   ```bash
   aws logs tail /ecs/api --follow --filter-pattern "ERROR"
   ```

3. **Check Dependencies:**
   - PostgreSQL connections: `SELECT count(*) FROM pg_stat_activity;`
   - Redis memory: `redis-cli INFO memory`
   - Worker queue depth: Check BullMQ metrics

4. **Mitigate:**
   - If database: Scale up RDS instance
   - If Redis: Evict old sessions
   - If workers: Scale out worker count
   - If proxy: Check BrightData status

5. **Rollback if needed:**
   ```bash
   aws ecs update-service --cluster scraping-platform --service api --task-definition api:previous
   ```

### 8.3 Backup & Recovery

**Daily Backups:**
- PostgreSQL: Automated RDS snapshots (30-day retention)
- S3: Versioning enabled (30-day lifecycle)

**Recovery:**
```bash
# Restore database from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier scraping-platform-restored \
  --db-snapshot-identifier scraping-platform-2026-02-15

# Restore S3 object
aws s3api get-object-version \
  --bucket scraping-platform \
  --key tenant_id/job_id/content.html \
  --version-id xxx
```

**RPO (Recovery Point Objective):** 1 hour
**RTO (Recovery Time Objective):** 4 hours

---

## 9. Financial Model (Adjusted)

### 9.1 First-Year Investment

| Item | Original Plan | **Adjusted Plan** | Delta |
|------|---------------|------------------|-------|
| Development (12 weeks) | $68,000 | $68,000 | $0 |
| Support (Month 8-12) | $0 | **$32,000** | +$32K |
| Security Audit | $0 | **$6,000** | +$6K |
| **TOTAL YEAR 1** | **$68,000** | **$106,000** | **+$38K** |

### 9.2 Monthly Profitability (Adjusted)

| Month | Free Users | Pro Customers | MRR | Infrastructure | Support | Proxy | Total Costs | **Profit** |
|-------|-----------|---------------|-----|---------------|---------|-------|-------------|------------|
| 4 | 100 | 0 | $0 | $680 | $0 | $0 | $680 | **-$680** |
| 7 | 500 | 50 | $3,750 | $1,155 | $0 | $750 | $1,905 | **+$1,845** |
| 8 | 700 | 80 | $6,000 | $1,155 | $4,000 | $1,387 | $6,542 | **-$542** |
| 10 | 1,200 | 150 | $11,250 | $1,500 | $4,000 | $2,100 | $7,600 | **+$3,650** |
| 12 | 2,000 | 200 | $15,000 | $1,915 | $8,000 | $2,800 | $12,715 | **+$2,285** |

**Key Changes:**
- **Pro pricing:** $75/month (was $50) = 50% higher revenue
- **Free tier:** 500 scrapes (was 1,000) = 50% lower costs
- **Proxy usage:** 40% (was 20%) = 2x higher costs (realistic)
- **Support hire:** $4K/month starting Month 8

**Break-Even:** Month 10 (was Month 7)

### 9.3 ROI Analysis

**Total Year 1 Investment:** $106,000
**Year 1 ARR:** $180,000 (200 Pro × $75/month × 12)
**ROI:** 1.7x (was 2.6x)

**Still positive, but more conservative.**

---

## 10. Success Metrics & Gates

### 10.1 Weekly Milestones

| Week | Milestone | Success Criteria | Risk |
|------|-----------|------------------|------|
| **3** | PoC Complete | ≥90% success, ≤2x latency, <500 LoC | HIGH - Could fail |
| **7** | API Production | 1000 req/min, auth working, RLS enforced | MEDIUM |
| **10** | Security Audit | Zero critical/high findings | MEDIUM |
| **12** | Anti-Detection | 92.5% success rate, cost controls active | LOW |
| **14** | Monitoring | Dashboards complete, alerts firing | LOW |
| **15** | Soft Launch | 10 beta users, 80% satisfaction | MEDIUM |

### 10.2 Month 4 Launch (Beta)

**Target Metrics:**
- ✅ 150 signups (was 500) - **ADJUSTED**
- ✅ 80%+ first-scrape success rate
- ✅ <0.5% security incidents
- ✅ NPS ≥30

**Launch Activities:**
1. HackerNews: "Show HN: Open-source Apify alternative ($75/month)"
2. GitHub: Release v1.0.0
3. Discord: Launch community server
4. Blog: "Why we built this" post

### 10.3 Month 12 Success

**Target Metrics:**
- ✅ 100 Pro customers (was 200) - **ADJUSTED**
- ✅ $7,500 MRR (was $10K) - **ADJUSTED**
- ✅ <5% monthly churn
- ✅ NPS ≥40
- ✅ 500+ GitHub stars

---

## Conclusion: Ready to Build

This comprehensive plan provides:
- ✅ **14-15 week realistic timeline** (adjusted from 12 weeks)
- ✅ **8 mandatory changes** to avoid critical failures
- ✅ **Day-by-day task breakdown** with file paths and acceptance criteria
- ✅ **Adjusted financial model** with realistic costs ($106K vs $68K)
- ✅ **Product & architect review** validating feasibility
- ✅ **Complete code examples** ready to implement
- ✅ **Testing strategy** with 80% coverage target
- ✅ **Operational playbooks** for production

**Success Probability:** 75-80% (up from 55-60% with original plan)

**Next Steps:**
1. **Week 1 (Starting Monday):** Begin PoC validation
2. **Week 3 (Friday):** GO/NO-GO decision
3. **Week 4 (If GO):** Start API development
4. **Week 15:** Soft launch to 10 beta users

**CRITICAL REMINDERS:**
- ✅ Week 2 PoC gate is MANDATORY - do NOT skip
- ✅ Security audit in Week 10 (not Month 9) - NON-NEGOTIABLE
- ✅ Hire support by Month 8 - REQUIRED to avoid burnout
- ✅ Proxy cost controls - ACTIVE from Day 1

---

**Document Version:** 3.0
**Last Updated:** 2026-02-03
**Prepared By:** Product Manager + Architect + Planning Team
**Next Review:** Week 3 (PoC completion)

**Ready to execute? Let's build this. 🚀**
