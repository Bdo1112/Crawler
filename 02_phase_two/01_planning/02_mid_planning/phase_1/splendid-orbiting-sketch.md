# Strategic Plan: Multi-Tenant Web Scraping Platform Engine Selection

## Executive Summary

After comprehensive product and architecture analysis, the recommendation is clear:

**Migrate from Firecrawl to Crawlee-based architecture**

### Key Decision
- **Primary Engine:** Crawlee (Python)
- **Optional Addition:** Scrapy (for high-volume static HTML, add after Month 6)
- **Migration Timeline:** 8-12 weeks
- **Team Viability:** 1-3 developers can build and maintain

### Why Not Continue with Firecrawl?
1. **Operational Complexity:** 7 Docker services requiring 18GB RAM minimum
2. **Production Readiness:** Self-hosted version is "not production-ready yet" (per comparison document)
3. **Team Burden:** Requires 2-3 DevOps engineers; unsustainable for 1-3 person team
4. **Cost at Scale:** 2-3x higher infrastructure costs than Crawlee at 100K+ jobs/day
5. **Maintenance:** ~50% of team time vs ~20% for Crawlee

---

## Combined Product + Architecture Analysis Summary

### Product-Market Fit (Product Manager Analysis)

**Crawlee Advantages:**
- **Time to Market:** 3-4 months to revenue-generating MVP (vs 6-9 months for Scrapy-first)
- **Product Positioning:** "Open-source Apify alternative with transparent pricing"
- **Developer Experience:** Built by Apify, proven by their $50M+ ARR platform
- **Cost Model:** 4-6x margin on scrape jobs ($2.60-$6.10 cost → $20-30 price)
- **Differentiation:** Instant engine switching (HTTP → Browser), Python + Node.js support

**Business Metrics:**
- Phase 1 (Months 1-6): Internal data collection - **ACHIEVABLE**
- Phase 2 (Months 7-12): Multi-tenant platform MVP - **AGGRESSIVE BUT POSSIBLE**
- Phase 3 (Months 13+): AI/LLM pipeline features - **ACHIEVABLE** (incremental)

**Risk Assessment:**
- Technical Debt: **LOW-MEDIUM** (~2-3 months/year payback)
- Community Risk: **LOW** (Apify-backed, active development)
- Vendor Lock-in: **MEDIUM-HIGH** (Apify controls roadmap, but engine abstraction allows migration)

### Architecture Viability (Cloud Architect Analysis)

**Infrastructure Comparison:**

| Metric | Crawlee | Firecrawl (Current) | Scrapy-First |
|--------|---------|---------------------|--------------|
| Services | 4 | 7 | 5 |
| RAM Required | 12GB | 18GB | 10GB |
| Monthly Cost (300K jobs) | $925 | $1,500-3,000 | $900 |
| Team Burden | 1-2 people | 2-3 people | 1-2 people (need expert) |
| Maintenance Time | 20% | 50% | 30% |

**Scalability:**
- Crawlee: 500 jobs/hour → 50K+ jobs/hour with auto-scaling
- Vertical: 2 CPU, 4GB RAM → 50-100 req/s (HTTP) or 10-20 browsers
- Horizontal: Add stateless workers behind BullMQ queue

**Cost Efficiency:**
- Crawlee HTTP: $0.003/scrape (0.3 cents)
- Scrapy: $0.0009/scrape (0.09 cents) - for static HTML only
- Firecrawl: $0.005+/scrape (0.5 cents) at scale

### What Can Be Salvaged (60% of Current Work)

**Keep & Port to Crawlee:**
- ✅ 3-layer escalation logic (scraper.py) → Crawlee router
- ✅ Challenge detection patterns (CHALLENGE_PATTERNS)
- ✅ Site profiles (SITE_PROFILES) → Database-driven config
- ✅ Tor integration → Crawlee ProxyConfiguration
- ✅ FlareSolverr integration → Separate microservice
- ✅ Database schema concepts

**Discard:**
- ❌ Firecrawl monorepo (apps/api, apps/playwright-service-ts)
- ❌ Complex TypeScript stack
- ❌ RabbitMQ (replace with simpler BullMQ)
- ❌ Patchright service (Crawlee bundles Playwright)

---

## Recommended Architecture

### Core Stack

```
┌─────────────────────────────────────────────────────────────┐
│                 API Gateway (FastAPI + Python)               │
│  - Authentication (API keys, OAuth)                          │
│  - Rate limiting (per-tenant quotas)                         │
│  - Request routing & intelligent engine selection            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Job Queue (BullMQ on Redis)                     │
│  - Priority queues (tenant tier-based)                       │
│  - Job isolation (tenant_id namespace)                       │
│  - Auto-scaling triggers                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
┌───────▼──────┐            ┌────────▼────────┐
│ Crawlee Pool │            │ Scrapy Cluster  │
│ (Primary)    │            │ (Optional)      │
│              │            │                 │
│ - HTTP mode  │            │ - Add Month 6+  │
│ - Playwright │            │ - Static HTML   │
│ - Mixed      │            │ - High volume   │
│              │            │                 │
│ Features:    │            │ Performance:    │
│ - Proxy rot. │            │ - 500 req/s     │
│ - Anti-det.  │            │ - Cost-optimal  │
│ - Session mgmt│            │                 │
└───────┬──────┘            └────────┬────────┘
        │                            │
        └────────────┬───────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│        Anti-Detection Layer (Selective, On-Demand)            │
│  - curl_cffi (Layer 1: TLS fingerprinting)                   │
│  - BrightData proxies (Layer 4: Premium tier only)           │
│  - FlareSolverr (Layer 5: Cloudflare challenges)             │
└──────────────────────────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│              Storage & Processing                             │
│  - PostgreSQL (job metadata, tenants, RLS)                   │
│  - S3/Minio (scraped content, multi-tenant buckets)          │
│  - Redis (cache, session state, rate limits)                 │
│  - Vector DB (Phase 3: LLM/RAG pipeline)                     │
└──────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Core Services:**
- FastAPI (Python) - API gateway
- Crawlee (Python) - Primary scraping engine
- BullMQ (Redis) - Job queue
- PostgreSQL 16 - Metadata & multi-tenancy
- Redis - Cache, queue, rate limiting
- S3 - Scraped content storage

**Optional Services:**
- Scrapy - Fast-path for static HTML (add Month 6+)
- FlareSolverr - Cloudflare challenge solver (on-demand)
- Tor Proxy - Development/testing (not production)

**Production Deployment:**
- AWS ECS Fargate - Auto-scaling containers
- ElastiCache Redis - Managed Redis
- RDS PostgreSQL - Managed database
- S3 - Object storage with lifecycle policies
- CloudWatch - Monitoring & logging

---

## Migration Roadmap (12 Weeks)

### Phase 1: Foundation & Validation (Weeks 1-2)

**Proof of Concept:**
- Set up Crawlee (Python) environment
- Implement 3-layer escalation (HTTP → Playwright → Proxy)
- Port 3-5 patterns from scraper.py
- Test against 20 representative sites
- Performance benchmark vs current Firecrawl

**Decision Gate:**
- Compare: Success rate, performance, complexity
- If <90% success rate OR >2x slower: Reconsider
- If passes: Continue to Phase 2

**Critical Files:**
- `poc/crawlee_test.py` - Crawlee implementation
- `poc/benchmark_results.md` - Performance comparison
- `poc/migration_decision.md` - Go/no-go recommendation

### Phase 2: API Layer (Weeks 3-4)

**Build:**
- FastAPI application skeleton
- Authentication (API keys, JWT)
- POST /v2/scrape endpoint (Firecrawl-compatible)
- BullMQ job queue integration
- PostgreSQL job storage

**Deliverables:**
- Working API accepting scrape requests
- Job queue processing with Crawlee
- Basic tenant management
- API documentation (OpenAPI/Swagger)

**Critical Files:**
- `api/main.py` - FastAPI app
- `api/routes/v2.py` - V2 endpoints
- `api/auth.py` - Authentication
- `workers/crawlee_worker.py` - Job processor
- `database/schema.sql` - PostgreSQL schema

### Phase 3: Multi-Tenancy (Weeks 5-6)

**Build:**
- Tenant schema with Row-Level Security (RLS)
- Rate limiting (Redis-based sliding window)
- Quota management & billing tracking
- S3 integration with tenant-isolated buckets
- Usage analytics

**Deliverables:**
- Multiple tenants can use platform simultaneously
- Per-tenant quotas enforced
- Usage tracking for billing
- Isolated data storage

**Critical Files:**
- `database/tenants.sql` - Tenant schema
- `api/middleware/rate_limit.py` - Rate limiting
- `api/services/quota.py` - Quota management
- `api/services/storage.py` - S3 integration
- `database/analytics.sql` - Usage tracking

### Phase 4: Anti-Detection (Weeks 7-8)

**Build:**
- curl_cffi integration (Layer 1 TLS fingerprinting)
- BrightData proxy integration (optional, premium tier)
- FlareSolverr integration (on-demand microservice)
- Challenge detection logic (port from scraper.py)
- Intelligent router (auto-select engine based on URL)

**Deliverables:**
- Multi-layer anti-detection working
- Automatic escalation on detection
- Proxy rotation for premium tiers
- FlareSolverr fallback for Cloudflare

**Critical Files:**
- `workers/layers/curl_cffi_layer.py` - Layer 1
- `workers/layers/crawlee_layer.py` - Layer 2-3
- `workers/layers/flaresolverr.py` - Layer 5
- `api/services/router.py` - Intelligent routing
- `config/site_profiles.json` - Site-specific configs

### Phase 5: Production Hardening (Weeks 9-10)

**Build:**
- Monitoring (Prometheus metrics + Grafana dashboards)
- Logging (structured JSON → CloudWatch)
- Error tracking (Sentry integration)
- Load testing (Locust, target: 1000 req/min)
- Documentation (deployment, runbooks)

**Deliverables:**
- Production-ready monitoring
- Alerting on critical metrics
- Load-tested to target volume
- Operational runbooks

**Critical Files:**
- `monitoring/prometheus.yml` - Metrics config
- `monitoring/grafana_dashboards/` - Dashboards
- `monitoring/alerts.yml` - Alert rules
- `tests/load/locustfile.py` - Load tests
- `docs/runbook.md` - Operations guide

### Phase 6: Migration & Launch (Weeks 11-12)

**Execute:**
- Deploy Crawlee platform to staging
- Parallel run: 20% traffic to Crawlee, 80% to Firecrawl
- Validate metrics: success rate, latency, cost
- Gradual traffic shift: 50%, 80%, 100%
- Decommission Firecrawl stack

**Rollback Plan:**
- Keep Firecrawl running for 2 weeks post-cutover
- DNS/load balancer allows instant rollback
- Data migration is incremental (no big bang)

**Critical Files:**
- `deployment/ecs_taskdef.json` - ECS configuration
- `deployment/terraform/` - Infrastructure as code
- `scripts/migrate_data.py` - Data migration
- `docs/cutover_plan.md` - Step-by-step guide

---

## Decision Framework: When to Add Scrapy

**Add Scrapy if:**
1. You have >70% static HTML sites (no JS required)
2. Volume exceeds 1M requests/month
3. You have a Scrapy expert on the team
4. Cost optimization is critical (need 3x cost reduction)

**When to add:** Month 6+ (after Crawlee platform is stable)

**How to add:**
- Implement intelligent router: Check if JS required → Crawlee, else → Scrapy
- Deploy Scrapy worker pool alongside Crawlee
- Use same BullMQ queue with different worker types
- **Effort:** 4-6 weeks, 1-2 developers

**Don't add if:**
- <50% static HTML
- Team has no Scrapy experience
- Volume <500K requests/month
- Crawlee performance is sufficient

---

## Cost Projection

### Monthly Infrastructure Cost (300K jobs/month)

**Crawlee Architecture:**
```
Compute (ECS Fargate):
- API: 2 tasks × 1vCPU, 2GB               $58
- Crawlee workers: 5 tasks × 2vCPU, 4GB   $292
- Scrapy workers (optional): 0 initially  $0

Data Services:
- ElastiCache Redis (cache.t3.medium)     $70
- RDS PostgreSQL (db.t3.medium)           $70
- S3 storage: 1TB                         $23
- S3 requests                             $5

Network:
- Data transfer: 500GB                    $45

Anti-Detection (selective use):
- Residential proxies (20% of requests)   $382
- FlareSolverr (on-demand)               $20

TOTAL: ~$965/month
```

**Scaling Projections:**
- 1M jobs/month: ~$1,500/month
- 10M jobs/month: ~$5,000/month (with auto-scaling)

**Firecrawl (Current) Comparison:**
- 300K jobs/month: ~$1,500-3,000
- 1M jobs/month: ~$5,000+
- **Savings: 35-50% with Crawlee**

---

## Success Metrics

### Phase 1 (Months 1-6): Internal Data Collection

**Technical Metrics:**
- Scrape success rate > 90%
- P99 latency < 30s (browser mode)
- Infrastructure cost < $5/1k scrapes
- Zero downtime deployments

**Business Metrics:**
- Build 3+ internal scrapers on platform
- Validate cost model
- Document learnings

### Phase 2 (Months 7-12): Multi-Tenant Platform MVP

**Technical Metrics:**
- 99.9% uptime
- <5% error rate
- Handle 10K+ jobs/day
- Auto-scaling functional

**Business Metrics:**
- 50+ paying customers
- $5K+ MRR (Monthly Recurring Revenue)
- Churn < 5%/month
- NPS > 40

### Phase 3 (Months 13-18): Growth + AI Features

**Technical Metrics:**
- Handle 100K+ jobs/day
- LLM extraction available
- Vector search operational

**Business Metrics:**
- 200+ paying customers
- $30K+ MRR
- Gross margin > 70%
- Product-market fit validated (retention > 60%)

---

## Risk Mitigation

### Risk 1: Crawlee Migration Fails (Success Rate <90%)

**Mitigation:**
- Week 1-2 proof of concept validates viability
- Parallel run with Firecrawl for 2 weeks
- Instant rollback capability via load balancer
- Keep Firecrawl stack until Crawlee proven

**Contingency:** Optimize Firecrawl instead (reduce services, add multi-tenancy)

### Risk 2: Team Lacks Bandwidth (1-3 developers insufficient)

**Mitigation:**
- Phased rollout spreads work over 12 weeks
- MVP focuses on core features only
- Scrapy deferred to Month 6+ (optional)
- Managed services reduce ops burden (RDS, ElastiCache)

**Contingency:** Extend timeline to 16 weeks, hire contractor for Phases 4-5

### Risk 3: Apify Kills Crawlee Open-Source

**Mitigation:**
- Engine abstraction layer (can swap to raw Playwright)
- Monitor Apify licensing changes
- Maintain fork if needed
- **Historical precedent:** Apify has been open-source friendly for 8+ years

**Contingency:** Migrate to Playwright + custom queue layer (6-9 months effort)

### Risk 4: Cost Overruns (>$2K/month before revenue)

**Mitigation:**
- Start with small ECS tasks, scale on-demand
- Use free tier where possible (S3, CloudWatch)
- Defer residential proxies until paying customers
- Monitor costs weekly

**Contingency:** Use EC2 instances instead of Fargate (40% cheaper, more ops)

---

## Critical Files to Modify/Create

### New Files (Crawlee Platform)

**Core Application:**
- `api/main.py` - FastAPI app entry point
- `api/routes/v2.py` - V2 API endpoints (Firecrawl-compatible)
- `api/auth.py` - Authentication & authorization
- `api/middleware/rate_limit.py` - Rate limiting
- `workers/crawlee_worker.py` - Crawlee job processor
- `workers/scrapy_worker.py` - Scrapy worker (optional, Phase 2)

**Anti-Detection:**
- `workers/layers/curl_cffi_layer.py` - Layer 1 (TLS fingerprinting)
- `workers/layers/crawlee_layer.py` - Layer 2-3 (HTTP + Playwright)
- `workers/layers/flaresolverr.py` - Layer 5 (Cloudflare solver)
- `api/services/router.py` - Intelligent engine selection

**Database:**
- `database/schema.sql` - PostgreSQL schema (tenants, jobs)
- `database/migrations/` - Schema migrations
- `config/site_profiles.json` - Site-specific configurations

**Infrastructure:**
- `docker-compose.yml` - Local development stack
- `deployment/ecs_taskdef.json` - ECS task definitions
- `deployment/terraform/` - Infrastructure as code
- `monitoring/prometheus.yml` - Metrics configuration
- `monitoring/grafana_dashboards/` - Grafana dashboards

### Files to Port from Current Firecrawl

**Salvage & Adapt:**
- `01_phase_one/scripts/scraper.py` → `workers/router.py`
  - 3-layer escalation logic
  - Challenge detection patterns
  - Site profiles (SITE_PROFILES)

- `01_phase_one/firecrawler/firecrawl/docker-compose.yaml` → `docker-compose.yml`
  - Simplify from 7 services to 4
  - Remove RabbitMQ, Patchright service
  - Keep Tor (optional), FlareSolverr (on-demand)

---

## Verification & Testing

### End-to-End Testing

**Scenario 1: Simple Scrape (HTTP Mode)**
1. Send POST /v2/scrape with static HTML URL
2. Verify: Job queued in BullMQ
3. Verify: Crawlee worker processes job (HTTP mode)
4. Verify: Result stored in S3
5. Verify: Job marked complete in PostgreSQL
6. Expected time: <5 seconds

**Scenario 2: JavaScript-Heavy Site (Playwright Mode)**
1. Send POST /v2/scrape with JS-heavy URL
2. Verify: Router selects Playwright engine
3. Verify: Browser launches, page renders
4. Verify: Content extracted correctly
5. Expected time: 5-15 seconds

**Scenario 3: Protected Site (Anti-Detection)**
1. Send POST /v2/scrape with Cloudflare-protected URL
2. Verify: Layer 1 fails (curl_cffi)
3. Verify: Layer 3 escalation (Playwright + proxy)
4. Verify: If fails, Layer 5 (FlareSolverr)
5. Verify: Challenge bypassed, content extracted
6. Expected time: 10-30 seconds

**Scenario 4: Multi-Tenant Isolation**
1. Create 2 tenants with different API keys
2. Send scrape requests from both tenants
3. Verify: Jobs isolated in separate queue namespaces
4. Verify: Results stored in separate S3 prefixes
5. Verify: Tenant A cannot access Tenant B's data

**Scenario 5: Rate Limiting**
1. Send 101 requests in 1 second (free tier limit: 100/hour)
2. Verify: Requests 1-100 succeed
3. Verify: Request 101 returns 429 Too Many Requests
4. Verify: Rate limit resets after 1 hour

### Performance Testing

**Load Test (Locust):**
```python
# Target: 1000 concurrent scrapes
locust -f tests/load/locustfile.py --users 1000 --spawn-rate 10
```

**Expected Results:**
- 90th percentile latency: <10s (HTTP mode)
- 99th percentile latency: <30s (Playwright mode)
- Error rate: <5%
- Throughput: 50-100 req/s

### Monitoring Validation

**Metrics to Track:**
- `scrape_jobs_total{status="success"}` - Should be >90%
- `scrape_duration_seconds{p99}` - Should be <30s
- `queue_depth` - Should stay <1000
- `worker_cpu_usage` - Should stay <80%

**Alerts to Test:**
- Queue depth > 1000 for 5 minutes → Alert fires
- Worker crash rate > 10% → Alert fires
- Tenant quota at 80% → Notification sent

---

## Next Steps (Week 1)

### Immediate Actions

1. **Day 1-2: Environment Setup**
   - Clone Crawlee examples repository
   - Set up Python 3.11+ environment
   - Install dependencies: `pip install crawlee[playwright]`
   - Run basic Crawlee example

2. **Day 3-4: Port One Pattern**
   - Choose simplest pattern from `scripts/scraper.py`
   - Implement in Crawlee (HTTP mode)
   - Test against 5 sites
   - Document results

3. **Day 5: Performance Benchmark**
   - Run same 5 sites with current Firecrawl
   - Compare: success rate, latency, resource usage
   - Document in `poc/benchmark_results.md`

4. **Day 6-7: Decision**
   - Review benchmark results
   - Go/no-go decision on migration
   - If go: Begin Phase 2 (API Layer)
   - If no-go: Document why, pivot to Firecrawl optimization

### Questions to Answer (Week 1)

**Critical for Architecture Refinement:**
1. What % of target sites are JS-heavy vs static HTML?
   - If >70% static: Consider adding Scrapy from start
   - If <30% static: Crawlee-only is optimal

2. What % of sites require anti-detection (proxies, challenges)?
   - If >50%: Budget for residential proxies from Month 1
   - If <20%: Defer proxies to paying customers

3. What's the monthly scraping volume target for Year 1?
   - <100K jobs/month: Single EC2 instance sufficient
   - 100K-1M: ECS Fargate auto-scaling needed
   - >1M: Multi-region, advanced scaling required

4. Do you have Scrapy expertise on the team?
   - Yes: Consider Scrapy from Phase 2
   - No: Stick with Crawlee-only

**Answer these and the plan can be further refined.**

---

## Recommendation Summary

### Do This

1. ✅ **Weeks 1-2:** Build Crawlee proof of concept, validate performance
2. ✅ **Weeks 3-12:** Follow migration roadmap if PoC succeeds
3. ✅ **Month 6+:** Add Scrapy if volume justifies (>1M req/month, >70% static HTML)
4. ✅ **Month 13+:** Add AI/LLM features (Crawl4AI or OpenAI SDK)

### Don't Do This

1. ❌ **Continue with Firecrawl** - Too complex for 1-3 person team, not production-ready
2. ❌ **Build hybrid from Day 1** - Delays MVP by 6+ months, too much complexity
3. ❌ **Go AI-first** (ScrapeGraphAI) - Unproven market, high LLM costs, small community
4. ❌ **Build everything custom** - Use Crawlee's abstractions, don't reinvent

### Key Success Factors

- **Start small:** PoC in Week 1, not full build
- **Validate early:** Performance benchmark before committing
- **Stay focused:** MVP features only, defer nice-to-haves
- **Leverage managed services:** RDS, ElastiCache, S3 reduce ops burden
- **Keep Firecrawl:** Parallel run for 2 weeks, instant rollback

---

## Conclusion

Both product management and architecture analyses converge on the same recommendation: **Crawlee is the right engine for a multi-tenant scraping platform built by a 1-3 person team.**

The migration is viable (8-12 weeks), cost-effective ($900/month vs $1,500+), and maintainable (20% team time vs 50%). Your current Firecrawl investment is 60% salvageable (escalation logic, anti-detection patterns, site profiles).

**Proceed with Week 1 proof of concept to validate before full commitment.**

---

## Mid-Planning Phase: Executive Decision Document

### Objective
Create a comprehensive `mid_planning_1.md` document for final decision makers (CEO, CTO, investors) that synthesizes all planning work and documents WHY each major decision was made through collaborative analysis by product design and architecture specialists.

### Approach

**Two-Agent Collaboration:**
1. **Product Designer Agent**: Analyzes from user/market/business perspective
2. **Cloud Architect Agent**: Analyzes from technical/infrastructure/cost perspective

**Document Structure:**

**Part 1: Product Design & Strategy** (20-30 pages by Product Designer)
- Executive summary with business case
- Product vision & market positioning
- User personas & jobs-to-be-done
- MVP feature set with prioritization rationale
- Monetization strategy & unit economics
- UX/UI decisions with trade-off analysis
- Product metrics & success criteria
- Product risks & mitigation strategies
- Decision log: WHY each product choice was made

**Part 2: Technical Architecture & Implementation** (20-30 pages by Cloud Architect)
- Architecture overview with system diagrams
- Technology stack decisions (detailed comparison matrices)
- Scalability & performance analysis
- Security & compliance strategy
- Infrastructure cost analysis (dev + ops)
- Migration strategy with rollback plan
- Technical risks & mitigation strategies
- Operational readiness (monitoring, SLAs, incident response)
- Decision log: WHY each technical choice was made

### Decision Documentation Format

For EVERY major decision (Crawlee vs Firecrawl, API-first, arq vs BullMQ, etc.):

```markdown
### Decision: [Technology/Product Choice]

**What We Chose:** [Brief description]

**Alternatives Considered:**
| Option | Pros | Cons | Cost | Verdict |
|--------|------|------|------|---------|
| Option A | ... | ... | $ | ✅ Chosen |
| Option B | ... | ... | $$ | ❌ Rejected |

**Product Perspective (Designer):**
[Why this enables product goals]

**Technical Perspective (Architect):**
[Why this is technically sound]

**Trade-offs:**
[What we're giving up]

**Why Acceptable:**
[Business/user justification]

**Risk Mitigation:**
[How we handle downsides]
```

### Key Decisions to Document

1. **Crawlee over Firecrawl**
   - Product: Time-to-market (4 months vs 6-9), simpler UX
   - Architect: 35-50% cost savings, 60% less infrastructure
   - Trade-off: 1.5x slower, acceptable for reliability over speed

2. **arq over BullMQ**
   - Product: Python-native matches developer persona
   - Architect: Single language stack, simpler ops
   - Trade-off: Lower throughput ceiling, sufficient for MVP

3. **API-First over Dashboard-First**
   - Product: Developer users prefer APIs, faster MVP
   - Architect: 4 weeks faster build time
   - Trade-off: Less accessible to non-technical, acceptable for target persona

4. **PostgreSQL RLS over App-Level Filtering**
   - Product: Security foundation enables SaaS business model
   - Architect: Database-enforced, immune to app bugs
   - Trade-off: 5% query slowdown, acceptable for security

5. **BrightData over Oxylabs/Smartproxy**
   - Product: 99.9% success rate = better UX
   - Architect: Proven anti-detection, reasonable cost
   - Trade-off: $12.75/GB vs $10/GB, acceptable for quality

6. **Gradual Migration over Big Bang**
   - Product: Risk mitigation = customer confidence
   - Architect: Instant rollback, continuous validation
   - Trade-off: $1K extra cost, acceptable for safety

### Output Files

**Primary Document:**
`/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/01_planning/02_mid_planning/mid_planning_1.md`

**Supporting Documents:**
- Product section analysis (if separate)
- Architecture section analysis (if separate)

### Tone & Style

**Executive-Friendly:**
- Clear summaries at each section
- Tables and diagrams for scanability
- Honest about trade-offs
- Quantified metrics (not "fast" but "35% cost savings")

**Technically Rigorous:**
- Detailed comparison matrices
- Cost projections with assumptions
- Risk analysis with probability/impact
- Mitigation strategies for each risk

**Decision-Focused:**
- Every section answers: "Why this choice?"
- Alternatives always documented
- Trade-offs explicitly stated
- Business case clearly articulated

### Review Criteria

Document succeeds when decision makers can:
1. ✅ Understand why migration is necessary
2. ✅ See clear business case (cost, time, risk)
3. ✅ Know target users and their needs
4. ✅ Approve MVP scope with confidence
5. ✅ Understand all major trade-offs
6. ✅ Make informed go/no-go decision

### Next Steps

1. Product Designer agent creates Part 1 (product design & strategy)
2. Cloud Architect agent creates Part 2 (technical architecture)
3. Both agents collaborate on decision log sections
4. Synthesis into single comprehensive document
5. Final review and approval gate

**Timeline:** 1-2 days for document creation
**Approval Gate:** Executive review before Week 1 PoC begins
