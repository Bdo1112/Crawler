# Mid-Planning Document: Executive Decision Report

**Date:** 2026-02-02
**Prepared By:** Product Design Team + Cloud Architecture Team
**For:** Final Decision Makers (CEO, CTO, Investors)

---

# Part 1: Product Design & Strategy

---

## 1. Executive Summary

### Opening: The Business Opportunity

The web scraping market is fragmented, expensive, and operationally complex. Enterprise solutions (Apify) start at $200/month. Self-hosted alternatives (Firecrawl) require 2-3 DevOps engineers. This creates a $500M+ TAM opportunity for a cost-effective, developer-friendly alternative.

**Our Opportunity:** Build an Apify-like multi-tenant platform (Crawlee-based) that is 50% cheaper, 80% simpler to operate, and 100% open-source. Target: data engineers, startups, and research teams that cannot afford proprietary solutions.

### Key Decisions

**1. Why Migrate from Firecrawl to Crawlee-Based Architecture**

| Criterion | Firecrawl | Crawlee Platform | Difference |
|-----------|-----------|------------------|-----------|
| **Infrastructure Cost** | $1,500-3,000/month | $965/month | 35-50% savings |
| **Operational Burden** | 50% team time | 20% team time | 2.5x reduction |
| **Services to Manage** | 7 services (18GB RAM) | 4 services (12GB RAM) | Simpler |
| **Time to MVP** | 4-8 weeks | 3-4 months | Manageable for 1-3 person team |
| **Code Salvage Rate** | N/A | 60% reusable | Anti-detection logic, patterns, routing |

**Recommendation:** Proceed with Crawlee migration. Risk is LOW given Week 1-2 PoC validation gate.

**2. Product We're Building: Multi-Tenant Scraping Platform**

Not a monolithic tool. A **platform** where:
- Teams log in, create API keys
- Each team has isolated quotas, data, and audit logs
- Single codebase scales to 1000s of teams
- Revenue from SaaS tiers (Free, Pro, Enterprise)

**Why Multi-Tenant?**
- Freemium model scales: $0 CAC for free users who convert to Pro ($600 LTV)
- Infrastructure efficient: $50 Pro customer costs only $5-10 to serve
- Competitive moat: lower costs enable lower prices

**3. Target Users (Market Segmentation)**

| Persona | Profile | TAM | Entry Point | LTV |
|---------|---------|-----|-----------|-----|
| **David - Data Engineer** | 5yr XP, Series A startup, Python | $2M | Free tier | $600 |
| **Sarah - ML Researcher** | PhD candidate, budget-constrained | $500K | Free tier | $100 |
| **Alex - CTO/SaaS Platform** | 10yr XP, internal platform, 5 teams | $100M | Enterprise | $10K+ |

**Total Addressable Market (TAM):** $100M+ (CTO segment alone; larger than Apify's current market)

**4. Go/No-Go Gate: Week 2 PoC Results**

Before committing full engineering resources, validate core assumptions:

| Criterion | Target | Gate Outcome |
|-----------|--------|--------------|
| **Success Rate** | ≥90% | Must pass to proceed |
| **Latency** | ≤2x Firecrawl | Acceptable trade-off |
| **Code Complexity** | <500 LoC | Simpler than Firecrawl fork |
| **Team Confidence** | High | Qualitative + quantitative |

**Timeline:** Week 1-2 PoC completes by Friday Feb 14, 2026. **Go decision required before Week 3 starts (Feb 17).**

### Business Case Summary

**Revenue Projection:**

| Metric | Month 4 | Month 7 | Month 12 | Month 18 |
|--------|---------|---------|----------|----------|
| **Free Users** | 100 | 500 | 1,000 | 2,000 |
| **Pro Customers** | 0 | 50 | 150 | 300 |
| **Enterprise Deals** | 0 | 0 | 3-5 | 15-20 |
| **MRR (Pro)** | $0 | $2,500 | $7,500 | $15,000 |
| **MRR (Enterprise)** | $0 | $0 | $2,500+ | $15,000+ |
| **Total MRR** | $0 | $2,500 | $10,000 | $30,000+ |
| **ARR** | $0 | $30K | $120K | $360K+ |

**Cost Structure:**

| Item | Month 7 | Month 12 | Month 18 |
|------|---------|----------|----------|
| **Infrastructure** | $965 | $1,500 | $3,500 |
| **Developer Salaries** | $0 | $0 | $0 |
| **Payroll (support)** | $0 | $2,000 | $4,000 |
| **Third-party (proxies)** | $500 | $1,000 | $2,000 |
| **Total OpEx** | $1,465 | $4,500 | $9,500 |

**Profitability:**

| Metric | Month 7 | Month 12 | Month 18 |
|--------|---------|----------|----------|
| **MRR** | $2,500 | $10,000 | $30,000 |
| **OpEx** | $1,465 | $4,500 | $9,500 |
| **Gross Profit** | $1,035 | $5,500 | $20,500 |
| **Gross Margin** | 41% | 55% | 68% |
| **Payback Period** | — | Month 12 | Fully profitable |

**Total Dev Cost (Months 1-12):** $46K (1 FTE developer, 12 weeks at $350/week base cost in startup environment)

**ROI:** $120K ARR by Month 12 on $46K investment = 2.6x return by year end. Break-even on developer cost: Month 9.

**Risk Level:** Low-Medium
- Technical: Low (Crawlee is production-proven)
- Market: Medium (need to validate PMF in free tier)
- Operational: Low (migrating known architecture)

**Contingency:** If PoC fails, return to Firecrawl optimization (less ambitious but still viable, $500K+ smaller revenue opportunity).

---

## 2. Product Vision & Market Positioning

### Problem Statement: Why Now?

**The Scraping Market is Broken:**

1. **Enterprise Solutions Too Expensive**
   - Apify: $200+/month minimum (100K scrapes)
   - Firecrawl: API-only, custom pricing, opaque costs
   - Cost per 1K scrapes: $0.50-1.50

2. **Self-Hosted Too Complex**
   - Firecrawl (open-source fork): 7 Docker services, 18GB RAM minimum
   - Requires 2-3 dedicated DevOps engineers
   - ~50% of small team time spent on maintenance
   - Not production-ready yet (per official Firecrawl docs)

3. **Developers Are Frustrated**
   - "I just need to scrape 50K pages/month, not a $2K/month service"
   - "I can't afford DevOps engineers to run Firecrawl"
   - "Why is there no Python-native scraping platform?"
   - "I want transparency—what am I actually paying for?"

**Market Validation:**
- HackerNews: 500+ upvotes on "Apify alternatives" threads (2024-2025)
- GitHub: 5K+ stars on web-scraping topics, 2K+ on Firecrawl fork
- Reddit r/webdev: 50+ posts/month asking for "cheap scraping" solutions
- LinkedIn: 1000+ connection requests to "scraping engineers"

### Our Solution: Apify-Like Platform (Crawlee-Based)

**What We're Building:**

1. **Open-Source Foundation**
   - GitHub public repo (MIT license)
   - Community contributions for anti-detection patterns
   - Transparent roadmap, security, costs
   - Builds trust (unlike proprietary Apify)

2. **SaaS + Self-Hosted Option**
   - Cloud option: managed infrastructure, webhooks, monitoring
   - Self-hosted option: Docker Compose, 4 services, single engineer can operate
   - Open-source ensures no lock-in

3. **Cost-Effective Model**
   - Infrastructure cost: $965/month for 300K jobs
   - Sell at 10-15x cost margin ($0.03-0.05/scrape)
   - Pro customer costs us $5-10/month to serve, sells for $50 ($600 LTV)

4. **Developer-First DX**
   - Python SDK (Jupyter notebook compatible)
   - Simple HTTP API (Firecrawl-compatible for migration)
   - 30-second setup: `pip install crawl-platform; token=sk-xyz; api.scrape(url)`

### Market Position Statement

**Messaging by Phase:**

**Phase 1 (Months 4-8): "Open-Source Apify Alternative with Transparent Pricing"**
- Competitor: Apify (closed, $200+/month)
- Differentiation: Open-source, no vendor lock-in, 50% cheaper
- Target: Developers, startups, researchers
- Positioning: Trust, cost, simplicity

**Phase 2 (Months 9-12): "The Developer-First Scraping Platform"**
- Competitor: Still Apify, now Firecrawl
- Differentiation: Python-native, Docker Compose, team operations
- Target: Data engineers, CTO/platforms
- Positioning: Developer experience, operational simplicity

**Phase 3 (Months 13+): "AI-Native Scraping + Data Extraction"**
- Competitor: ScrapeGraphAI, competitors in AI space
- Differentiation: Crawl + extract in one platform, LLM integration native
- Target: Enterprises, AI teams
- Positioning: AI enablement, data quality

### Competitive Differentiation

| Factor | Apify | Firecrawl | Our Platform | Winner |
|--------|-------|-----------|-------------|--------|
| **Pricing** | $200+/month | API only, custom | $50/month transparent | Ours |
| **Operational Complexity** | Managed | 7 services, complex | 4 services, simple | Ours |
| **Open-Source** | No | Partial (fork) | Yes, MIT | Ours |
| **Python-Native** | No (Node.js) | Yes (Python) | Yes (FastAPI) | Tie |
| **Self-Hosted** | No | Yes (hard) | Yes (simple) | Ours |
| **Anti-Detection** | Excellent | Good | Good (inherited) | Apify |
| **Community** | Small (corporate) | Medium (OSS) | Large (our goal) | TBD |
| **Cost per 1K Scrapes** | $0.60-1.50 | $0.50+ | $0.40-3.50 | Ours (low), Firecrawl (mid) |

**Why We Win:**
- Cheaper than Apify (transparency + open-source)
- Simpler than Firecrawl (4 services vs 7, managed stack)
- Better DX than both (Python, Jupyter, no lock-in)

**Why We Lose (Where Competitors Win):**
- Apify: 10-year brand, feature completeness, enterprise sales team
- Firecrawl: Already have Docker setup, might choose proven solution
- Our advantage: Growth, price-sensitive market, developer love

---

## 3. User Personas & Jobs-to-be-Done

### Persona 1: David - Data Engineer at Series A Startup

**Profile:**
- 5 years experience (2-3 companies)
- Python expert, some DevOps knowledge
- Startup equity-motivated, risk-tolerant
- Works at 20-100 person company

**Current Situation:**
- Needs to scrape 100K pages/month for ML training data
- Apify costs $500/month (5% of data budget), plus $2K onboarding
- Built internal scraper but brittle (breaks every 2 weeks)
- No dedicated DevOps—engineer time is more expensive

**Pain Points:**
- Apify too expensive ($500/month eats margin on projects)
- Firecrawl too complex (setup took 2 weeks, still flaky)
- Internal solution not reliable (missing Cloudflare handling)
- Rate limiting killed by target sites (needs rotation)
- No audit trail (compliance requirement for data collection)

**Jobs-to-be-Done:**

1. **"Scrape 100K pages/month reliably"**
   - Success: 95%+ success rate, auto-retry on failures
   - Timeline: Monthly, on-demand throughout month
   - Current solution: Custom Python + Selenium (breaks weekly)
   - Desired: "Black box" API that just works

2. **"Integrate with data pipeline (pandas, SQL)"**
   - Success: Results directly into Redshift/BigQuery
   - Timeline: Daily, automatic
   - Current solution: Manual export to CSV, pandas read_csv
   - Desired: Direct stream to data warehouse

3. **"Track cost per scrape"**
   - Success: Understand economics (is this worth $500/month?)
   - Timeline: Daily dashboard, monthly reports
   - Current solution: Guesswork ("roughly 100K pages")
   - Desired: "Exact cost attribution: $0.003 per successful scrape"

4. **"Handle rate limiting gracefully"**
   - Success: Automatic backoff, rotate proxies, respect robots.txt
   - Timeline: Should be invisible
   - Current solution: Hard-coded delays (slow)
   - Desired: Intelligent retry with proxy rotation

5. **"Monitor data quality"**
   - Success: Alert if success rate drops <90%
   - Timeline: Real-time monitoring
   - Current solution: Manual checks
   - Desired: Slack notification on job failure

**Success Metrics (Quantified):**
- Success rate: >95%
- Cost per scrape: <$0.01 (vs $0.005 for Apify, acceptable)
- Time to first scrape: <2 minutes (setup)
- MTTR (mean time to recovery): <5 minutes
- Operational overhead: <5 hours/month

**Buying Criteria (Ranked):**
1. **Pricing** - Most critical (cost-sensitive startup)
2. **Developer experience** - API-first, Python, no DevOps
3. **Performance** - 95%+ success, <5s latency
4. **Community** - Help from Slack/forum, not paid support

**Deal Size:** $50/month Pro (10K scrapes) = $600 LTV, potential upgrade to $500/month custom at scale

---

### Persona 2: Sarah - ML Researcher at University

**Profile:**
- PhD candidate, computer science
- Python expert, academic focus
- Budget-constrained (no funding)
- Building public dataset for research

**Current Situation:**
- Needs to scrape 50K academic papers/month from journals
- Many sites have Cloudflare protection (unacademic but common)
- Can run on research server (own hardware)
- Academic ethics: must respect robots.txt, rate limits

**Pain Points:**
- Cannot afford Apify ($200+/month, no grant funding)
- Firecrawl too complex (no DevOps background)
- Many sites block naive requests (need anti-detection)
- Need offline capability (no cloud account available)
- Academic ethics: must be transparent (open-source preferred)

**Jobs-to-be-Done:**

1. **"Bypass Cloudflare/bot protection"**
   - Success: 90%+ success on protected sites
   - Timeline: One-time setup, runs daily
   - Current solution: None (stuck on protected sites)
   - Desired: Automatic handling, no code changes

2. **"Scrape 50K pages/month on limited hardware"**
   - Success: Full content extraction (HTML → JSON)
   - Timeline: Monthly batch, can run overnight
   - Current solution: Requests + BeautifulSoup (breaks on JS)
   - Desired: Out-of-the-box solution, memory-efficient

3. **"Export to academic formats (BibTeX, JSON)"**
   - Success: Structured data for analysis
   - Timeline: End of scrape job
   - Current solution: Manual pandas transforms
   - Desired: Built-in export formats

4. **"Run locally without cloud account"**
   - Success: Complete self-hosted on university server
   - Timeline: Deploy once, forget
   - Current solution: None (Apify/Firecrawl are cloud-only)
   - Desired: Docker Compose on Raspberry Pi

5. **"Document data provenance"**
   - Success: Know when/how data was collected (ethics)
   - Timeline: Per-job metadata
   - Current solution: Manual notes
   - Desired: Automatic, auditable, compliant

**Success Metrics (Quantified):**
- Success rate: >90% (even on protected sites)
- Cost: Free or <$10/month
- Memory usage: <2GB (research server constraint)
- Setup time: <1 hour

**Buying Criteria (Ranked):**
1. **Cost** - Free if possible, max $10/month
2. **Anti-detection** - Must handle Cloudflare
3. **Self-hosted** - Offline execution only
4. **Open-source** - Trust, transparency, academic use

**Deal Size:** Free tier or $10/month (self-hosted), represents community advocacy value

---

### Persona 3: Alex - CTO at B2B SaaS Company

**Profile:**
- 10 years experience (3-4 companies, Series B+ current)
- Full-stack engineer, operations-minded
- Leads 5 data engineer team
- Manages internal platforms, budgets, vendor relationships

**Current Situation:**
- Building internal multi-tenant scraping platform for 5 teams
- Currently using Firecrawl self-hosted (complex, flaky)
- Processes 1M+ internal scrapes/month
- Costs: $2K infrastructure + 50% engineer time = $10K/month all-in

**Pain Points:**
- Firecrawl too complex: 7 Docker services, constant DevOps burden
- Operational overhead: 50% of engineer time on infrastructure
- Cost: $2K/month infrastructure for self-hosted (should be $500)
- Scaling: Every 200K scrapes/month requires new VM, manual work
- Multi-tenancy: Built custom RLS, should be in platform

**Jobs-to-be-Done:**

1. **"Build internal platform for 5 engineering teams"**
   - Success: Each team has API key, isolated quotas, audit logs
   - Timeline: Deploy once, manage for 12+ months
   - Current solution: Custom Firecrawl fork (nightmare)
   - Desired: Turn-key multi-tenant platform

2. **"Scale to 1M+ scrapes/month efficiently"**
   - Success: Auto-scaling, cost per scrape decreases as volume increases
   - Timeline: Transparent (ops team should understand it)
   - Current solution: Add VMs, pray it works
   - Desired: Automatic load balancing, no manual intervention

3. **"Track usage per team for chargeback"**
   - Success: Per-team billing, quotas enforced, real-time usage
   - Timeline: Monthly reports, real-time dashboard
   - Current solution: Rough estimates from logs
   - Desired: Exact per-API-key metrics

4. **"Reduce operational burden to <20% engineer time"**
   - Success: One engineer can manage for 5 teams
   - Timeline: Ongoing
   - Current solution: 50% (1 engineer full-time on infra)
   - Desired: <10 hours/week on ops

5. **"Maintain 99.9% uptime for internal SLA"**
   - Success: Monitoring, alerting, runbooks for common issues
   - Timeline: Always on
   - Current solution: Manual firefighting
   - Desired: Automated, predictable, monitored

**Success Metrics (Quantified):**
- Uptime: 99.9% (within SLA)
- Cost: <$1K/month for 1M scrapes (vs $2K now)
- Ops time: <20% engineer time (vs 50% now)
- Setup time: <1 week for new team
- MTTR: <30 minutes for any incident

**Buying Criteria (Ranked):**
1. **Operational simplicity** - 4 services vs 7, managed
2. **Cost efficiency** - $1K vs $2K (50% savings)
3. **Multi-tenancy support** - Built-in, RLS, quotas
4. **Professional support** - SLA, dedicated contact
5. **Feature completeness** - Don't want to build more

**Deal Size:** $1,000-2,000/month custom enterprise = $12K-24K ARR, grows with volume

---

### Jobs-to-be-Done Summary

| Job | David (Startup) | Sarah (Research) | Alex (CTO) |
|-----|-----------------|------------------|-----------|
| **Primary Job** | Scrape reliably | Bypass protection | Multi-tenant ops |
| **Secondary Job** | Integrate pipeline | Offline execution | Cost attribution |
| **Success Metric** | $0.01/scrape | Free, 90% success | 99.9% uptime |
| **Buying Signal** | Pricing transparency | Open-source | Managed services |

**Our Product Must Support All Three:**
- David: Cheap, easy, built-in integration
- Sarah: Self-hosted, anti-detection, open-source
- Alex: Multi-tenancy, monitoring, professional support

---

## 4. MVP Feature Set with Rationale

### Must-Have Features for MVP (Month 4 Launch)

We are ruthlessly focused. Only features that directly support product-market fit and revenue generation.

#### 1. Core Scraping API

**Feature:** POST /v2/scrape, GET /v2/scrape/{id}

**Why Must-Have:**
- This IS the product (core value proposition)
- Firecrawl-compatible (easier migration for existing users)
- Enables all three personas to use the platform

**Product Impact:**
- David: "I can call one endpoint and scrape any URL"
- Sarah: "Same API in Jupyter notebooks"
- Alex: "Can integrate into internal platform immediately"

**User Value:**
- Single endpoint for all scraping needs
- No need to learn multiple tools
- Direct replacement for Apify/Firecrawl

**Timeline:** Week 3-4 (part of API layer build)

**Technical Details:**
```
POST /v2/scrape
{
  "url": "https://example.com",
  "method": "http|browser|auto",  # Intelligent escalation
  "formats": ["markdown|html|json"],
  "timeout": 30,
  "headless": true
}

Response:
{
  "job_id": "job_12345",
  "status": "queued|running|completed|failed",
  "data": {
    "html": "...",
    "markdown": "...",
    "success": true,
    "elapsed_ms": 1500
  }
}
```

**Acceptance Criteria:**
- [ ] Returns job ID immediately (async processing)
- [ ] Polling with GET /v2/scrape/{id} works
- [ ] Handles timeouts, retries, failures gracefully
- [ ] OpenAPI documentation auto-generated
- [ ] <100ms latency on API call (response time), not scrape

---

#### 2. 3-Layer Anti-Detection System

**Feature:** Automatic escalation from HTTP → Browser → Proxies

**Why Must-Have:**
- This is the competitive differentiator vs dumb HTTP clients
- 90%+ of websites require some form of handling
- Makes platform useful for real-world scraping

**Product Impact:**
- David: "Works on protected sites without code changes"
- Sarah: "Cloudflare sites just work"
- Alex: "No need for external FlareSolverr service"

**User Value:**
- Automatic—user doesn't think about layers
- Intelligent routing based on URL/pattern
- Cost-efficient (try cheap method first, escalate only if needed)

**Timeline:** Week 7-8 (depends on PoC validation)

**Technical Details:**

```
Layer 1: curl_cffi (TLS fingerprinting)
  - No JavaScript execution
  - ~50ms latency
  - Cost: $0.00 (included)
  - Success: ~70% of sites

Layer 2: Crawlee HTTP (Session management)
  - Light JavaScript handling
  - ~200-500ms latency
  - Cost: $0.001 per request
  - Success: ~85% of sites

Layer 3: Crawlee Playwright (Full browser)
  - Full JavaScript execution
  - ~2-5s latency
  - Cost: $0.005 per request
  - Success: ~95% of sites

Layer 4: BrightData Proxies (Rotation)
  - IP rotation + browser
  - ~500ms+ latency
  - Cost: $0.02 per request
  - Success: ~98% of sites

Layer 5: FlareSolverr (Cloudflare solver)
  - Dedicated challenge solver
  - ~10-30s latency
  - Cost: $0.05 per request
  - Success: ~99% of Cloudflare sites
```

**Automatic Escalation Logic:**
```
if challenge_pattern(response):
  if "cloudflare" in challenge_pattern:
    use_flaresolverr()  # Fast track Cloudflare
  else:
    if layer == 1:
      retry(layer=2)  # HTTP → Browser
    elif layer == 2:
      retry(layer=3, use_proxy=true)  # Add proxy rotation
    elif layer == 3:
      retry(layer=4)  # Premium proxy
    else:
      fail()  # All layers exhausted
```

**Acceptance Criteria:**
- [ ] Layer 1 (curl_cffi) handles 70% of test sites
- [ ] Layer 2 (Browser) handles 85% of test sites
- [ ] Layer 3 (Proxies) handle 95% of test sites
- [ ] Automatic escalation works correctly
- [ ] Cost tracking per layer per request
- [ ] Zero manual intervention needed

---

#### 3. Multi-Tenant Isolation (PostgreSQL RLS)

**Feature:** Tenant data separation at database layer

**Why Must-Have:**
- Foundation for SaaS business (without it, can't do freemium)
- Security requirement (enterprise will demand it)
- Enables billing/quota enforcement
- Competitive requirement vs Apify (who have this)

**Product Impact:**
- David: "My scrape data is private, not accessible to other users"
- Sarah: "University data stays in our bucket"
- Alex: "Internal platform can serve 5 teams securely"

**User Value:**
- No data leakage (technical guarantee)
- Per-tenant quotas (fairness)
- Per-tenant audit logs (compliance)
- Trust (security is product feature)

**Timeline:** Week 5-6

**Technical Details:**

```sql
-- Schema with RLS
CREATE TABLE tenants (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  tier VARCHAR DEFAULT 'free',  -- free|pro|enterprise
  created_at TIMESTAMP
);

CREATE TABLE scrape_jobs (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id),
  url VARCHAR NOT NULL,
  status VARCHAR,  -- queued|running|completed|failed
  result JSONB,
  created_at TIMESTAMP,
  completed_at TIMESTAMP
);

-- Row-Level Security
ALTER TABLE scrape_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON scrape_jobs
  USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- Usage: SELECT * FROM scrape_jobs;
-- Returns only rows for current tenant (enforced by DB)
```

**Acceptance Criteria:**
- [ ] RLS enforced at database layer (not application)
- [ ] SELECT/INSERT/UPDATE/DELETE filtered by tenant
- [ ] Multiple tenants cannot see each other's data
- [ ] Audit logging per tenant
- [ ] Zero data leakage in tests

---

#### 4. Rate Limiting & Quotas

**Feature:** Per-tenant request limits, per-second throttling

**Why Must-Have:**
- Prevents abuse (free tier can't DDoS)
- Enables tiered pricing (free: 1K, pro: 10K)
- Protects infrastructure
- Monetization lever (upsell when quota exceeded)

**Product Impact:**
- David: "Predictable costs ($50/month = 10K scrapes, no surprises)"
- Sarah: "Free tier allows 1K/month (reasonable for research)"
- Alex: "Internal team can't accidentally spend $5K in one query"

**User Value:**
- Cost predictability (no bill shock)
- Fairness (one user can't hog resources)
- Transparency (real-time usage tracking)

**Timeline:** Week 5-6 (part of multi-tenancy)

**Technical Details:**

```python
# Rate Limiting Implementation
TIER_QUOTAS = {
  "free": 1_000,      # per month
  "pro": 10_000,      # per month
  "enterprise": None  # unlimited
}

# Per-second limits (prevent burst abuse)
RATE_LIMITS = {
  "free": 1,           # 1 req/sec (60/min)
  "pro": 10,           # 10 req/sec (600/min)
  "enterprise": 100    # 100 req/sec
}

# Enforcement
@app.post("/v2/scrape")
async def scrape(request: ScrapeRequest):
  tenant_id = get_current_tenant()

  # Check monthly quota
  usage = get_monthly_usage(tenant_id)
  if usage >= TIER_QUOTAS[tier]:
    raise HTTPException(
      status_code=429,
      detail="Monthly quota exceeded. Upgrade to Pro."
    )

  # Check rate limit (sliding window)
  if not rate_limit.allow(tenant_id):
    raise HTTPException(
      status_code=429,
      detail=f"Rate limit: {RATE_LIMITS[tier]}/sec"
    )

  return create_job()
```

**Acceptance Criteria:**
- [ ] Free tier limited to 1K scrapes/month
- [ ] Pro tier limited to 10K scrapes/month
- [ ] Per-second limits enforced (prevent burst abuse)
- [ ] Usage tracking accurate (billing relies on this)
- [ ] Clear error messages when quota exceeded

---

#### 5. Basic Monitoring (Prometheus + Grafana)

**Feature:** Metrics, dashboards, alerts on platform health

**Why Must-Have:**
- Production readiness (can't run without observability)
- Incident response (need data to debug)
- Transparency (show customers platform is healthy)
- Operational confidence (team knows what's happening)

**Product Impact:**
- David: "Dashboard shows my scrapes are working (builds confidence)"
- Sarah: "Can see when jobs failed and why"
- Alex: "Can build SLA dashboard for internal teams"

**User Value:**
- Transparency (know your scrapes are running)
- Debugging (understand failures)
- Trust (see platform stability metrics)

**Timeline:** Week 9-10

**Technical Details:**

```python
# Prometheus Metrics
scrape_jobs_total = Counter(
  'scrape_jobs_total',
  'Total scrape jobs attempted',
  ['status', 'tier', 'method']
)

scrape_job_duration = Histogram(
  'scrape_job_duration_seconds',
  'Scrape job duration',
  ['method'],
  buckets=(1, 5, 10, 30, 60)
)

scrape_success_rate = Gauge(
  'scrape_success_rate',
  'Percentage of successful scrapes',
  ['method', 'tier']
)

# Grafana Dashboards
Dashboards:
  - Platform Health (uptime, error rate, latency)
  - Per-Method Performance (HTTP vs Browser vs Proxy)
  - Per-Tenant Usage (top customers, quota consumption)
  - System Resources (CPU, memory, disk)

# Alerts (via PagerDuty/Slack)
- Error rate >5% → Warning
- Error rate >10% → Critical
- P95 latency >30s → Warning
- Infrastructure CPU >80% → Warning
```

**Acceptance Criteria:**
- [ ] Prometheus metrics exported on /metrics endpoint
- [ ] Grafana dashboards created for key metrics
- [ ] Alerts configured for critical issues
- [ ] <5% performance overhead from instrumentation
- [ ] Customer-facing uptime page (simple)

---

### Feature Priority Matrix (RICE Scoring)

| Feature | Reach | Impact | Confidence | Effort | Score | Priority | Why |
|---------|-------|--------|-----------|--------|-------|----------|-----|
| **Scraping API** | 100% | 10/10 | High | 40hr | 6.25 | **P0** | Core value prop |
| **Anti-Detection** | 80% | 10/10 | High | 60hr | 4.00 | **P0** | Differentiator |
| **Multi-Tenancy** | 60% | 10/10 | High | 80hr | 2.50 | **P0** | SaaS foundation |
| **Rate Limiting** | 50% | 9/10 | High | 30hr | 5.00 | **P0** | Monetization lever |
| **Monitoring** | 40% | 8/10 | High | 40hr | 3.00 | **P0** | Operational readiness |
| **Dashboard UI** | 30% | 7/10 | Medium | 60hr | 1.05 | P1 | Nice-to-have, Postman sufficient |
| **Webhooks** | 20% | 6/10 | Low | 40hr | 0.50 | P2 | Polling sufficient for MVP |
| **Scheduled Scrapes** | 15% | 6/10 | Low | 40hr | 0.38 | P2 | Users can cron externally |
| **Actor Marketplace** | 10% | 8/10 | Low | 80hr | 0.25 | P3 | Need user base first |
| **OAuth/SSO** | 5% | 7/10 | Medium | 40hr | 0.22 | P3 | Free tier doesn't need |
| **LLM Extraction** | 5% | 9/10 | Medium | 120hr | 0.15 | P3 | Phase 3 feature (separate tier) |

**Rationale for Deferred Features:**

| Feature | Why Deferred | When to Reconsider | Effort Estimate |
|---------|-------------|-------------------|-----------------|
| **Dashboard UI** | Postman + API docs sufficient for MVP | When free tier >500 users | 3-4 weeks |
| **Webhooks** | Polling is simpler, less breakage | Month 8 (after revenue) | 2-3 weeks |
| **Scheduled Scrapes** | Users can cron externally (not our job) | Month 9 (requested by customers) | 2-3 weeks |
| **Actor Marketplace** | Need user base + community first | Month 13 (1K+ users) | 4-6 weeks |
| **OAuth/SSO** | API keys work fine for MVP, enterprise in Month 12 | Month 12 (enterprise sales) | 2-3 weeks |
| **LLM Extraction** | AI-first feature (Phase 3), separate product | Month 13+ (validate core first) | 6-8 weeks |

**Timeline Impact:**
- Must-haves (P0): 250 hours of development = 6-7 weeks with 1 developer
- This aligns with our 4-month timeline (Week 1-2 PoC, Week 3-12 development)

---

## 5. Monetization Strategy

### Market Context: Pricing Opportunities

**Current Market:**
- Apify: $200+/month (managed service)
- Firecrawl: Custom API pricing (opaque)
- ScrapeGraphAI: $20-100/month (LLM-based)
- No clear "freemium" player

**Opportunity:** Fill the freemium gap (free → $50 → custom) with transparent pricing.

### Proposed Pricing Tiers

**Tier 1: Free (Forever)**

| Attribute | Value |
|-----------|-------|
| **Price** | $0/month |
| **Scrapes/month** | 1,000 |
| **Success Rate Guarantee** | 85% (HTTP only, no browser) |
| **Features** | Basic API, community support |
| **Support Channel** | Discord/GitHub issues (community) |
| **RPS Limit** | 1 request/second |
| **SLA** | Best effort (no uptime guarantee) |
| **Use Cases** | Evaluation, small scripts, research |

**Tier 2: Pro**

| Attribute | Value |
|-----------|-------|
| **Price** | $50/month (or $500/year, 17% discount) |
| **Scrapes/month** | 10,000 |
| **Success Rate Guarantee** | 95% (browser + anti-detection) |
| **Features** | Full API, email support, usage dashboard |
| **Support Channel** | Email (24-48 hr response) |
| **RPS Limit** | 10 requests/second |
| **SLA** | 99% uptime (no refund, but monitored) |
| **Use Cases** | Startups, small teams, production scraping |

**Tier 3: Enterprise**

| Attribute | Value |
|-----------|-------|
| **Price** | Custom ($1,000-5,000+/month) |
| **Scrapes/month** | Unlimited (or contracted) |
| **Success Rate Guarantee** | 99% (dedicated resources) |
| **Features** | Everything + webhooks, scheduled scrapes, priority support |
| **Support Channel** | Slack + phone (dedicated account manager) |
| **RPS Limit** | 100+ requests/second (negotiable) |
| **SLA** | 99.9% uptime with refund clause |
| **Use Cases** | Enterprises, data agencies, large platforms |

### Unit Economics

**Cost per 1,000 Scrapes (Delivered to Customer):**

| Metric | HTTP Only | Browser + Proxy | Browser + Dedicated |
|--------|-----------|-----------------|-------------------|
| **Compute** | $0.40 | $3.00 | $5.00 |
| **Proxy/IP** | $0.00 | $2.00 | $3.00 |
| **Storage** | $0.01 | $0.10 | $0.20 |
| **Total Cost** | **$0.41** | **$5.10** | **$8.20** |

**Gross Margin by Tier:**

| Tier | Price/1K Scrapes | Cost/1K | Margin $ | Margin % | Notes |
|------|-----------------|---------|----------|----------|-------|
| **Free (HTTP)** | $0.00 | $0.41 | -$0.41 | -100% | We lose money; acceptable (CAC = 0) |
| **Pro (Mixed)** | $5.00 | $5.10 | -$0.10 | -2% | Nearly break-even; subsidized by upmarket |
| **Pro (Browser)** | $5.00 | $5.10 | -$0.10 | -2% | Customers self-select based on need |
| **Enterprise** | $10-50+ | $5.10-8.20 | $5-45 | 50-90% | High margin (scale of use) |

**Alternative View (Per Customer):**

| Segment | Monthly Revenue | Monthly Cost | Gross Profit | Gross Margin |
|---------|-----------------|--------------|--------------|--------------|
| **Free user (1K scrapes)** | $0 | $1.64 | -$1.64 | -∞ |
| **Pro customer (10K scrapes)** | $50 | $51.00 | -$1.00 | -2% |
| **Pro customer (10K mixed)** | $50 | $30 | $20 | 40% |
| **Enterprise (1M scrapes)** | $2,000 | $1,000 | $1,000 | 50% |

**This looks bad. Let's explain:**

1. **Free tier is a CAC loss leader, not a profit center**
   - LTV of free user = $600 (converts to Pro in Month 6-12)
   - CAC of free user = $0 (organic)
   - LTV:CAC = ∞ (break-even on conversion)

2. **Pro tier is volume-dependent**
   - Light users (1K scrapes/month): We lose money, but...
   - Heavy users (10K scrapes/month): We make 40% margin
   - Average Pro customer: 5K scrapes = 20% margin ($10 profit)

3. **Enterprise is where we make money**
   - 1M scrapes/month @ $2K = 50% margin ($1K/month)
   - Only 3-5 enterprise customers needed to be profitable

### Projected MRR & Growth

**Year 1 Progression:**

| Month | Free Users | Pro Customers | Enterprise | Free MRR | Pro MRR | Enterprise MRR | Total MRR | Cumulative Revenue |
|-------|-----------|---------------|-----------|---------|---------|----------------|-----------|-------------------|
| 4 | 50 | 0 | 0 | $0 | $0 | $0 | $0 | $0 |
| 5 | 150 | 5 | 0 | $0 | $250 | $0 | $250 | $250 |
| 6 | 300 | 15 | 0 | $0 | $750 | $0 | $750 | $1,000 |
| 7 | 500 | 50 | 0 | $0 | $2,500 | $0 | $2,500 | $3,500 |
| 8 | 700 | 80 | 1 | $0 | $4,000 | $1,000 | $5,000 | $8,500 |
| 9 | 900 | 120 | 2 | $0 | $6,000 | $2,000 | $8,000 | $16,500 |
| 10 | 1,200 | 150 | 3 | $0 | $7,500 | $3,000 | $10,500 | $27,000 |
| 11 | 1,500 | 180 | 4 | $0 | $9,000 | $4,000 | $13,000 | $40,000 |
| 12 | 2,000 | 200 | 5 | $0 | $10,000 | $5,000 | $15,000 | $55,000 |

**Year 2 Projection (Months 13-18):**

| Month | Free Users | Pro Customers | Enterprise | Pro MRR | Enterprise MRR | Total MRR |
|-------|-----------|---------------|-----------|---------|----------------|-----------|
| 13 | 3,000 | 250 | 8 | $12,500 | $8,000 | $20,500 |
| 14 | 4,000 | 300 | 10 | $15,000 | $10,000 | $25,000 |
| 15 | 5,000 | 350 | 12 | $17,500 | $12,000 | $29,500 |
| 16 | 6,500 | 400 | 15 | $20,000 | $15,000 | $35,000 |
| 17 | 8,000 | 450 | 18 | $22,500 | $18,000 | $40,500 |
| 18 | 10,000 | 500 | 20 | $25,000 | $20,000 | $45,000 |

**Key Assumptions:**
- Conversion: 5% of free users convert to Pro per month (conservative)
- Churn: 2% Pro churn, 1% Enterprise churn (very good)
- Enterprise ACV: $1,000/month average (some pay $500, some $5K+)
- Free tier grows due to word-of-mouth (Slack, HN, GitHub)

### Go-to-Market Timeline

| Phase | Duration | Goal | Success Metric | Launch Activities |
|-------|----------|------|----------------|-------------------|
| **Alpha** | Months 1-3 | Internal validation | 3+ internal scrapers | N/A (internal only) |
| **Beta** | Months 4-6 | Free tier adoption | 500 signups, 80% activation | Launch HN, blog, GitHub, Discord |
| **Pro Launch** | Months 7-9 | Revenue generation | 50+ Pro customers, $5K MRR | Email existing beta, content marketing |
| **Enterprise** | Months 10-12 | Enterprise deals | 3-5 deals, $5K+ MRR | Outbound sales, partnerships |
| **Scale** | Months 13-18 | Growth | 200+ customers, $30K+ MRR | Product-led growth, affiliate program |

**Launch Strategy (Month 4 - Public Beta):**

1. **HackerNews (Week 1)**
   - Submit "Show HN: Apify alternative, $50/month"
   - Target >500 upvotes (plausible for this niche)
   - Drive 2,000-3,000 visits, 50-100 signups

2. **GitHub Announcement (Week 1)**
   - Release v0.1.0 with open-source code
   - Target 100 stars in first week, 500+ by Month 5
   - Drive community contributions (anti-detection patterns)

3. **Blog Post Series (Week 2-3)**
   - "Why we built an open-source scraping platform"
   - "Crawlee vs Apify vs Scrapy"
   - "Self-hosting scraping infrastructure: cost analysis"
   - Drive SEO traffic, establish thought leadership

4. **Discord Community (Week 1)**
   - Launch Discord server
   - Target: 500+ members by Month 6
   - Support, feature requests, beta testing

5. **Twitter/LinkedIn (Ongoing)**
   - Announce milestones, feature releases
   - Target early adopters, developers

### Pricing Strategy Rationale

**Why $50/month for Pro?**

1. **Price Point Psychology**
   - Below Apify ($200/month) by 4x
   - Above "toy" tools ($1-5/month)
   - Feels expensive enough to be "enterprise" but affordable for startups

2. **Unit Economics**
   - 10K scrapes/month at $50 = $5/1K scrapes (sell price)
   - Cost is $5.10/1K scrapes (HTTP) to $30/1K (browser)
   - Pro customers are profitable at scale (mix of HTTP + browser)

3. **Competitive Positioning**
   - Apify: $200 (4x more)
   - Crawl4AI: $20-50 (similar)
   - ScrapeGraphAI: $100+ (more expensive)
   - Our position: "Best price for feature set"

4. **LTV & CAC Relationship**
   - Free user converts at ~5% per month (conservative)
   - Average customer lifetime: 12-18 months
   - LTV: $50 × 15 months × 95% retention = $712.50
   - CAC: $0 (organic) or $50-100 (when we do ads)
   - LTV:CAC = 7-14x (great business)

5. **Freemium Conversion Math**
   - Need 500 free users → 50 Pro customers @ 10% conversion
   - 50 Pro customers × $50 = $2.5K MRR (our Month 7 target)
   - This is achievable if we get virality

---

## 6. Product Metrics & OKRs

### North Star Metric: Weekly Active Scrapers (WAS)

**Definition:** Unique API keys that made ≥1 successful request in the past 7 days

**Why This Metric?**
- Proxy for active, engaged users (they're using the product)
- Not vanity (anyone can sign up free)
- Not revenue-dependent (captures growth before monetization)
- Comparable to similar platforms (Apify uses similar)

**Target Trajectory:**
| Month | WAS | Free Users | Pro Customers | Implied Conversion |
|-------|-----|-----------|---------------|-------------------|
| 4 | 50 | 100 | 0 | 0% |
| 6 | 150 | 300 | 15 | 5% |
| 8 | 300 | 700 | 80 | 11% |
| 10 | 400 | 1,200 | 150 | 13% |
| 12 | 500 | 2,000 | 200 | 10% |
| 18 | 1,000 | 10,000 | 500 | 5% |

**Dashboard Tracking:**
```
KPI: Weekly Active Scrapers
  ├─ WAS (primary)
  ├─ Free users who are active (% of 100)
  ├─ Pro customers who are active (% of 100)
  ├─ Conversion rate: Active Pro / Active Free
  └─ Trend: 7-day moving average
```

### OKRs by Phase

#### Phase 1 (Months 1-6): Validate Product-Market Fit

**Objective 1: Validate Core Product (Tech + Product)**

**Key Results:**
- KR1: Build 3+ internal scrapers on platform (success rate >90%)
  - Measure: Count of internal projects using platform
  - Target: Email, database indexing, Slack integration (3 realistic targets)
  - Timeline: By end of Month 3
  - Owner: Tech lead

- KR2: Document cost model ($<0.01/scrape)
  - Measure: Real cost tracking data from PoC
  - Target: Prove unit economics work (profitability possible)
  - Timeline: By end of Week 2 PoC
  - Owner: Product manager

- KR3: Team rates >4/5 on ease-of-use (internal survey)
  - Measure: 1-5 Likert scale survey
  - Target: David/Sarah/Alex personas all rate 4+
  - Timeline: End of Month 3
  - Owner: Product manager

**Success Definition:** If all KRs are green, proceed to public beta. If any KR is red, investigate and pivot.

**Objective 2: Build Free Tier Product-Market Fit**

**Key Results:**
- KR1: 500+ beta signups by Month 6
  - Measure: Signup tracking (Mixpanel or Amplitude)
  - Target: 1-2 per day initial, ramping to 10+/day post-launch
  - Timeline: By Month 6
  - Owner: Marketing + community

- KR2: 80%+ first scrape success rate
  - Measure: (succeeded on first try) / (total first attempts)
  - Target: User onboarding is frictionless
  - Timeline: Continuous (target by Month 5)
  - Owner: Product + engineering

- KR3: <0.5% security incidents
  - Measure: (security incidents) / (total users)
  - Target: Multi-tenancy holds up under real usage
  - Timeline: Continuous
  - Owner: Engineering + security

**Success Definition:** If all KRs are green, we have product-market fit for free tier. Ready to charge.

---

#### Phase 2 (Months 7-12): Achieve Business Model Viability

**Objective 1: Achieve Profitability & Scale**

**Key Results:**
- KR1: 200+ Pro customers by Month 12
  - Measure: Pro tier signups
  - Target: Aggressive growth from free tier
  - Timeline: Ramp from 5 (Month 5) → 50 (Month 7) → 200 (Month 12)
  - Owner: Sales + marketing (product-led growth)

- KR2: $10K+ MRR by Month 12
  - Measure: Monthly Recurring Revenue (non-refundable)
  - Target: 200 × $50 = $10K (all from Pro tier)
  - Timeline: Build up Month 7-12
  - Owner: Finance + sales

- KR3: <5% monthly churn
  - Measure: (Pro customers churned) / (Pro customers start of month)
  - Target: Strong retention (healthy business)
  - Timeline: Continuous (achieved by Month 8)
  - Owner: Product + support

- KR4: NPS >40 (from Pro customers)
  - Measure: "How likely would you recommend? (0-10)" survey
  - Target: Promoters (9-10) - Detractors (0-6) = >40
  - Timeline: Monthly surveys, target by Month 9
  - Owner: Product + marketing

**Success Definition:** If all KRs are green, we have a sustainable business. Profitability in Month 12.

**Objective 2: Build Brand & Community**

**Key Results:**
- KR1: 1K GitHub stars
  - Measure: GitHub star count
  - Target: Signals credibility, open-source adoption
  - Timeline: By Month 12
  - Owner: Marketing + community

- KR2: 500+ Discord members
  - Measure: Active Discord members
  - Target: Healthy community, low-touch support
  - Timeline: By Month 12
  - Owner: Community manager

- KR3: 10 published blog posts (SEO-driven)
  - Measure: Blog post count, target keywords ranking
  - Target: Drive organic traffic, establish expertise
  - Timeline: 1-2 per month
  - Owner: Marketing

**Success Definition:** Strong brand presence. Position for enterprise sales (Month 13+).

---

#### Phase 3 (Months 13-18): Growth & Expansion

**Objective 1: Scale Revenue & Profitability**

**Key Results:**
- KR1: 500+ total customers (Pro + Enterprise)
  - Measure: Total paying customers
  - Target: Explosive growth (200 → 500, 2.5x)
  - Timeline: By Month 18
  - Owner: Sales

- KR2: $30K+ MRR
  - Measure: Monthly Recurring Revenue
  - Target: 200 Pro × $50 + 20 Enterprise × $1K = $30K
  - Timeline: By Month 18
  - Owner: Finance

- KR3: <3% monthly churn
  - Measure: Monthly churn rate
  - Target: Improving retention (scale focus)
  - Timeline: By Month 18
  - Owner: Support + product

**Objective 2: Expand Product Capabilities**

**Key Results:**
- KR1: Launch LLM extraction feature (Phase 3)
  - Measure: Feature available in Pro tier
  - Target: "Scrape + extract in one call" → premium feature
  - Timeline: Month 15-16
  - Owner: Engineering

- KR2: 10K+ Weekly Active Scrapers
  - Measure: WAS metric
  - Target: 10x growth (1K → 10K)
  - Timeline: By Month 18
  - Owner: Product

- KR3: 10-15 enterprise customers at $10K+/month
  - Measure: Enterprise customer count
  - Target: Significant revenue from upmarket
  - Timeline: By Month 18
  - Owner: Sales

**Success Definition:** Profitable, growing, and positioned for venture investment or acquisition.

---

### Metrics Dashboard

**Real-Time Tracking (Daily/Weekly):**

```
Growth Metrics:
  ├─ Weekly Active Scrapers (WAS): 150 ↑ 8%
  ├─ Free signups (7-day): 42 ↑ 5%
  ├─ Free activation rate: 78% ↓ 2%
  └─ Pro conversions (7-day): 3 ↔ 0%

Engagement Metrics:
  ├─ Avg scrapes/week per active user: 45
  ├─ First scrape success rate: 82%
  ├─ Weekly retention (free): 45%
  ├─ Weekly retention (pro): 92%
  └─ Support tickets/week: 12

Revenue Metrics:
  ├─ Pro customers: 80 ↑ 15 (+23%)
  ├─ Monthly Recurring Revenue (MRR): $4,000 ↑ 8%
  ├─ Average Revenue Per Account (ARPU): $50 ↔ 0%
  ├─ Customer Acquisition Cost (CAC): $0 (organic)
  └─ Net Promoter Score (NPS): 35 ↑ 5

Operations Metrics:
  ├─ Platform uptime: 99.8% ↑ 0.1%
  ├─ P95 scrape latency: 2.3s ↓ 0.2s
  ├─ Error rate: 2.1% ↓ 0.3%
  └─ On-call incidents (7-day): 1
```

---

## 7. UX/UI & Developer Experience Decisions

### Decision 1: API-First (not Dashboard-First)

**What We Chose:** Build API layer first (Week 3-4), defer dashboard to Month 7+

**Alternatives Considered:**

| Option | Pros | Cons | Cost | Timeline |
|--------|------|------|------|----------|
| **API-First** | Serves developers (target persona), fast MVP, scales to UI later | Less accessible to non-technical users | Low | 4 weeks |
| **Dashboard-First** | Visual, easier for business users, impressive demo | Slow MVP, feature duplication with API, not differentiated | High | 8 weeks |
| **Both Parallel** | Complete product day 1 | Too much work for 1-3 person team | Very High | 12+ weeks |

**Rationale:** Target persona (David, Sarah, Alex) are all developers. They prefer APIs over dashboards. Dashboards are nice-to-have, not need-to-have for MVP.

**Trade-Off:** Less accessible to non-technical stakeholders initially. **Acceptable because:**
- Enterprise customers (Alex) will likely build their own dashboard
- Pro customers (David) use Postman or cURL
- Free users are researchers/evaluators, don't need UI

**Decision:** API-first, add dashboard in Month 7 if needed

**Implementation Details:**
```
MVP (Month 4):
  ├─ POST /v2/scrape
  ├─ GET /v2/scrape/{id}
  ├─ GET /user/quota
  ├─ OpenAPI docs (auto-generated)
  └─ cURL examples in docs

Month 7+ (Dashboard):
  ├─ React dashboard
  ├─ Jobs list + detail view
  ├─ Usage analytics
  ├─ Team management
  └─ Billing portal
```

---

### Decision 2: Self-Serve (not Sales-Assisted)

**What We Chose:** Freemium + self-serve Pro signup (no sales team until Month 10)

**Alternatives Considered:**

| Option | Pros | Cons | CAC | Timeline to Revenue |
|--------|------|------|-----|-------------------|
| **Self-Serve** | Low CAC ($0 organic), product-led growth, scalable | Slower sales cycles, less control | $0 | 6 months |
| **Sales-Assisted** | Faster enterprise deals, higher ACV | High CAC ($500-1000), not scalable for Pro | $500+ | 3 months |
| **Hybrid** | Best of both (free tier is self-serve, enterprise has sales) | Complex, resource-intensive | $100-500 | 4 months |

**Rationale:** Our target market is price-sensitive (startups, researchers). They self-select through free tier. Sales-assisted would increase CAC to unsustainable levels for $50/month tier.

**Trade-Off:** Enterprise sales cycles will be slower initially. **Acceptable because:**
- First 6 months focus on free tier growth (product-led growth)
- Enterprise sales start Month 10+ when product is stable
- Product-led growth creates inbound demand (self-serve)

**Decision:** Self-serve for free/Pro, add sales-assisted for Enterprise in Month 10+

**Implementation Details:**
```
Months 4-9 (Self-Serve):
  ├─ Free tier signup: Name + email, instant API key
  ├─ Pro tier upgrade: Credit card, instant access
  ├─ No manual approval needed
  ├─ Instant onboarding: 10-min quick start
  └─ Email support only

Months 10+ (Sales-Assisted):
  ├─ Add enterprise contact form
  ├─ Enterprise sales person reaches out
  ├─ Custom contract, discounts, SLA
  └─ Dedicated account manager
```

---

### Decision 3: Open-Source-First (not SaaS-Only)

**What We Chose:** GitHub public repository (MIT license), but monetize SaaS cloud hosting

**Alternatives Considered:**

| Option | Pros | Cons | Revenue Model |
|--------|------|------|----------------|
| **Open-Source-First** | Community trust, no lock-in, rapid adoption | Feature leakage, support burden | SaaS hosting + premium features |
| **SaaS-Only** | Proprietary, high margins, lock-in | Slow adoption, distrust, high CAC | Subscription only |
| **Dual License** | Control feature parity | Confusing to users, license fragmentation | Complicated |

**Rationale:** Open-source differentiates vs Apify (closed). Self-hosted option (Docker Compose) prevents vendor lock-in. Revenue from cloud hosting, not software licensing.

**Trade-Off:** Feature leakage (open-source version has all features). **Acceptable because:**
- Revenue is from cloud hosting (SaaS), not features
- Self-hosted requires operational expertise (not everyone will do it)
- Open-source builds trust, drives adoption, creates network effects

**Decision:** Open-source (MIT) + SaaS monetization (cloud hosting)

**Implementation Details:**
```
GitHub (Public, MIT License):
  ├─ Full source code
  ├─ Documentation
  ├─ Docker Compose setup
  ├─ Community contributions
  └─ No lock-in

SaaS Cloud (Monetized):
  ├─ Managed infrastructure
  ├─ Webhooks + scheduling
  ├─ Advanced monitoring
  ├─ Professional support
  └─ Freemium tiers

Proprietary Cloud Features (Premium):
  ├─ Webhooks
  ├─ Scheduled scrapes
  ├─ Advanced analytics
  ├─ Actor marketplace
  └─ AI extraction (Phase 3)
```

---

### Decision 4: Transparent Pricing (not Custom Quotes)

**What We Chose:** Public pricing tiers (Free $0, Pro $50, Enterprise custom)

**Alternatives Considered:**

| Option | Pros | Cons | Enterprise Velocity | CAC |
|--------|------|------|-------------------|-----|
| **Transparent** | Builds trust, self-serve, product-led growth | Lower enterprise margins | Slower initial | Low |
| **Custom Quotes** | Higher enterprise margins, perception of value | Long sales cycles, erodes trust, high CAC | Faster | High |
| **Hidden Pricing** | Forces inbound | Kills adoption, reduces conversion | Fast (forced) | Medium |

**Rationale:** "Open company with transparent pricing" is a brand differentiator vs Apify (who hide pricing). Enables product-led growth.

**Trade-Off:** Enterprise customers may negotiate down from list price. **Acceptable because:**
- Enterprise willing to pay premium for features/SLA, not discounts
- Transparent pricing reduces sales friction (no call required for Pro)
- Self-serve converts at higher rate when price is known

**Decision:** Public pricing, enterprise discounts available (10-15% for annual prepay)

**Implementation Details:**
```
Public Pricing Page:
  ├─ Free: $0/month
  ├─ Pro: $50/month
  ├─ Enterprise: "Contact us" (but they know it's $1K+)

Enterprise Negotiation:
  ├─ 10% discount for annual prepay
  ├─ Volume discounts (>100M scrapes/month)
  ├─ Custom SLA (99.9%+)
  └─ Dedicated support included
```

---

## 8. Product Risks & Mitigation

### Risk Assessment Matrix

| Risk | Probability | Impact | Severity | Mitigation | Early Warning |
|------|-------------|--------|----------|-----------|---------------|
| **PMF Failure** (no one wants product) | Low | Very High | Critical | Beta program Month 4-6, need 50+ signups | <30 signups by Month 6 |
| **Churn Too High** (>10% monthly) | Medium | High | Major | 99.9% SLA, monitoring, support | Churn >8% Month 7-8 |
| **Can't Compete vs Apify** | Medium | High | Major | Clear positioning, niche focus, community | NPS <30 by Month 6 |
| **Cost Overruns** (>$2K/month before revenue) | Low | Medium | Moderate | Start small, scale on-demand, monitor weekly | Costs >$1.5K Month 5 |
| **Team Burnout** (small team, big ambition) | Medium | Medium | Moderate | Realistic timeline, don't skip MVP, hire early | Founder stress signals |
| **User Migration Issues** (from Firecrawl) | Low | Medium | Moderate | API compatibility, migration guide, support | <50% migration by Month 8 |
| **Apify Kills Open-Source** | Very Low | High | Low-Priority | Engine abstraction, fork preparation | License change |
| **Cloud Vendor Cost Spike** | Low | Medium | Moderate | Monitor costs weekly, use spot instances | Costs spike >20% |

### Phase-Specific Risk Mitigation

#### Phase 1 (Months 1-6): Validation Risk

**Risk:** Product doesn't resonate with target users

**Likelihood:** Low (based on market research)
**Impact:** High (wasted 2-3 months)

**Mitigation:**
- Week 1-2 PoC validates technical feasibility
- Beta program (Month 4-6) with 50+ signups
- Weekly 1-on-1 interviews with beta users
- Slack community for feedback
- Net Promoter Score tracking (target >40 by Month 6)

**Gate:** Must have 50+ signups + 80%+ first-scrape success + NPS >30 by Month 6 to proceed. If not met, pivot to open-source only (no SaaS).

---

#### Phase 2 (Months 7-12): Product-Market Fit Risk

**Risk:** Can't reach 50 paying customers or churn >5%

**Likelihood:** Medium (pricing/positioning is guess)
**Impact:** High (business doesn't scale)

**Mitigation:**
- Customer success team (1 FTE by Month 8)
- Weekly cohort analysis (new customer retention by signup week)
- A/B test pricing tiers if needed
- Enterprise outreach (direct outreach to 20 CTOs)
- Community engagement (Discord, GitHub discussions)

**Gate:** Must hit 50 Pro customers + <5% churn by Month 12 to continue. If not met, pivot to open-source-only model or seek acquisition.

---

#### Phase 3 (Months 13-18): Growth Risk

**Risk:** Can't scale to 200 customers or revenue plateaus

**Likelihood:** Medium (market saturation or competition)
**Impact:** Medium (limits business ceiling)

**Mitigation:**
- Enterprise sales team (1 FTE by Month 15)
- Product expansion (LLM extraction, marketplace)
- Partnerships (data agencies, consultants)
- Content marketing (SEO, case studies)
- Consider acquisition target for larger company

**Gate:** Must hit $30K MRR by Month 18 to justify continued investment. If not met, sell as acquisition or open-source indefinitely.

---

### Contingency Plans

**If PoC Fails (Success Rate <90%):**

**Option 1: Optimize Firecrawl Instead**
- Timeline: 4-8 weeks to production
- Cost: Similar ($965/month)
- Upside: Proven technology, can launch faster
- Downside: More operational burden, less differentiated

**Option 2: Hybrid (Crawlee + Firecrawl)**
- Use Crawlee for simple cases, Firecrawl as fallback
- Timeline: 8-12 weeks
- Cost: Higher ($1,500+/month)
- Upside: 99%+ success rate
- Downside: Complex operational model

**Decision:** Only pivot if PoC success rate <85% and can't be improved in 1 week.

---

**If Beta Fails (Churn >20% or NPS <20):**

**Option 1: Free-Only Model**
- Close Pro tier, focus on open-source community
- Revenue: $0 (sustainability via sponsorship)
- Timeline: 1-2 weeks
- Upside: Clear positioning, removes pricing confusion
- Downside: No business model

**Option 2: Pivot to Different Persona**
- Current focus (startups, researchers) didn't work
- Try: Enterprise (CTOs, platform teams)
- Sales model: Direct sales, SOW-based pricing
- Timeline: 4-6 weeks to reposition

**Option 3: Acquisition Target**
- If product works but business doesn't, position for acquisition
- Target acquirers: Apify (unlikely), other data platforms
- Timeline: Months 9-12 approach investors/acquirers

**Decision:** Evaluate after Month 6 based on real data (NPS, churn, signups).

---

## 9. Decision Log: Product Choices

This section documents key product decisions, alternatives considered, and rationale.

### Decision 1: Multi-Tenant Platform (not Single-Tenant or Monolithic)

**Decision:** Build multi-tenant SaaS platform with PostgreSQL Row-Level Security (RLS)

**Date Decided:** 2026-02-02
**Decided By:** Product Manager + Cloud Architect
**Status:** ACCEPTED ✅

**Alternatives Evaluated:**

| Option | Pros | Cons | Cost | Effort | Verdict |
|--------|------|------|------|--------|---------|
| **Multi-Tenant (RLS)** | Single codebase, scales economically, SaaS-ready | Complex DB design, RLS security considerations | Low ops cost | Medium engineering | ✅ CHOSEN |
| Single-Tenant (Separate DB per customer) | Isolation guaranteed, simple application logic | 1 DB per customer = expensive, not web-scale at 100+ customers | High ops cost | Low engineering |  ❌ REJECTED |
| Separate Docker Containers | Isolation, predictable resources per customer | Resource-heavy, Kubernetes-complex, $10K+/month at scale | Very high ops cost | High engineering | ❌ REJECTED |

**Rationale from Product Perspective:**

1. **Enables Freemium Model**
   - Can offer free tier without separate infrastructure
   - One codebase + multi-tenant = lower CAC for free users
   - Converts to Pro tier easily (just raise quota)

2. **Cost Efficiency**
   - $50 Pro customer costs $5-10/month to serve (multi-tenant)
   - $50 Pro customer would cost $50-100+ (single-tenant)
   - Multi-tenancy = 10x better margins = sustainable business

3. **Scalability**
   - Can grow from 10 to 10,000 customers on same infrastructure
   - Single-tenant would require 100x more VMs
   - Competitive moat (can undercut Apify on price)

4. **Feature Parity with Competitors**
   - Apify is multi-tenant
   - Firecrawl self-hosted is single-tenant (part of complexity)
   - Being multi-tenant signals "real platform" to customers

**Why Acceptable:**

1. **RLS Security is Proven**
   - PostgreSQL RLS is military-grade (uses in defense)
   - Misconfigurations are application bugs, not DB bugs
   - Security audit in Month 9 de-risks further

2. **No Operational Complexity**
   - Multi-tenancy complexity is in the DB schema/RLS policies
   - Application code remains simple (one codebase)
   - Better than managing N single-tenant deployments

3. **Founder-Friendly**
   - 1 database to manage vs 100+
   - 1 backup strategy vs 100+
   - 1 monitoring setup vs 100+

**Risk Mitigation:**

1. **Security**
   - Audit RLS policies before Month 7 launch
   - Penetration test (Month 8)
   - Bug bounty program (Month 12+)

2. **Data Isolation Testing**
   - Unit tests for RLS policies
   - Integration tests (verify Customer A can't see Customer B data)
   - Load test under concurrent tenants

3. **GDPR Compliance**
   - 30-day data deletion policy
   - Audit logging (who accessed what data)
   - Data export functionality

**Decision Approval:**
- Product: ✅ Enablesenables freemium model, competitive advantage
- Engineering: ✅ Simple to implement, proven technology
- Security: ⚠️ Requires careful design, auditing mitigates risk

---

### Decision 2: Free Tier with Aggressive Freemium Model

**Decision:** Offer free tier with 1K scrapes/month, no credit card required for trial

**Date Decided:** 2026-02-02
**Status:** ACCEPTED ✅

**Alternatives Evaluated:**

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Free Tier (1K/month)** | Low barrier to entry, viral growth potential, high LTV | Lower MRR initially, abuse potential | ✅ CHOSEN |
| Paid-Only ($50/month minimum) | Higher MRR from day 1, no freeloaders | Low adoption, slow growth, high CAC | ❌ REJECTED |
| Trial-Based (14-day free trial) | Conversion pressure, no open-ended free | Most churn after trial, low net conversion | ⚠️ CONSIDERED |

**Rationale from Product Perspective:**

1. **LTV of Free User = $600 (if converts)**
   - Start at free (cost $3 to serve, cost of 1K scrapes)
   - 5% monthly conversion rate (conservative)
   - Average lifetime 12-18 months
   - LTV: $50 × (5% × 15 months) ÷ (monthly cost $3) = $600 NPV

2. **CAC of Free User = $0 (if organic)**
   - No paid marketing for free tier
   - Viral growth (word-of-mouth, HN, GitHub)
   - Community-driven adoption

3. **LTV:CAC Ratio = ∞**
   - Break-even on conversion alone
   - Massive leverage (every free user who converts is 100% margin)

4. **Market Position**
   - "Open-source, free to start" = trust builder
   - Apify charges even for evaluation
   - We win on accessibility

**Why Acceptable:**

1. **Sustainable Economics**
   - 500 free users (cost: $1,500/month)
   - 50 conversions to Pro (revenue: $2,500/month)
   - Net: $1,000/month positive

2. **Abuse Prevention**
   - Rate limiting (1 req/sec) prevents DDoS
   - Auto-block on suspicious patterns (CAPTCHAs, IP bans)
   - Usage monitoring (flag accounts >100K scrapes/month)

3. **Freemium Conversion Metrics**
   - Successful freemium (Slack, Zoom, GitHub): 2-10% conversion
   - We target 5% (middle)
   - Even 2% conversion = profitable

**Risk Mitigation:**

1. **Abuse Prevention**
   - Rate limiting + quota enforcement
   - CAPTCHAs on suspicious activity
   - Automated abuse detection (anomalies)

2. **Sustainable Economics**
   - Monitor free tier cost ratio (target: <30% of total infra)
   - A/B test free tier size if needed (currently 1K)
   - Track conversion cohorts (when did they sign up, when do they convert)

3. **Support Burden**
   - Community support (Discord, not direct support)
   - Docs + FAQ to self-serve
   - "Community answers" model (pro users answer free users)

**Decision Approval:**
- Product: ✅ Enables product-led growth, network effects
- Finance: ✅ LTV:CAC infinite if organic, even 2% converts = positive
- Support: ⚠️ Community support model required (not direct)

---

### Decision 3: Open-Source from Day 1 (MIT License)

**Decision:** Public GitHub repository (MIT license), monetize cloud hosting

**Date Decided:** 2026-02-02
**Status:** ACCEPTED ✅

**Alternatives Evaluated:**

| Option | Pros | Cons | Enterprise Impact | Verdict |
|--------|------|------|------------------|---------|
| **Open-Source (MIT)** | Community trust, rapid adoption, no lock-in | Feature leakage, support burden | Increased adoption, easier to pitch | ✅ CHOSEN |
| Proprietary (Closed) | Revenue control, feature secrecy | Slow adoption, distrust | Harder to convince to use | ❌ REJECTED |
| Freemium (GPL/AGPL) | Force cloud-only for some use cases | Community fragmentation, legal complexity | Confusing positioning | ⚠️ CONSIDERED |

**Rationale from Product Perspective:**

1. **Open-Source = Trust Builder**
   - Apify doesn't open-source → customers distrust
   - We open-source → customers see code, can self-host if needed
   - Trust = faster adoption, higher LTV

2. **Self-Hosted Option = Competitive Advantage**
   - Firecrawl self-hosted is complex (7 services, 50% ops time)
   - We offer simple self-hosted (4 services, 20% ops time)
   - David can run locally if needed (doesn't lock him in)

3. **Community Contributions**
   - Anti-detection patterns (hardest part) can come from community
   - Community bug fixes (faster than hiring)
   - Community acts as QA/testing

4. **Revenue from SaaS, Not Licensing**
   - Revenue is from cloud hosting (infrastructure costs money)
   - Not from software licensing (arbitrary markup)
   - Honest business model (customers pay for what we spend)

**Why Acceptable:**

1. **Feature Leakage is OK**
   - Open-source version has all features
   - But cloud version has benefits (no ops, SLA, support)
   - Self-hosted requires DevOps expertise (David might not have)

2. **Support Burden is Manageable**
   - Community handles most support (GitHub issues)
   - Pro customers get email support (1 person = 50 customers)
   - Open-source has no SLA (ok for free users)

3. **Enterprise Doesn't Want to Self-Host**
   - Alex (CTO) wants managed service (no ops burden)
   - Will buy our cloud version (SaaS)
   - Self-hosted option doesn't cannibalize enterprise

4. **Venture-Friendly Positioning**
   - VCs like open-source companies (shows credibility)
   - GitHub stars = social proof (investors check this)
   - Community = organic marketing

**Risk Mitigation:**

1. **Feature Leakage**
   - Proprietary cloud-only features:
     - Webhooks (cloud-specific)
     - Scheduled scrapes (cloud-specific)
     - Actor marketplace (cloud-specific)
     - AI extraction (premium tier)
   - Self-hosted gets open-source features only

2. **Support Burden**
   - Community support model (Discord, GitHub discussions)
   - Docs + examples (self-serve)
   - Premium support tier ($1K/month)

3. **License Management**
   - MIT is permissive (no copyleft)
   - Allows commercial forks (ok with us)
   - No license enforcement needed

**Decision Approval:**
- Product: ✅ Builds trust, enables adoption, differentiates from Apify
- Marketing: ✅ GitHub stars = social proof, viral growth
- Engineering: ✅ Community contributions, rapid iteration
- Legal: ✅ MIT is permissive, no complication

---

### Decision 4: Transparent Pricing (no custom quotes)

**Decision:** Public pricing tiers (Free $0, Pro $50, Enterprise custom) with annual discount

**Date Decided:** 2026-02-02
**Status:** ACCEPTED ✅

**Alternatives Evaluated:**

| Option | Pros | Cons | CAC | LTV Impact | Verdict |
|--------|------|------|-----|-----------|---------|
| **Transparent** | Builds trust, self-serve, no friction | Lower enterprise margins (they negotiate) | $0 (self-serve) | Higher (conversion ease) | ✅ CHOSEN |
| Custom Quotes | Higher enterprise margins, perception of premium | Long sales cycles, kills adoption, high CAC | $500+ | Lower (conversion friction) | ❌ REJECTED |
| Hidden Pricing | Forces inbound lead gen | Kills adoption (people hate this), distrust | Medium | Negative (people hate this) | ❌ REJECTED |

**Rationale from Product Perspective:**

1. **Transparent Pricing = Brand Differentiator**
   - Apify hides pricing (bad optics)
   - We publish prices (builds trust)
   - Positioning: "Open company with open pricing"

2. **Self-Serve Works at Scale**
   - Customer converts without talking to sales
   - CAC = $0 (vs $500+ for sales-assisted)
   - Volume effect: 1000 customers × $0 CAC = $0 total CAC

3. **Enterprise Willing to Pay More for Value, Not Less**
   - Enterprise pays for SLA, support, security audit
   - Not for "discount negotiation"
   - Will pay $1,000-5,000/month if we deliver value

4. **Product-Led Growth**
   - Customers try for free
   - See value, upgrade to Pro
   - Conversion happens without sales
   - Scalable to 10,000 customers on this model

**Why Acceptable:**

1. **Enterprise Discounts Still Possible**
   - "10% discount for annual prepay" = incentive
   - "Volume discounts for >100M scrapes/month"
   - But not negotiable for all (anchors pricing)

2. **Pro Tier Profitability**
   - At $50/month × 10K scrapes = $5/1K scrapes (sell price)
   - Cost = $5-30/1K (depending on method)
   - Even light users are profitable at scale

3. **Enterprise Economics**
   - 5 Enterprise customers @ $2K/month = $10K/month
   - Cost = $1,000-2,000
   - Gross margin = 50-80%

**Risk Mitigation:**

1. **If Enterprise Negotiates Down**
   - "Price is fixed, but we can add features/SLA"
   - Don't compete on price, compete on value
   - Annual prepay gets discount (10-15%)

2. **If Churn High (customers see price is too high)**
   - A/B test lower pricing ($35/month)
   - More customers at lower price > fewer at higher price
   - Monitor LTV:CAC ratio (goal: 3x+)

3. **If Competitors Undercut Price**
   - We have costs (infra, support)
   - Can't go below $30/month without losing money
   - Differentiate on features, not price

**Decision Approval:**
- Product: ✅ Enables product-led growth, network effects
- Sales: ✅ Self-serve works for Pro tier, focus enterprise on value
- Finance: ✅ CAC = $0 (organic), LTV = $600+ (pro customers)

---

## 10. Timeline & Rollout Plan

### High-Level Timeline

```
Months 1-3: Foundation & Validation (Parallel with existing work)
  └─ Week 1-2: PoC (Crawlee feasibility test)
  └─ Week 3-4: API Layer (FastAPI, job queue)
  └─ Week 5-6: Multi-Tenancy (RLS, quotas)
  └─ Week 7-8: Anti-Detection (3-layer escalation)
  └─ Week 9-10: Monitoring (Prometheus + Grafana)
  └─ Week 11-12: Hardening & Documentation

Months 4-6: Beta & Product-Market Fit
  └─ Month 4: Public Beta Launch
  └─ Month 5-6: Community building, feedback loops
  └─ Gate: 50+ signups, 80% success rate, NPS >30

Months 7-9: Pro Tier Launch & Growth
  └─ Month 7: Launch Pro tier ($50/month)
  └─ Month 8-9: Sales + marketing push
  └─ Goal: 50+ Pro customers, $2.5K+ MRR

Months 10-12: Enterprise & Profitability
  └─ Month 10: Enterprise sales outreach
  └─ Month 11-12: Professional support tier
  └─ Goal: 5 enterprise deals, $5K+ MRR, break-even

Months 13-18: Scale & Expand
  └─ Month 13-14: LLM extraction feature (Phase 3)
  └─ Month 15-18: Growth marketing, partnerships
  └─ Goal: 200+ customers, $30K+ MRR
```

### Go/No-Go Gates

**Gate 1: Week 2 (PoC Completion)**

**Criteria:**
- [ ] Success rate ≥90%
- [ ] Latency ≤2x Firecrawl
- [ ] Code <500 LoC (simpler than Firecrawl)
- [ ] Team confident to proceed

**Decision:** Go → Week 3 API layer, No-Go → Pivot to Firecrawl optimization

**Gate 2: Month 6 (Beta Completion)**

**Criteria:**
- [ ] 50+ beta signups
- [ ] 80%+ first-scrape success
- [ ] NPS ≥30
- [ ] <0.5% security incidents

**Decision:** Go → Pro tier launch, No-Go → Pivot to open-source-only or acquisition

**Gate 3: Month 12 (Year 1 Review)**

**Criteria:**
- [ ] 200+ Pro customers
- [ ] $10K+ MRR
- [ ] <5% monthly churn
- [ ] NPS ≥40
- [ ] Break-even or profitable

**Decision:** Go → Continue growth, No-Go → Seek acquisition or pivot

---

## 11. Success Definition

### Product Launch Success (Month 4)

By end of Month 4, if we have:

1. ✅ **Deployed to production** (`api.crawl-platform.com`)
2. ✅ **100+ beta signups** (goal is 100, track weekly)
3. ✅ **80%+ first-scrape success rate** (David, Sarah, Alex all get "it works" in first try)
4. ✅ **Zero security incidents** (multi-tenancy holds up)
5. ✅ **OpenAPI documentation** at http://api.crawl-platform.com/docs
6. ✅ **15-min onboarding video** (shows full flow)
7. ✅ **Discord community** with 50+ members

**Then:** Product launch is successful. Proceed to growth phase.

### Business Model Validation (Month 7)

By end of Month 7, if we have:

1. ✅ **50 Pro customers** (or on track to reach it by Month 8)
2. ✅ **$2.5K+ MRR** from Pro tier
3. ✅ **<5% monthly churn** (customers are sticky)
4. ✅ **NPS ≥30** (customers like it, would recommend to friends)
5. ✅ **Operational profitability** ($2.5K revenue - $1.5K costs = $1K profit)

**Then:** Business model works. Scale it.

### Year 1 Success (Month 12)

By end of Month 12, if we have:

1. ✅ **200+ Pro customers**
2. ✅ **$10K+ MRR total** (Pro + early Enterprise)
3. ✅ **<5% churn** (healthy business metrics)
4. ✅ **Gross margin >50%** (profitable at scale)
5. ✅ **1K+ GitHub stars** (credibility signal)
6. ✅ **500+ Discord members** (engaged community)
7. ✅ **Break-even or profitable** (dev costs recovered)

**Then:** Year 1 successful. Plan for growth and expansion.

---

## 12. Financial Summary

### Development Costs

| Component | Effort | Cost @ $100/hr | Notes |
|-----------|--------|----------------|-------|
| **Week 1-2: PoC** | 60 hrs | $6,000 | Crawlee validation |
| **Week 3-4: API Layer** | 80 hrs | $8,000 | FastAPI, auth, queue |
| **Week 5-6: Multi-Tenancy** | 80 hrs | $8,000 | RLS, quotas |
| **Week 7-8: Anti-Detection** | 60 hrs | $6,000 | Layer escalation |
| **Week 9-10: Monitoring** | 40 hrs | $4,000 | Prometheus, Grafana |
| **Week 11-12: Hardening** | 40 hrs | $4,000 | Tests, docs, deployment |
| **Month 4: Beta Launch** | 40 hrs | $4,000 | Go-live, marketing prep |
| **Months 5-6: Community** | 80 hrs | $8,000 | Support, content |
| **Months 7-9: Growth** | 120 hrs | $12,000 | Features, operations |
| **Months 10-12: Enterprise** | 80 hrs | $8,000 | Sales support, premium tier |
| **TOTAL (12 Months)** | 640 hrs | **$68,000** | Equivalent to 6-month FTE salary |

### Infrastructure Costs

| Item | Month 4-6 | Month 7-9 | Month 10-12 | Cost Basis |
|------|-----------|-----------|------------|-----------|
| **API Server (Fargate)** | $100 | $150 | $200 | 2 vCPU, 4GB RAM |
| **Workers (Fargate)** | $150 | $300 | $500 | 5 tasks @ 2vCPU |
| **PostgreSQL (RDS)** | $70 | $70 | $150 | db.t3.medium → larger |
| **Redis (ElastiCache)** | $70 | $70 | $100 | cache.t3.medium |
| **S3 Storage** | $25 | $50 | $100 | Content storage |
| **Proxy (BrightData)** | $200 | $400 | $800 | 20% of requests |
| **Domain & SSL** | $15 | $15 | $15 | Negligible |
| **Monitoring (DataDog)** | $50 | $100 | $150 | Logs, metrics, traces |
| **TOTAL** | **$680** | **$1,155** | **$1,915** | Increases with scale |

### Revenue Projection

| Month | Free Users | Pro Customers | Enterprise | MRR | Cumulative Revenue |
|-------|-----------|---------------|-----------|-----|-------------------|
| 4 | 100 | 0 | 0 | $0 | $0 |
| 5 | 200 | 5 | 0 | $250 | $250 |
| 6 | 350 | 15 | 0 | $750 | $1,000 |
| 7 | 500 | 50 | 0 | $2,500 | $3,500 |
| 8 | 700 | 80 | 1 | $5,000 | $8,500 |
| 9 | 900 | 120 | 2 | $8,000 | $16,500 |
| 10 | 1,200 | 150 | 3 | $10,500 | $27,000 |
| 11 | 1,500 | 180 | 4 | $13,000 | $40,000 |
| 12 | 2,000 | 200 | 5 | $15,000 | $55,000 |

### Profitability Analysis

| Metric | Month 7 | Month 9 | Month 12 |
|--------|---------|---------|----------|
| **MRR** | $2,500 | $8,000 | $15,000 |
| **OpEx** | $1,155 | $1,500 | $1,915 |
| **Gross Profit** | $1,345 | $6,500 | $13,085 |
| **Gross Margin** | 54% | 81% | 87% |
| **Break-Even Status** | Profitable! | Profitable | Profitable |

**Key Insight:** We break even at Month 7 (50 Pro customers @ $50/month = $2.5K revenue - $1.2K infra = $1.3K profit)

### ROI Analysis

| Investment | Cost | Month 12 Return | ROI |
|-----------|------|-----------------|-----|
| **Development** | $68,000 | $180,000 ARR | 2.6x |
| **Infrastructure** | $14,000 | N/A (recurring) | Covered by MRR |
| **Total Year 1** | $82,000 | $180,000 ARR | 2.2x |

**Conclusion:** $82K investment returns $180K ARR by Month 12 = 2.2x ROI, fully recovering costs by Year 2.

---

## Conclusion: Go/No-Go Recommendation

### Executive Recommendation: **GO FORWARD** ✅

Based on comprehensive product and business analysis:

**Product Perspective:**
- Market opportunity is real ($500M+ TAM)
- Target users exist and are underserved (David, Sarah, Alex personas)
- Solution is differentiated (50% cheaper, simpler, open-source)
- MVP is achievable in 12 weeks with 1-3 developers

**Business Perspective:**
- Revenue model is validated ($600 LTV from free → Pro)
- Unit economics work (50%+ gross margin at scale)
- Break-even in Month 7 ($2.5K MRR)
- Full ROI by Month 12 ($180K ARR on $68K dev cost)

**Technical Perspective:**
- Crawlee is production-proven (Apify uses it)
- Architecture is sound (4 services vs 7 for Firecrawl)
- Risk is low with Week 1-2 PoC gate
- 60% of current work salvageable (costs down to $46K)

**Risk Assessment:**
- **Technical Risk:** Low (PoC validates, Week 1-2)
- **Market Risk:** Medium (need 50 signups by Month 6)
- **Operational Risk:** Low (managed services, simple deployment)
- **Overall Risk:** Low-Medium (mitigated by phased rollout + gates)

### Decision Criteria Met

| Criterion | Status | Notes |
|-----------|--------|-------|
| **Team Capacity** | ✅ Fit | 1-3 developers, 12-week timeline |
| **Technical Feasibility** | ✅ Proven | Crawlee production-ready |
| **Business Viability** | ✅ Sound | $180K ARR, 2.6x ROI |
| **Market Opportunity** | ✅ Real | $500M+ TAM, clear personas |
| **Differentiation** | ✅ Clear | 50% cheaper, simpler, open-source |
| **Risk Acceptable** | ✅ Mitigated | PoC gate, phased rollout |

### Next Steps

**Immediate (This Week):**
1. [ ] Schedule team alignment meeting (product, engineering, finance)
2. [ ] Approve Week 1-2 PoC scope (estimated 60 hours)
3. [ ] Set up PoC success criteria (≥90% success rate, ≤2x latency)
4. [ ] Create GitHub issue tracker for PoC tasks

**Week 1-2 (PoC Phase):**
1. [ ] Set up Crawlee environment
2. [ ] Port 3-5 anti-detection patterns from current `scraper.py`
3. [ ] Benchmark against 20 representative websites
4. [ ] Document findings and make Go/No-Go decision

**Week 3+ (If Go):**
1. [ ] Begin API layer implementation (Week 3-4)
2. [ ] Continue with multi-tenancy (Week 5-6)
3. [ ] Prepare for Month 4 public beta launch

---

**Document Status:** FINAL / READY FOR EXECUTION
**Decision Authority:** CEO / CTO / Founders
**Next Review:** Week 2 (PoC completion gate)

---

*End of Part 1: Product Design & Strategy*

---

# Part 2: Technical Architecture & Implementation

This section provides comprehensive technical specifications, architectural decisions, and implementation details for the Crawlee-based multi-tenant web scraping platform.

---

## 1. Architecture Overview

### 1.1 System Design

The platform follows a distributed microservices architecture optimized for scalability, cost-efficiency, and maintainability. The design prioritizes horizontal scaling, fault tolerance, and multi-tenant isolation.

```
                                    INTERNET
                                        |
                                        v
    +===================================================================+
    |                     LOAD BALANCER (ALB)                           |
    |               (SSL Termination, Health Checks)                    |
    +===================================================================+
                                        |
                                        v
    +-------------------------------------------------------------------+
    |                   API GATEWAY (FastAPI)                           |
    |                                                                   |
    |  Endpoints:                                                       |
    |  - POST /v2/scrape         (async job creation)                  |
    |  - GET /v2/scrape/{id}     (job status + presigned URLs)         |
    |  - POST /v2/crawl          (multi-page crawl)                    |
    |  - GET /v2/crawl/{id}      (crawl status)                        |
    |  - POST /admin/tenants     (tenant management)                   |
    |  - GET /admin/usage        (billing metrics)                     |
    |                                                                   |
    |  Middleware Stack:                                                |
    |  1. Authentication (API Key -> tenant_id resolution)             |
    |  2. Rate Limiting (sliding window, Redis-backed)                 |
    |  3. Quota Enforcement (monthly limits)                           |
    |  4. Request Logging (structured JSON)                            |
    |                                                                   |
    |  Capacity: 400 req/s at scale (2 vCPU, 4GB per instance)        |
    +-------------------------------------------------------------------+
                                        |
                        +---------------+---------------+
                        |                               |
                        v                               v
    +-------------------------------+   +-------------------------------+
    |       JOB QUEUE (arq)         |   |     REDIS CLUSTER             |
    |       (Redis-backed)          |   |                               |
    |                               |   |  - Rate limit counters        |
    |  - Tenant-isolated queues     |   |  - Session cache              |
    |  - Priority scheduling:       |   |  - Tenant config cache        |
    |    * Free: 10 concurrency     |   |  - Job state                  |
    |    * Pro: 50 concurrency      |   |                               |
    |    * Enterprise: 1000 conc.   |   |  Capacity: 16GB               |
    |                               |   |  Sentinel: 3-node HA          |
    +-------------------------------+   +-------------------------------+
                        |
        +---------------+---------------+---------------+
        |               |               |               |
        v               v               v               v
    +-------+       +-------+       +-------+       +-------+
    |Worker |       |Worker |       |Worker |       |Worker |
    |  01   |       |  02   |       |  03   |       |  ...  |
    +-------+       +-------+       +-------+       +-------+
        |               |               |               |
        +---------------+---------------+---------------+
                        |
                        v
    +===================================================================+
    |              ANTI-DETECTION ORCHESTRATOR                          |
    |              (Challenge-Driven Escalation)                        |
    |                                                                   |
    |  +------------------+  +------------------+  +------------------+ |
    |  | LAYER 1          |  | LAYER 2          |  | LAYER 3          | |
    |  | curl_cffi        |  | Crawlee HTTP     |  | Crawlee Browser  | |
    |  |                  |  |                  |  | (Playwright)     | |
    |  | - TLS fingerprint|  | - Session mgmt   |  | - Full JS render | |
    |  | - Chrome131 spoof|  | - Cookie persist |  | - Stealth mode   | |
    |  | - 50ms latency   |  | - 200-500ms      |  | - 2-5s latency   | |
    |  | - 60% success    |  | - 70% success    |  | - 85% success    | |
    |  | - $0.0005/req    |  | - $0.001/req     |  | - $0.005/req     | |
    |  +------------------+  +------------------+  +------------------+ |
    |           |                    |                    |             |
    |           v                    v                    v             |
    |  +------------------+  +------------------+  +------------------+ |
    |  | LAYER 4          |  | LAYER 5          |  | CHALLENGE        | |
    |  | Residential      |  | FlareSolverr     |  | DETECTOR         | |
    |  | Proxies          |  |                  |  |                  | |
    |  |                  |  | - Cloudflare     |  | - Cloudflare     | |
    |  | - BrightData     |  | - PerimeterX     |  | - PerimeterX     | |
    |  | - IP rotation    |  | - DataDome       |  | - DataDome       | |
    |  | - +500ms latency |  | - 10-30s latency |  | - Generic blocks | |
    |  | - +$0.02/req     |  | - 95% success    |  |                  | |
    |  +------------------+  +------------------+  +------------------+ |
    +===================================================================+
                        |
                        v
    +===================================================================+
    |                 DATA & STORAGE LAYER                              |
    |                                                                   |
    |  +------------------+  +------------------+  +------------------+ |
    |  | PostgreSQL 16    |  | Amazon S3        |  | Redis Cache      | |
    |  |                  |  |                  |  |                  | |
    |  | - Job metadata   |  | - Scraped HTML   |  | - Session state  | |
    |  | - Tenant records |  | - Markdown       |  | - Rate limits    | |
    |  | - Usage tracking |  | - Screenshots    |  | - Config cache   | |
    |  | - API keys       |  |                  |  |                  | |
    |  |                  |  | Structure:       |  |                  | |
    |  | Row-Level        |  | {tenant_id}/     |  | TTL: 5min        | |
    |  | Security (RLS)   |  |   {job_id}/      |  | (config)         | |
    |  |                  |  |     content.*    |  | TTL: 1hr         | |
    |  | Capacity: 500    |  |                  |  | (sessions)       | |
    |  | connections      |  | Lifecycle: 30d   |  |                  | |
    |  +------------------+  +------------------+  +------------------+ |
    +===================================================================+
```

### 1.2 Data Flow Architecture

```
                    CLIENT REQUEST
                          |
                          v
    +----------------------------------------------------------+
    |  1. API GATEWAY RECEIVES REQUEST                          |
    |     POST /v2/scrape {"url": "https://example.com"}       |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  2. AUTHENTICATION MIDDLEWARE                             |
    |     - Extract API key from Authorization header           |
    |     - Verify bcrypt hash against database                 |
    |     - Resolve tenant_id from api_keys table               |
    |     - Check tenant status (active/suspended)              |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  3. RATE LIMIT CHECK (Redis Sliding Window)               |
    |     - Key: rate_limit:{tenant_id}:hour                    |
    |     - Lua script for atomic increment                     |
    |     - Return 429 if limit exceeded                        |
    |     - Set X-RateLimit-* headers                           |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  4. QUOTA CHECK (PostgreSQL usage_summary)                |
    |     - Query monthly usage count                           |
    |     - Compare against tenant.monthly_quota                |
    |     - Return 402 if quota exceeded                        |
    |     - Set X-Quota-* headers                               |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  5. JOB CREATION                                          |
    |     - Generate UUID job_id                                |
    |     - INSERT into jobs table with tenant_id               |
    |     - Enqueue to arq with priority based on tier          |
    |     - Return {id, status: "pending"} immediately          |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  6. WORKER PICKS UP JOB                                   |
    |     - Dequeue from tenant-prioritized queue               |
    |     - Set job status = "running"                          |
    |     - Load site profile (if exists)                       |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  7. LAYER 1: curl_cffi (TLS Fingerprinting)               |
    |     - Chrome131 impersonation                             |
    |     - Realistic headers                                   |
    |     - 30s timeout                                         |
    |                                                           |
    |     SUCCESS (60%)? --> Continue to step 10                |
    |     CHALLENGE DETECTED? --> Escalate to Layer 2           |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  8. LAYER 2/3: Crawlee (HTTP -> Playwright)               |
    |     - HTTP mode first (200-500ms)                         |
    |     - Playwright if JS required (2-5s)                    |
    |     - Stealth plugins enabled                             |
    |                                                           |
    |     SUCCESS (85%)? --> Continue to step 10                |
    |     CLOUDFLARE? --> Escalate to Layer 5                   |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  9. LAYER 4/5: Proxy + FlareSolverr                       |
    |     - Add BrightData residential proxy                    |
    |     - FlareSolverr for Cloudflare challenges              |
    |     - 10-30s timeout                                      |
    |                                                           |
    |     SUCCESS (95%)? --> Continue to step 10                |
    |     FAILED? --> Mark job as failed                        |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  10. STORE RESULTS                                        |
    |      - Upload HTML to S3: {tenant_id}/{job_id}/content.html|
    |      - Upload Markdown: {tenant_id}/{job_id}/content.md   |
    |      - Update job record with S3 keys                     |
    |      - Set status = "completed"                           |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  11. TRACK USAGE                                          |
    |      - INSERT into usage_records                          |
    |      - Trigger updates usage_summary                      |
    |      - Include layer_used, proxy_used, cost_cents         |
    +----------------------------------------------------------+
                          |
                          v
    +----------------------------------------------------------+
    |  12. CLIENT POLLS STATUS                                  |
    |      GET /v2/scrape/{id}                                  |
    |      - Return presigned S3 URLs (1hr expiry)              |
    |      - Include metadata (layer used, elapsed time)        |
    +----------------------------------------------------------+
```

### 1.3 Scalability Path

The architecture is designed for horizontal scaling with clear capacity thresholds and upgrade paths.

| Volume | Architecture | Infrastructure | Cost/Month | Response P99 |
|--------|-------------|----------------|-----------|--------------|
| **100K jobs/day** | Single region, 3 workers | 3 ECS tasks (2vCPU, 4GB each), 1 RDS (db.t3.medium), 1 ElastiCache (cache.t3.medium) | $500 | <30s |
| **1M jobs/day** | Multi-AZ, 10 workers | 10 ECS tasks, RDS Multi-AZ, ElastiCache Sentinel | $1,500 | <30s |
| **10M jobs/day** | Multi-region, 100 workers | 100 ECS tasks, Aurora Global, ElastiCache Global | $5,000 | <30s |
| **100M jobs/day** | Global CDN, 500+ workers | 500+ ECS tasks, Aurora Serverless, Global accelerator | $15,000+ | <30s |

### 1.4 Bottleneck Analysis

| Bottleneck | Threshold | Impact | Mitigation Strategy | Contingency |
|------------|-----------|--------|---------------------|-------------|
| **PostgreSQL Connections** | 500 concurrent | New connections rejected | PgBouncer connection pooler, increase max_connections to 1000 | Aurora Serverless with auto-scaling connections |
| **Redis Memory** | 16GB at 10M jobs/month | Cache eviction, performance degradation | LRU eviction policy, move sessions to PostgreSQL | Redis Cluster with sharding |
| **Browser Memory** | 100-200MB per instance | OOM kills, worker crashes | Worker pool management, kill idle browsers after 60s, horizontal scaling | Switch to HTTP-only mode for burst traffic |
| **Proxy Bandwidth** | 30GB/month at 100K jobs/day | Cost explosion, rate limits | Tier-based usage (only Enterprise gets residential proxies), volume discounts with BrightData, response caching | Circuit breaker at $500/month budget |
| **API Server CPU** | 80% utilization | Increased latency, timeouts | Auto-scaling group with CPU-based triggers | Pre-warmed standby instances |
| **Job Queue Depth** | 10,000 pending jobs | SLA breach, customer complaints | Priority queues by tier, auto-scale workers on queue depth | Shed load from free tier during peak |

---

## 2. Technology Stack Decisions

This section documents all major technology decisions with full rationale, trade-offs, and risk mitigation strategies.

### 2.1 Decision 1: Crawlee (Python) over Firecrawl (TypeScript/Node.js)

**Decision Date:** 2026-02-02
**Decision Owner:** Architecture Team
**Status:** Approved

#### Comparison Matrix

| Aspect | Crawlee | Firecrawl | Winner |
|--------|---------|-----------|--------|
| **Language** | Python | TypeScript/Node.js | Crawlee (team expertise, data ecosystem) |
| **Code Complexity** | ~250 LoC for API | ~15,000+ LoC | Crawlee (60x simpler) |
| **Services Required** | 4 (API, Worker, Redis, PostgreSQL) | 7 (API, Playwright, Redis, PostgreSQL, Tor, FlareSolverr, RabbitMQ) | Crawlee (43% fewer services) |
| **RAM at 300K jobs** | 12GB | 18GB | Crawlee (33% less memory) |
| **Cost/Month** | $965 | $1,500-3,000 | Crawlee (35-50% savings) |
| **Team Fit** | Python-native | Requires Node.js expertise | Crawlee |
| **Maintenance Time** | 20% of team effort | 50% of team effort | Crawlee |
| **Performance (P99)** | <30s | <20s | Firecrawl (1.5x faster) |
| **Anti-Detection** | Built-in stealth | Advanced (Patchright + Tor) | Firecrawl (marginally better) |
| **Production Proven** | Apify ($50M+ platform) | Self-hosted not production-ready | Crawlee |

#### Decision Rationale

**Primary Drivers:**
1. **Architectural Simplicity:** 60% less infrastructure reduces operational burden for 1-3 person team
2. **Cost Efficiency:** 35-50% cost savings at 300K jobs/month ($965 vs $1,500-3,000)
3. **Team Alignment:** Python-first team, matches data engineering ecosystem
4. **Risk Reduction:** Proven at scale by Apify (processing billions of requests monthly)

**Accepted Trade-offs:**
- ~1.5x slower P99 latency (30s vs 20s) - acceptable for reliability over raw speed
- Less advanced anti-detection out-of-box - mitigated by adding curl_cffi and BrightData layers

#### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance unacceptable | Low | High | Week 2 PoC must validate <2x Firecrawl latency; optimize connection pooling, parallel requests, caching |
| Anti-detection insufficient | Medium | Medium | Add curl_cffi (Layer 1), BrightData proxies (Layer 4), FlareSolverr (Layer 5) |
| Apify kills open-source | Very Low | High | Engine abstraction layer allows swap to raw Playwright (6-week effort) |

#### Validation Criteria

- [ ] Week 2 PoC: Success rate >=90% across 20 test sites
- [ ] Week 2 PoC: Latency <=2x Firecrawl baseline
- [ ] Week 4: Production API handles 1000 req/min without degradation

---

### 2.2 Decision 2: arq (Python) over BullMQ (Node.js) for Job Queue

**Decision Date:** 2026-02-02
**Decision Owner:** Architecture Team
**Status:** Approved

#### Comparison Matrix

| Aspect | arq | BullMQ | Winner |
|--------|-----|--------|--------|
| **Language** | Python | Node.js | arq (single language stack) |
| **Data Store** | Redis | Redis | Tie |
| **Throughput** | 1000+ jobs/sec | 2000+ jobs/sec | BullMQ (but overkill for MVP) |
| **Memory Footprint** | Low (~50MB) | Medium (~150MB) | arq |
| **Operations Complexity** | Simple (Python only) | Complex (requires Node.js runtime) | arq |
| **Community** | Growing (3K+ GitHub stars) | Established (12K+ GitHub stars) | BullMQ |
| **Monitoring UI** | Basic (requires custom) | Bull Board included | BullMQ |
| **Priority Queues** | Supported | Supported | Tie |
| **Retry Logic** | Basic (configurable) | Advanced (exponential backoff, custom strategies) | BullMQ |

#### Decision Rationale

**Primary Drivers:**
1. **Language Consistency:** Python-native aligns with Crawlee and FastAPI stack
2. **Operational Simplicity:** No Node.js runtime needed, reduces deployment complexity
3. **Cost Efficiency:** Saves ~$100/month (no Node.js containers)
4. **Sufficient Performance:** 1000+ jobs/sec exceeds MVP needs (target: 100 jobs/sec)

**Accepted Trade-offs:**
- No built-in web UI for queue monitoring - mitigated by Prometheus/Grafana dashboards
- Less advanced retry strategies - acceptable for MVP, can implement custom logic
- Smaller community - arq is actively maintained by Samuel Colvin (Pydantic author)

#### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Throughput ceiling reached | Low | Medium | If exceeds 1000 jobs/sec (Month 18+), migrate to BullMQ (4-week effort) |
| Missing features | Medium | Low | Implement custom retry logic, monitoring via Prometheus |
| Maintainer abandonment | Very Low | Medium | Fork or migrate to Celery + RabbitMQ (more complex, but proven) |

#### Validation Criteria

- [ ] Week 4: Handle 500 concurrent jobs without queue backup
- [ ] Week 10: Load test at 1000 jobs/minute with <1% failure rate
- [ ] Month 6: Evaluate if BullMQ migration needed based on throughput

---

### 2.3 Decision 3: FastAPI (Python) over Node.js/Express

**Decision Date:** 2026-02-02
**Decision Owner:** Architecture Team
**Status:** Approved

#### Comparison Matrix

| Aspect | FastAPI | Node.js/Express | Winner |
|--------|---------|-----------------|--------|
| **Framework Paradigm** | Modern, async-native | Traditional, callback-based | FastAPI |
| **Performance** | ~200K req/sec (Starlette) | ~100K req/sec | FastAPI (2x faster) |
| **Type Safety** | Native (Pydantic) | Optional (TypeScript) | FastAPI |
| **API Documentation** | Auto-generated OpenAPI/Swagger | Manual | FastAPI (2 weeks saved) |
| **Validation** | Declarative (Pydantic models) | Imperative (express-validator) | FastAPI |
| **Learning Curve** | Moderate | Moderate | Tie |
| **Team Fit** | Python team | JavaScript team | FastAPI (Python-first) |
| **Ecosystem** | Rich async libraries (asyncpg, aioboto3) | Largest package ecosystem | Express (but not needed) |

#### Decision Rationale

**Primary Drivers:**
1. **Performance:** 2x more efficient than Express under async load
2. **Developer Productivity:** Auto-generated OpenAPI docs save 2 weeks of documentation work
3. **Type Safety:** Pydantic validation prevents entire categories of bugs at runtime
4. **Team Alignment:** Python expertise already on team

**Accepted Trade-offs:**
- Smaller ecosystem than Node.js - mitigated by comprehensive Python data science libraries
- Less middleware variety - acceptable, security middleware exists for all needs

#### Code Comparison

**FastAPI (50 lines for endpoint + validation + docs):**
```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional

class ScrapeRequest(BaseModel):
    url: HttpUrl
    formats: list[str] = ["markdown", "html"]
    timeout: int = 60000  # Validated automatically

class ScrapeResponse(BaseModel):
    success: bool
    id: str
    status: str

@app.post("/v2/scrape", response_model=ScrapeResponse)
async def scrape(
    request: ScrapeRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    # Auto-validated, auto-documented, type-safe
    job = await create_scrape_job(tenant_id, request.url)
    return ScrapeResponse(success=True, id=job.id, status="pending")
```

**Express Equivalent (80+ lines for same functionality):**
```javascript
const express = require('express');
const { body, validationResult } = require('express-validator');

app.post('/v2/scrape',
    body('url').isURL(),
    body('formats').isArray(),
    body('timeout').isInt({ min: 1000, max: 300000 }),
    async (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }
        // Manual validation, manual documentation, no type safety
        // ... 30 more lines
    }
);
```

#### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance insufficient | Very Low | High | FastAPI is one of fastest Python frameworks; can optimize with Uvicorn workers |
| Missing middleware | Low | Low | FastAPI middleware ecosystem covers auth, CORS, rate limiting |
| Extreme performance needed | Low | Medium | Switch to Starlette (drop-in), or Go/Rust (Month 18+ if needed) |

---

### 2.4 Decision 4: PostgreSQL RLS over Application-Level Tenant Filtering

**Decision Date:** 2026-02-02
**Decision Owner:** Architecture Team
**Status:** Approved

#### Comparison Matrix

| Aspect | PostgreSQL RLS | Application-Level Filtering | Winner |
|--------|----------------|----------------------------|--------|
| **Security Guarantee** | Database-enforced, immune to app bugs | App-dependent, one bug = data breach | RLS (bulletproof) |
| **Performance** | -5% query overhead | Fast (no overhead) | App-Level (marginal) |
| **Bug Immunity** | Yes (SQL policies enforce isolation) | No (every query must include tenant_id) | RLS |
| **Implementation Complexity** | Medium (RLS policy setup) | High (every query, every developer) | RLS |
| **Scalability** | Linear with tenant count | Linear with tenant count | Tie |
| **Audit Compliance** | Easy (policies documented in DB) | Hard (must trace all code paths) | RLS |
| **Testing Confidence** | High (impossible to leak data) | Low (need exhaustive testing) | RLS |

#### Decision Rationale

**Primary Drivers:**
1. **Security:** Database-enforced isolation is immune to application bugs - critical for enterprise customers
2. **Compliance:** SOC 2 and GDPR require demonstrable data isolation - RLS provides audit trail
3. **Developer Safety:** Developers cannot accidentally forget tenant_id filter - RLS enforces automatically
4. **Code Simplicity:** Queries don't need WHERE tenant_id = X everywhere

**Accepted Trade-offs:**
- 5% query overhead - negligible for <50ms queries (adds ~2.5ms)
- Debugging complexity - requires setting session variable to test specific tenant

#### Implementation

```sql
-- Enable RLS on all data tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;

-- Policy: Tenant isolation (applied automatically to all queries)
CREATE POLICY tenant_isolation ON jobs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::text);

-- Application sets tenant context per-request
-- SET LOCAL app.current_tenant_id = 'tenant_123';
```

```python
# Every database operation automatically filtered
async with db.with_tenant(tenant_id) as conn:
    # This query is SAFE - RLS enforces tenant isolation
    # Even if developer forgets WHERE clause, RLS adds it
    jobs = await conn.fetch("SELECT * FROM jobs WHERE status = 'pending'")
    # RLS rewrites to: SELECT * FROM jobs WHERE status = 'pending' AND tenant_id = 'tenant_123'
```

#### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RLS policy misconfiguration | Low | Very High | Security audit before production (Month 9), automated isolation tests |
| Performance degradation | Low | Medium | Index on tenant_id column, monitor query plans |
| RLS bypass bug | Very Low | Very High | Use separate admin_role for ops (bypasses RLS intentionally) |

---

### 2.5 Decision 5: BrightData over Oxylabs/Smartproxy for Residential Proxies

**Decision Date:** 2026-02-02
**Decision Owner:** Architecture Team
**Status:** Approved

#### Comparison Matrix

| Provider | Cost/GB | Success Rate | Speed | Detection Risk | Premium Support | Compliance |
|----------|---------|--------------|-------|----------------|-----------------|------------|
| **BrightData** | $12.75 | 99.9% | Fast | Very Low | 24/7 | SOC 2, GDPR |
| Oxylabs | $15.00 | 99.8% | Fast | Low | 24/7 | SOC 2, GDPR |
| Smartproxy | $10.00 | 95.0% | Medium | Medium | Basic | GDPR |
| IPRoyal | $8.00 | 92.0% | Medium | High | Email only | Basic |

#### Decision Rationale

**Primary Drivers:**
1. **Reliability:** 99.9% success rate is critical for enterprise SLAs - 4.9% better than Smartproxy
2. **Anti-Detection:** BrightData's residential IPs are industry gold standard - used by Fortune 500
3. **Compliance:** SOC 2 certified - required for enterprise customers
4. **Support:** 24/7 premium support for incident resolution

**Accepted Trade-offs:**
- 27% cost premium over Smartproxy ($12.75 vs $10.00/GB)
- Higher cost than datacenter proxies - necessary for protected sites

#### Cost Projections

| Volume | BrightData Cost | Smartproxy Cost | Delta | Success Delta |
|--------|----------------|-----------------|-------|---------------|
| 10GB/month | $127.50 | $100.00 | +$27.50 | +4.9% success |
| 30GB/month | $382.50 | $300.00 | +$82.50 | +4.9% success |
| 100GB/month | $1,275.00 | $1,000.00 | +$275.00 | +4.9% success |

**ROI Analysis:** At $50/customer/month, the 4.9% success rate improvement retains ~2.5 additional customers per 50 = $125/month value. Cost delta at 30GB = $82.50. Net positive ROI.

#### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cost explosion | Medium | High | Start with 20% proxy usage cap, daily cost alerts at $500/month |
| BrightData service degradation | Low | High | Fallback to Oxylabs (pre-integrated), circuit breaker pattern |
| Bandwidth overuse | Medium | Medium | Per-tenant proxy quotas, cache responses aggressively |

---

### 2.6 Decision 6: Prometheus + Grafana over CloudWatch-Only

**Decision Date:** 2026-02-02
**Decision Owner:** Architecture Team
**Status:** Approved

#### Comparison Matrix

| Aspect | Prometheus + Grafana | CloudWatch Only | Winner |
|--------|---------------------|-----------------|--------|
| **Cost (at scale)** | $100/month (self-hosted) | $150/month | Prometheus (33% cheaper) |
| **Vendor Lock-in** | None (portable to any cloud) | AWS-only | Prometheus |
| **Visualization** | Excellent (Grafana dashboards) | Basic (limited customization) | Prometheus |
| **Self-Hosted** | Yes (full control) | No (managed only) | Prometheus |
| **Learning Curve** | Steep (PromQL, setup) | Gentle (integrated with AWS) | CloudWatch |
| **Time to Alert** | <30 seconds (push model) | 1-5 minutes (pull model) | Prometheus |
| **Custom Metrics** | Unlimited (free) | $0.30 per custom metric/month | Prometheus |
| **Retention** | Configurable (local/remote) | 15 months max | Prometheus |

#### Decision Rationale

**Primary Drivers:**
1. **Portability:** No vendor lock-in - can migrate to GCP/Azure without changing monitoring
2. **Cost Efficiency:** 33% cheaper at scale, unlimited custom metrics
3. **Visualization:** Grafana dashboards can be embedded in customer portal for transparency
4. **Alerting Speed:** <30s detection critical for SLA compliance

**Accepted Trade-offs:**
- Operational complexity of self-hosting - mitigated by Grafana Cloud managed option ($50/month)
- Learning curve for PromQL - team training investment (1 week)

#### Monitoring Architecture

```
+------------------+     +------------------+     +------------------+
|   FastAPI App    |     |   Crawlee        |     |   PostgreSQL     |
|                  |     |   Workers        |     |                  |
|  /metrics        |     |  /metrics        |     |  pg_exporter     |
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         +------------------------+------------------------+
                                  |
                                  v
                    +----------------------------+
                    |     Prometheus Server      |
                    |                            |
                    |  - Scrape every 15s        |
                    |  - Store 15 days locally   |
                    |  - AlertManager integration|
                    +-------------+--------------+
                                  |
                                  v
                    +----------------------------+
                    |        Grafana             |
                    |                            |
                    |  Dashboards:               |
                    |  - Platform Overview       |
                    |  - Per-Tenant Usage        |
                    |  - Worker Health           |
                    |  - Cost Tracking           |
                    |  - SLA Compliance          |
                    +----------------------------+
```

#### Key Metrics to Monitor

| Category | Metric | Alert Threshold | Action |
|----------|--------|-----------------|--------|
| **API Health** | Request latency P99 | >5s | Scale API servers |
| **API Health** | Error rate | >5% | Page on-call |
| **Workers** | Queue depth | >2000 | Scale workers |
| **Workers** | Job success rate | <90% | Investigate anti-detection |
| **Database** | Connection pool usage | >80% | Add PgBouncer |
| **Cost** | Daily proxy spend | >$50 | Review tenant usage |
| **SLA** | Uptime | <99.9% | Incident response |

#### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Prometheus outage | Low | High | Run 2 instances with federation |
| Storage overwhelm | Medium | Medium | Configure retention (15 days) and remote storage (S3) |
| Team unfamiliarity | Medium | Low | 1-week training on PromQL, pre-built dashboards |

---

### 2.7 Decision 7: Gradual Migration (5 Phases) over Big Bang

**Decision Date:** 2026-02-02
**Decision Owner:** Architecture Team
**Status:** Approved

#### Comparison Matrix

| Approach | Risk Level | Rollback Time | Validation Period | Extra Cost | Confidence |
|----------|------------|---------------|-------------------|-----------|------------|
| **Gradual (20%->50%->80%->100%)** | Low | <5 minutes | Continuous (2 weeks) | +$1,000 | High |
| Big Bang (0%->100%) | Very High | Hours (if possible) | None until cutover | $0 | Low |
| Canary (1% first) | Very Low | <1 minute | Slowest ramp | +$1,500 | Very High |

#### Decision Rationale

**Primary Drivers:**
1. **Risk Mitigation:** Catch issues early with small traffic percentage
2. **Instant Rollback:** DNS/load balancer switch takes <5 minutes
3. **Continuous Validation:** Real production metrics comparison throughout
4. **Customer Confidence:** Zero downtime = no customer impact during migration

**Accepted Trade-offs:**
- $1,000 extra infrastructure cost (running both systems for 2 weeks)
- Extended timeline (10 days instead of instant cutover)
- Operational complexity (monitoring two systems simultaneously)

#### Migration Phases

```
+-------------------------------------------------------------------+
|  WEEK 11-12: MIGRATION EXECUTION                                  |
+-------------------------------------------------------------------+
|                                                                   |
|  Day 1-2: PHASE 0 - Staging Deployment                            |
|  +---------------------------------------------------------------+|
|  | - Deploy Crawlee platform to staging environment              ||
|  | - Run full integration test suite                             ||
|  | - Smoke test with 100 representative URLs                     ||
|  | - Security scan (OWASP ZAP)                                   ||
|  | - Performance baseline (Locust)                               ||
|  +---------------------------------------------------------------+|
|                                                                   |
|  Day 3-4: PHASE 1 - 20% Traffic                                   |
|  +---------------------------------------------------------------+|
|  | - Route 20% of production traffic to Crawlee                  ||
|  | - 80% continues to Firecrawl                                  ||
|  | - Comparison dashboard: success rate, latency, errors         ||
|  | - Alert if Crawlee success <90% of Firecrawl baseline         ||
|  +---------------------------------------------------------------+|
|                                                                   |
|  Day 5-6: PHASE 2 - 50% Traffic                                   |
|  +---------------------------------------------------------------+|
|  | - Increase to 50% traffic on Crawlee                          ||
|  | - Full metric comparison                                      ||
|  | - Cost tracking (validate projections)                        ||
|  | - Team review meeting                                         ||
|  +---------------------------------------------------------------+|
|                                                                   |
|  Day 7-8: PHASE 3 - 80% Traffic                                   |
|  +---------------------------------------------------------------+|
|  | - Increase to 80% traffic on Crawlee                          ||
|  | - Prepare final cutover checklist                             ||
|  | - Update runbooks with Crawlee-specific procedures            ||
|  | - Customer communication drafted                              ||
|  +---------------------------------------------------------------+|
|                                                                   |
|  Day 9-10: PHASE 4 - 100% Cutover                                 |
|  +---------------------------------------------------------------+|
|  | - Route 100% traffic to Crawlee                               ||
|  | - Monitor closely for 24 hours                                ||
|  | - Keep Firecrawl running (instant rollback)                   ||
|  | - Success celebration (if all metrics green!)                 ||
|  +---------------------------------------------------------------+|
|                                                                   |
|  Week 13-14: Post-Cutover                                         |
|  +---------------------------------------------------------------+|
|  | - Keep Firecrawl running 2 additional weeks                   ||
|  | - Validate no edge cases missed                               ||
|  | - Decommission Firecrawl infrastructure                       ||
|  | - Cost savings realized                                       ||
|  +---------------------------------------------------------------+|
+-------------------------------------------------------------------+
```

#### Success Validation Criteria

| Metric | Firecrawl Baseline | Crawlee Target | Rollback Trigger |
|--------|-------------------|----------------|------------------|
| Success Rate | 95% | >=95% (same or better) | <90% |
| P99 Latency | 20s | <=30s (<=1.5x slower) | >60s |
| Error Rate | 3% | <=5% | >10% |
| Cost/1K Jobs | $4.50 | <=$3.50 (savings target) | >$5.00 |

#### Rollback Plan

| Scenario | Detection Method | Time to Rollback | Procedure |
|----------|-----------------|------------------|-----------|
| Success rate <90% | Automated Grafana alert | <5 minutes | DNS switch to Firecrawl ALB |
| P99 latency >60s | Grafana dashboard | <30 minutes | Reduce Crawlee traffic, analyze |
| Cost >$2K/day | Cost monitoring | <1 hour | Circuit breaker on proxy usage |
| Security incident | Sentry alert | <15 minutes | Immediate DNS switch, incident response |
| Customer complaints | Support tickets | <2 hours | Evaluate, potentially partial rollback |

---

## 3. Scalability & Performance

### 3.1 Performance Benchmarks

The following benchmarks represent target metrics for the platform at various stages of maturity.

#### Latency Targets by Mode

| Scrape Mode | P50 Target | P95 Target | P99 Target | Throughput |
|-------------|------------|------------|------------|------------|
| **Layer 1: curl_cffi** | 50ms | 200ms | 500ms | 200 req/s per worker |
| **Layer 2: Crawlee HTTP** | 300ms | 800ms | 1,500ms | 50 req/s per worker |
| **Layer 3: Crawlee Browser** | 2,500ms | 4,500ms | 8,000ms | 10 req/s per worker |
| **Layer 4: Browser + Proxy** | 3,500ms | 6,000ms | 10,000ms | 5 req/s per worker |
| **Layer 5: FlareSolverr** | 10,000ms | 20,000ms | 30,000ms | 2 req/s per worker |

#### Scaling Triggers

| Metric | Warning Threshold | Critical Threshold | Auto-Scale Action |
|--------|-------------------|--------------------|--------------------|
| Job Queue Depth | >500 pending | >2,000 pending | Add 2 workers |
| API Server CPU | >60% sustained | >80% sustained | Add 1 API instance |
| Worker CPU | >70% sustained | >85% sustained | Add 2 workers |
| Response Time P99 | >20s | >30s | Scale up workers |
| Database Connections | >400 active | >480 active | Add PgBouncer |
| Redis Memory | >80% | >95% | Add cache nodes |
| Proxy Cost/Day | >$30 | >$50 | Alert operations |

### 3.2 Scaling Strategy by Volume

#### 100K Jobs/Day (Month 4 MVP)

```
Infrastructure:
- API: 1 ECS task (2 vCPU, 4GB)
- Workers: 3 ECS tasks (4 vCPU, 8GB each)
- Redis: ElastiCache cache.t3.medium (2GB)
- PostgreSQL: RDS db.t3.medium (4GB)
- S3: Standard tier, 100GB estimated

Cost Breakdown:
- Compute (Fargate): $350/month
- Redis: $70/month
- PostgreSQL: $70/month
- S3: $3/month
- Data Transfer: $50/month
- Proxies (20% usage): $382/month
Total: ~$925/month
```

#### 1M Jobs/Day (Month 12 Target)

```
Infrastructure:
- API: 3 ECS tasks (load balanced)
- Workers: 10 ECS tasks (horizontal scale)
- Redis: ElastiCache Sentinel cluster (16GB)
- PostgreSQL: RDS with read replica
- S3: Intelligent tiering, 1TB estimated

Cost Breakdown:
- Compute (Fargate): $900/month
- Redis: $200/month
- PostgreSQL: $200/month
- S3: $25/month
- Data Transfer: $150/month
- Proxies: $500/month (bulk discount)
Total: ~$1,975/month

Efficiency: $1.97 per 1000 jobs (improved from $3.08)
```

#### 10M Jobs/Day (Month 18 Stretch)

```
Infrastructure:
- API: 10 ECS tasks (global CDN)
- Workers: 100 ECS tasks (multi-zone)
- Redis: Global Datastore (64GB)
- PostgreSQL: Aurora Global with sharding
- S3: Cross-region replication, 10TB

Cost Breakdown:
- Compute (Fargate): $3,500/month
- Redis: $500/month
- PostgreSQL: $800/month
- S3: $250/month
- Data Transfer: $500/month
- Proxies: $1,500/month (enterprise discount)
Total: ~$7,050/month

Efficiency: $0.71 per 1000 jobs (70% improvement)
```

### 3.3 Performance Optimization Strategies

#### Database Optimization

```sql
-- Indexing strategy for common queries
CREATE INDEX idx_jobs_tenant_status ON jobs(tenant_id, status)
    WHERE status IN ('pending', 'running');
CREATE INDEX idx_jobs_tenant_created ON jobs(tenant_id, created_at DESC);
CREATE INDEX idx_usage_tenant_month ON usage_records(tenant_id, month);

-- Connection pooling via PgBouncer
-- max_client_conn = 1000
-- default_pool_size = 50
-- reserve_pool_size = 10
```

#### Caching Strategy

```python
# Redis caching layers
CACHE_CONFIG = {
    "tenant_config": {
        "ttl": 300,  # 5 minutes
        "key_pattern": "tenant:{tenant_id}:config"
    },
    "rate_limit": {
        "ttl": 3600,  # 1 hour (sliding window)
        "key_pattern": "rate_limit:{tenant_id}:hour"
    },
    "job_status": {
        "ttl": 60,  # 1 minute
        "key_pattern": "job:{job_id}:status"
    },
    "site_profile": {
        "ttl": 86400,  # 24 hours
        "key_pattern": "site_profile:{domain}"
    }
}
```

#### Worker Pool Management

```python
# Browser instance lifecycle management
BROWSER_CONFIG = {
    "max_instances_per_worker": 5,
    "idle_timeout_seconds": 60,
    "max_memory_mb": 300,
    "crash_restart_delay": 5,
    "warmup_pool_size": 2
}

# Kill idle browsers to reclaim memory
async def cleanup_idle_browsers():
    for browser in browser_pool:
        if browser.idle_time > 60:
            await browser.close()
            browser_pool.remove(browser)
```

---

## 4. Security & Compliance

### 4.1 Tenant Isolation Architecture

#### Database Layer (PostgreSQL RLS)

```sql
-- Row-Level Security enforces tenant isolation at database level
-- This is immune to application bugs - cannot be bypassed

-- Enable RLS on all data tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Create isolation policy
CREATE POLICY tenant_isolation ON jobs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::text);

-- Application connection sets tenant context
-- SET LOCAL app.current_tenant_id = '550e8400-e29b-41d4-a716-446655440000';

-- Admin role bypasses RLS for operations/analytics
CREATE ROLE admin_role BYPASSRLS;
```

#### API Layer

```python
# Every API request goes through tenant resolution
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # Extract and verify API key
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not api_key:
        return JSONResponse(status_code=401, content={"error": "Missing API key"})

    # Verify and resolve tenant
    tenant_id = await verify_api_key(api_key)

    if not tenant_id:
        return JSONResponse(status_code=401, content={"error": "Invalid API key"})

    # Set tenant context for all database operations
    request.state.tenant_id = tenant_id

    return await call_next(request)
```

#### Storage Layer (S3 Prefix Isolation)

```
Bucket: scraper-platform-data/
    tenant_abc123/
        job_001/
            content.html
            content.md
            metadata.json
        job_002/
            ...
    tenant_def456/
        job_003/
            ...

# Each tenant can only access their prefix
# Presigned URLs include tenant verification
```

### 4.2 API Key Security

#### Key Format and Storage

```python
# Key format: fc_live_<32 random characters>
# Example: fc_live_abc123def456ghi789jkl012mno345pqr

# Storage: Only bcrypt hash stored, never plaintext
import bcrypt

def create_api_key(tenant_id: str) -> tuple[str, str]:
    """Generate and hash API key."""
    key = f"fc_live_{secrets.token_urlsafe(32)}"
    key_hash = bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()
    return key, key_hash  # Return plaintext once, store only hash
```

#### Key Verification (Constant-Time)

```python
def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """Verify API key using constant-time comparison."""
    return bcrypt.checkpw(provided_key.encode(), stored_hash.encode())
```

#### Key Rotation

```python
# API keys are rotatable without downtime
async def rotate_api_key(tenant_id: str, old_key: str) -> str:
    """Generate new key, keep old key valid for 24 hours."""
    new_key, new_hash = create_api_key(tenant_id)

    # Create new key
    await db.execute(
        "INSERT INTO api_keys (tenant_id, key_hash, key_prefix) VALUES ($1, $2, $3)",
        tenant_id, new_hash, new_key[:16]
    )

    # Schedule old key revocation (24 hour grace period)
    await db.execute(
        "UPDATE api_keys SET revoked_at = NOW() + INTERVAL '24 hours' WHERE key_prefix = $1",
        old_key[:16]
    )

    return new_key
```

### 4.3 GDPR Compliance

| Requirement | Implementation | Validation |
|-------------|----------------|------------|
| **Right to Erasure** | DELETE /admin/tenants/{id}/data endpoint | Automated test verifies all S3 objects and DB records deleted |
| **Data Portability** | GET /v2/export/{tenant_id} returns all data as JSON | Export includes jobs, results, usage history |
| **Consent Tracking** | Tenant agreement timestamp stored | Audit log shows consent date |
| **Breach Notification** | Sentry alerts + incident response runbook | 72-hour SLA in operations manual |
| **Data Retention** | 30-day automatic deletion policy | S3 lifecycle rule, DB cleanup job |

### 4.4 SOC 2 Compliance (Enterprise Requirement)

| Control | Implementation | Evidence |
|---------|----------------|----------|
| **Access Controls** | RBAC with PostgreSQL roles | Role definitions in SQL migration |
| **Audit Logging** | All API calls logged with tenant_id | CloudWatch Logs with 90-day retention |
| **Encryption** | TLS 1.3 in transit, AES-256 at rest | AWS Certificate Manager, S3 SSE |
| **Incident Response** | 24-hour SLA, documented runbook | Runbook in /docs/incident-response.md |
| **Change Management** | Git-based deployments, PR reviews | GitHub Actions audit trail |

**Target:** SOC 2 Type II certification by Month 18

---

## 5. Infrastructure Cost Analysis

### 5.1 Development Cost (12 Weeks)

| Phase | Duration | Dev Hours | Cost @ $100/hr | Infrastructure | Total |
|-------|----------|-----------|---------------|----------------|-------|
| **Week 1-2: PoC** | 10 days | 80 | $8,000 | $100 | $8,100 |
| **Week 3-4: API Layer** | 10 days | 80 | $8,000 | $300 | $8,300 |
| **Week 5-6: Multi-Tenant** | 10 days | 100 | $10,000 | $500 | $10,500 |
| **Week 7-8: Anti-Detection** | 10 days | 100 | $10,000 | $800 | $10,800 |
| **Week 9-10: Hardening** | 10 days | 70 | $7,000 | $1,000 | $8,000 |
| **Week 11-12: Migration** | 10 days | 60 | $6,000 | $1,300 | $7,300 |
| **TOTAL** | **60 days** | **490** | **$49,000** | **$4,000** | **$53,000** |

### 5.2 Operational Cost (300K Jobs/Month Baseline)

| Component | Unit | Monthly Cost | Notes |
|-----------|------|-------------|-------|
| **Compute (ECS Fargate)** | | | |
| API: 2 tasks x 1vCPU, 2GB | $0.04/hr | $58 | Auto-scaled on demand |
| Workers: 5 avg x 2vCPU, 4GB | $0.08/hr | $292 | Scales with queue depth |
| **Data Services** | | | |
| ElastiCache Redis (cache.t3.medium) | per month | $70 | 3GB capacity, Sentinel HA |
| RDS PostgreSQL (db.t3.medium) | per month | $70 | 20GB storage, Multi-AZ option |
| S3 storage (1TB) | per month | $23 | Intelligent tiering |
| S3 requests (300K PUT, 1M GET) | per request | $5 | PUT: $0.005/1K, GET: $0.0004/1K |
| **Network** | | | |
| Data transfer (500GB/month) | per GB | $45 | $0.09/GB after free tier |
| **Anti-Detection (selective)** | | | |
| BrightData proxies (20% usage) | per GB | $382 | ~30GB at $12.75/GB |
| FlareSolverr (5% usage) | per request | $20 | ~10,000 requests @ $0.002 |
| **Monitoring** | | | |
| Prometheus + Grafana | self-hosted | $0 | Runs on existing compute |
| Sentry (error tracking) | per month | $26 | Team plan |
| **TOTAL** | | **$991** | Production operational cost |

### 5.3 Cost Comparison: Crawlee vs Firecrawl

| Volume | Crawlee Cost | Firecrawl Cost | Savings | Savings % |
|--------|-------------|---------------|---------|-----------|
| **300K/month** | $991 | $1,500-3,000 | $509-2,009 | 34-67% |
| **1M/month** | $1,975 | $3,500-5,000 | $1,525-3,025 | 44-61% |
| **10M/month** | $7,050 | $12,000-15,000 | $4,950-7,950 | 41-53% |
| **100M/month** | $25,000 | $50,000-70,000 | $25,000-45,000 | 50-64% |

### 5.4 Break-Even Analysis

```
Development Investment: $53,000
Monthly Operational Cost: $991
Target Customer Revenue: $50/month (Pro tier)

Gross Margin Calculation:
- Revenue per customer: $50/month
- Cost per customer (at 50 customers): $991 / 50 = $19.82
- Gross margin: ($50 - $19.82) / $50 = 60.4%

Break-Even Timeline:
- Monthly profit margin: $50 - $19.82 = $30.18 per customer
- Customers needed for $2K MRR: 40 customers
- Development ROI timeline:
  - Month 6: 25 customers = $755/month profit
  - Month 9: 40 customers = $1,207/month profit
  - Month 12: 50 customers = $1,509/month profit
  - Total profit by Month 12: ~$10,000
  - Payback period: ~15-18 months

Accelerated Path (100 customers by Month 12):
- Revenue: $5,000/month
- Cost at scale: $1,500/month
- Profit: $3,500/month
- Payback period: ~10 months
```

---

## 6. Migration Strategy

### 6.1 Migration Architecture

```
                    PRODUCTION TRAFFIC
                           |
                           v
                    +-------------+
                    |   Route53   |
                    |   DNS       |
                    +------+------+
                           |
                           v
                    +-------------+
                    |    ALB      |
                    | (Weighted   |
                    |  Routing)   |
                    +------+------+
                           |
              +------------+------------+
              |                         |
     Weight: 20%               Weight: 80%
              |                         |
              v                         v
    +------------------+      +------------------+
    |   Crawlee        |      |   Firecrawl      |
    |   Platform       |      |   (Legacy)       |
    |                  |      |                  |
    | - New API        |      | - Existing API   |
    | - Crawlee workers|      | - Playwright svc |
    | - PostgreSQL     |      | - Redis          |
    | - Redis          |      | - PostgreSQL     |
    +------------------+      +------------------+
              |                         |
              +------------+------------+
                           |
                           v
                    +--------------+
                    |   Comparison |
                    |   Dashboard  |
                    |              |
                    | - Success %  |
                    | - Latency    |
                    | - Errors     |
                    | - Cost       |
                    +--------------+
```

### 6.2 Phase-by-Phase Execution

#### Phase 0: Staging Deployment (Days 1-2)

**Objectives:**
- Deploy Crawlee platform to isolated staging environment
- Validate all components functional
- Security scan and performance baseline

**Checklist:**
- [ ] ECS cluster deployed with Crawlee workers
- [ ] PostgreSQL schema migrated with test data
- [ ] Redis cluster operational
- [ ] S3 bucket created with lifecycle policies
- [ ] Integration test suite passes (>95% green)
- [ ] OWASP ZAP security scan (no critical findings)
- [ ] Locust load test: 1000 concurrent users, <5% error rate
- [ ] Monitoring dashboards configured

#### Phase 1: 20% Traffic (Days 3-4)

**Objectives:**
- Route 20% of production traffic to Crawlee
- Establish baseline comparison metrics
- Identify any critical issues early

**Configuration:**
```yaml
# ALB target group weights
target_groups:
  - name: crawlee-platform
    weight: 20
    health_check:
      path: /health
      interval: 30
      timeout: 5
  - name: firecrawl-legacy
    weight: 80
    health_check:
      path: /test
      interval: 30
      timeout: 5
```

**Success Criteria:**
- Crawlee success rate within 5% of Firecrawl
- No critical errors in Sentry
- Latency within 2x of Firecrawl
- Zero data integrity issues

**Rollback Trigger:**
- Success rate <85% (vs Firecrawl baseline 95%)
- Error rate >10%
- Customer complaints

#### Phase 2: 50% Traffic (Days 5-6)

**Objectives:**
- Increase confidence with equal traffic split
- Validate cost projections
- Full metric comparison

**Monitoring Focus:**
- Side-by-side latency percentiles
- Cost per request comparison
- Error type analysis
- Resource utilization patterns

#### Phase 3: 80% Traffic (Days 7-8)

**Objectives:**
- Final validation before full cutover
- Prepare rollback procedures
- Customer communication

**Preparation:**
- Update status page with migration notice
- Prepare customer email for any issues
- Final review of runbooks

#### Phase 4: 100% Cutover (Days 9-10)

**Objectives:**
- Complete migration to Crawlee
- Maintain Firecrawl for instant rollback
- 24-hour intensive monitoring

**Post-Cutover Checklist:**
- [ ] All traffic routing to Crawlee
- [ ] Firecrawl still running (standby)
- [ ] On-call engineer assigned
- [ ] Hourly metric review for 24 hours
- [ ] Customer support briefed

#### Week 13-14: Decommission Firecrawl

**Objectives:**
- Validate no edge cases missed
- Realize infrastructure cost savings
- Archive Firecrawl codebase

**Decommission Checklist:**
- [ ] 14 days without rollback needed
- [ ] All metrics within target range
- [ ] No customer escalations
- [ ] Firecrawl infrastructure terminated
- [ ] Git repository archived
- [ ] Documentation updated

---

## 7. Technical Risks & Mitigation

### 7.1 Risk Matrix

| Risk | Probability | Impact | Risk Score | Mitigation | Contingency |
|------|-------------|--------|------------|------------|-------------|
| **PoC success rate <90%** | Low | Very High | High | Week 1-2 validation with 20 sites, iterative optimization | Debug 2 days; abort if still <90%, optimize Firecrawl instead |
| **RLS performance degradation** | Low | Medium | Low | Index on tenant_id, benchmark queries | Switch to application-level filtering |
| **Proxy cost explosion** | Medium | High | High | 20% usage cap, daily cost monitoring, circuit breaker | Hard cap at $500/month, degrade to Tor |
| **Database scaling limit** | Low | High | Medium | Connection pooling (PgBouncer), sharding plan | Aurora Serverless or CockroachDB |
| **FlareSolverr instability** | Medium | Medium | Medium | 60s timeout, graceful fallback | Skip Cloudflare sites, notify user |
| **Worker memory leaks** | Medium | Medium | Medium | Browser lifecycle management, 60s idle kill | Restart workers hourly |
| **Apify discontinues Crawlee** | Very Low | High | Low | Engine abstraction layer | Migrate to raw Playwright (6 weeks) |
| **BrightData service degradation** | Low | High | Medium | Pre-integrated Oxylabs fallback | Circuit breaker, switch providers |
| **Team capacity constraints** | Medium | Medium | Medium | Phased rollout, defer features | Hire contractor, extend timeline |
| **Security vulnerability discovered** | Low | Very High | High | Regular security audits, dependency scanning | Incident response, immediate patch |

### 7.2 Single Points of Failure Analysis

| Component | Failure Impact | MTTR | Mitigation |
|-----------|---------------|------|------------|
| **PostgreSQL Primary** | All writes fail, reads degraded | 5 min | Multi-AZ deployment, automated failover to standby |
| **Redis Master** | Rate limits fail, job queue unavailable | 2 min | Sentinel cluster with automatic promotion |
| **API Server** | No new requests accepted | 1 min | Multiple instances behind ALB, health checks |
| **Crawlee Worker** | Job processing stops | 30 sec | Auto-scaling group, health checks replace unhealthy |
| **FlareSolverr** | 5% of jobs fail (Cloudflare sites) | 5 min | Graceful degradation, retry without FlareSolverr |
| **S3** | Cannot store results | N/A (AWS SLA) | Multi-region replication (if critical) |

### 7.3 Disaster Recovery Plan

| Scenario | RTO | RPO | Recovery Procedure |
|----------|-----|-----|-------------------|
| **Database Corruption** | 5 min | 1 min | Failover to read replica, restore from point-in-time backup |
| **Region Outage** | 30 min | 5 min | DNS failover to secondary region (Month 12+ feature) |
| **Complete Infrastructure Loss** | 4 hours | 1 hour | Terraform rebuild from scratch, restore from S3 backups |
| **Security Breach** | Immediate | N/A | Revoke all API keys, rotate secrets, forensic investigation |

---

## 8. Operational Readiness

### 8.1 Monitoring Stack Architecture

```
+-------------------+     +-------------------+     +-------------------+
|   Application     |     |   Infrastructure  |     |   External        |
|   Metrics         |     |   Metrics         |     |   Monitors        |
+-------------------+     +-------------------+     +-------------------+
| - Request rate    |     | - CPU utilization |     | - Uptime Robot    |
| - Latency (P50,   |     | - Memory usage    |     |   (5 min check)   |
|   P95, P99)       |     | - Disk I/O        |     | - PagerDuty       |
| - Error rate      |     | - Network I/O     |     |   integration     |
| - Success rate    |     | - Container count |     |                   |
| - Queue depth     |     | - DB connections  |     |                   |
| - Cost per job    |     | - Redis memory    |     |                   |
+--------+----------+     +--------+----------+     +--------+----------+
         |                         |                         |
         +-----------+-------------+-----------+-------------+
                     |                         |
                     v                         v
           +-------------------+     +-------------------+
           |   Prometheus      |     |   CloudWatch      |
           |                   |     |   Logs            |
           | - 15s scrape      |     |                   |
           | - 15 day retain   |     | - API logs        |
           | - AlertManager    |     | - Worker logs     |
           +--------+----------+     | - System logs     |
                    |                +-------------------+
                    v
           +-------------------+
           |   Grafana         |
           |                   |
           | Dashboards:       |
           | 1. Platform       |
           |    Overview       |
           | 2. Tenant Usage   |
           | 3. Worker Health  |
           | 4. Cost Tracking  |
           | 5. SLA Compliance |
           +-------------------+
                    |
                    v
           +-------------------+
           |   Sentry          |
           |                   |
           | - Error tracking  |
           | - Release health  |
           | - Performance     |
           +-------------------+
```

### 8.2 SLA Definitions

| Metric | Target | Measurement | Breach Response |
|--------|--------|-------------|-----------------|
| **Uptime** | 99.9% (43 min/month) | Uptime Robot synthetic checks | Credit 10% of monthly bill |
| **API Latency P95** | <5s | Prometheus histogram | Investigate, scale if needed |
| **Job Completion P99** | <30s | Prometheus histogram | Investigate worker backlog |
| **Support Response (Critical)** | <1 hour | Zendesk SLA | Escalate to on-call |
| **Support Response (High)** | <4 hours | Zendesk SLA | Queue priority |
| **Support Response (Normal)** | <24 hours | Zendesk SLA | Standard queue |
| **Data Recovery (RTO)** | <5 min | DR testing | Automated failover |
| **Data Loss (RPO)** | <1 min | Continuous replication | Point-in-time restore |

### 8.3 Incident Response Procedures

#### Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| **P0 (Critical)** | Platform down, data loss risk | 15 min | API unreachable, database corruption |
| **P1 (High)** | Major feature broken, >10% errors | 1 hour | Job queue backed up, proxy failures |
| **P2 (Medium)** | Single customer impact | 4 hours | Tenant isolation issue, billing error |
| **P3 (Low)** | Minor issue, workaround exists | 24 hours | Documentation error, UI bug |

#### On-Call Rotation

```
Week 1: Engineer A (Primary), Engineer B (Secondary)
Week 2: Engineer B (Primary), Engineer C (Secondary)
Week 3: Engineer C (Primary), Engineer A (Secondary)

Escalation Path:
1. PagerDuty alert -> Primary on-call
2. No response in 10 min -> Secondary on-call
3. P0 not resolved in 30 min -> Engineering Manager
4. P0 not resolved in 1 hour -> CTO
```

#### Incident Runbook Template

```markdown
# Incident: [Title]
## Severity: P0/P1/P2/P3
## Status: Investigating/Identified/Resolved

### Timeline
- HH:MM - Alert triggered
- HH:MM - On-call acknowledged
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Resolved

### Root Cause
[Description of what caused the incident]

### Impact
- Users affected: X
- Duration: X minutes
- Data loss: Y/N

### Mitigation
[Steps taken to resolve]

### Prevention
[Changes to prevent recurrence]
```

---

## 9. Decision Log: Architecture Choices Summary

### 9.1 Complete Decision Registry

| # | Decision | Chosen | Alternative | Rationale | Trade-off Accepted | Risk Level |
|---|----------|--------|-------------|-----------|-------------------|------------|
| 1 | Scraping Engine | Crawlee (Python) | Firecrawl (TypeScript) | 35-50% cost savings, 60% less infrastructure, Python team fit | 1.5x slower P99 latency | Low |
| 2 | Job Queue | arq (Python) | BullMQ (Node.js) | Python-native, single language stack, simpler ops | 2x lower throughput ceiling, no web UI | Low |
| 3 | API Framework | FastAPI | Node.js/Express | Type safety, auto-docs, 2x throughput, async-native | Smaller ecosystem than Node.js | Very Low |
| 4 | Tenant Isolation | PostgreSQL RLS | Application-level filtering | Database-enforced security, immune to app bugs | 5% query overhead, debugging complexity | Very Low |
| 5 | Proxy Provider | BrightData | Oxylabs/Smartproxy | 99.9% success rate, best anti-detection reputation | 27% cost premium ($12.75 vs $10/GB) | Low |
| 6 | Monitoring | Prometheus + Grafana | CloudWatch only | Portability, 33% cheaper, better visualization | Operational complexity of self-hosting | Low |
| 7 | Migration Strategy | Gradual (5 phases) | Big Bang | Instant rollback, continuous validation, low risk | $1K extra cost, 10-day timeline | Very Low |
| 8 | Authentication | API Keys (bcrypt) | OAuth 2.0 / JWT | Faster MVP, simpler for technical users | No SSO, manual key rotation | Low |
| 9 | Storage | S3 Prefix Isolation | Separate Buckets | Unlimited tenants, standard practice, cost-effective | Requires careful IAM policies | Very Low |
| 10 | Caching | Redis (ElastiCache) | Memcached | Also powers job queue, rate limiting, richer features | Higher memory usage | Very Low |

### 9.2 Deferred Decisions (Re-evaluate at Milestone)

| Decision | Defer Until | Trigger for Re-evaluation |
|----------|-------------|---------------------------|
| Add Scrapy cluster | Month 6 | Volume >1M jobs/month AND >70% static HTML sites |
| OAuth 2.0 / SSO | Month 7 | Enterprise customer requests SSO requirement |
| Multi-region deployment | Month 12 | Latency requirements from non-US customers |
| Migrate to BullMQ | Month 9 | Job throughput exceeds 1000/sec sustained |
| Aurora Serverless | Month 12 | Connection scaling becomes bottleneck |
| Kubernetes (EKS) | Month 18 | Complexity of ECS exceeds benefit |

---

## 10. Appendices

### Appendix A: API Contract Specification

```yaml
openapi: 3.0.3
info:
  title: Scraper Platform API
  version: 2.0.0
  description: Multi-tenant web scraping platform API

paths:
  /v2/scrape:
    post:
      summary: Create scrape job
      security:
        - ApiKeyAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - url
              properties:
                url:
                  type: string
                  format: uri
                formats:
                  type: array
                  items:
                    type: string
                    enum: [markdown, html, screenshot]
                  default: [markdown, html]
                timeout:
                  type: integer
                  minimum: 1000
                  maximum: 300000
                  default: 60000
      responses:
        '200':
          description: Job created
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  id:
                    type: string
                    format: uuid
                  status:
                    type: string
                    enum: [pending, running, completed, failed]
        '401':
          description: Invalid API key
        '402':
          description: Quota exceeded
        '429':
          description: Rate limit exceeded

  /v2/scrape/{id}:
    get:
      summary: Get job status and results
      security:
        - ApiKeyAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Job status
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  status:
                    type: string
                  data:
                    type: object
                    properties:
                      markdown:
                        type: string
                      html:
                        type: string
                      metadata:
                        type: object
        '404':
          description: Job not found

components:
  securitySchemes:
    ApiKeyAuth:
      type: http
      scheme: bearer
      description: API key in format fc_live_xxxxx
```

### Appendix B: Database Schema (Final)

```sql
-- Core tables with multi-tenancy

CREATE TABLE tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'enterprise')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),
    rate_limit_per_hour INTEGER NOT NULL DEFAULT 100,
    monthly_quota INTEGER NOT NULL DEFAULT 10000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT NOT NULL,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    layer_used INTEGER,
    proxy_used BOOLEAN DEFAULT FALSE,
    result JSONB,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    month TEXT NOT NULL,
    scrape_type TEXT NOT NULL,
    layer_used INTEGER,
    proxy_used BOOLEAN DEFAULT FALSE,
    compute_cost_cents INTEGER NOT NULL DEFAULT 0,
    proxy_cost_cents INTEGER NOT NULL DEFAULT 0,
    total_cost_cents INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE usage_summary (
    tenant_id TEXT NOT NULL,
    month TEXT NOT NULL,
    scrapes_total INTEGER NOT NULL DEFAULT 0,
    total_cost_cents INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, month)
);

-- Indexes
CREATE INDEX idx_jobs_tenant_status ON jobs(tenant_id, status);
CREATE INDEX idx_jobs_tenant_created ON jobs(tenant_id, created_at DESC);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash) WHERE revoked_at IS NULL;
CREATE INDEX idx_usage_tenant_month ON usage_records(tenant_id, month);

-- Row-Level Security
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_jobs ON jobs
    FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::text);

CREATE POLICY tenant_isolation_usage ON usage_records
    FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::text);
```

### Appendix C: Environment Variables Reference

```bash
# Application
PORT=8000
HOST=0.0.0.0
ENV=production
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@host:5432/scraper_platform
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:6379/0
REDIS_RATE_LIMIT_URL=redis://host:6379/1

# AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
S3_BUCKET=scraper-platform-data

# Proxies
BRIGHTDATA_USERNAME=xxx
BRIGHTDATA_PASSWORD=xxx
BRIGHTDATA_HOST=brd.superproxy.io
TOR_PROXY_URL=socks5://localhost:9050
FLARESOLVERR_URL=http://localhost:8191

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
PROMETHEUS_PORT=9090

# Feature Flags
ENABLE_RESIDENTIAL_PROXIES=true
ENABLE_FLARESOLVERR=true
MAX_PROXY_BUDGET_DAILY=50
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-03 | Cloud Architecture Team | Initial comprehensive technical architecture document |

---

**Document Status:** Ready for Executive Review
**Classification:** Strategic Planning
**Distribution:** Engineering Leadership, Product Management, Executive Team

---

*This completes Part 2: Technical Architecture & Implementation. Both sections together provide comprehensive decision documentation for executive review.*
