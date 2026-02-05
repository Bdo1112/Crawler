# Iteration Plan Summary: Weeks 1-4

**Document**: `/Users/brianoh/Dev/01_Personal/04_crawler/iteration_1_weeks_1-4.md`

**Status**: ✅ Complete and Ready for Implementation

---

## What's Included

### 1. Strategic Context & Architectural Decisions

**Why Crawlee over Firecrawl?**
- 35-50% cost savings ($965/month vs $1,500-3,000)
- 60% less infrastructure burden (4 services vs 7)
- 20% team maintenance time vs 50%
- Production-proven (used by Apify's $50M+ platform)

**Key Tech Choices**:
- ✅ **FastAPI** (Python-first, async, auto-docs)
- ✅ **arq** (Redis queue, Python-native vs Node.js BullMQ)
- ✅ **PostgreSQL + RLS** (single DB, multi-tenant isolation)
- ✅ **API Keys** (simple auth for MVP, OAuth deferred to Month 7+)
- ✅ **Docker Compose** (reproducible dev + prod deployment)

**Trade-offs Explained**: For every major decision, the plan explains:
- Why this approach?
- What alternatives were considered?
- What are the trade-offs?
- How does this align with team constraints (1-3 people, cost-sensitive)?

### 2. Iteration 1: Weeks 1-2 (Proof of Concept)

**Goal**: Validate Crawlee can replace Firecrawl with ≥90% success rate and ≤2x latency.

**Structure**: 10 days, 4-5 hour tasks, building incrementally.

**Daily Breakdown**:

| Day | Task | Deliverable | Output |
|-----|------|-------------|--------|
| 1 | Environment Setup | Crawlee installed, examples running | `SETUP_NOTES.md` |
| 2 | Layer 1 (HTTP) | Static HTML scraping | `crawlee_layer1.py`, `LAYER1_COMPARISON.md` |
| 3 | Challenge Detection | Bot challenge patterns ported | `challenge_detector.py`, detection results |
| 4 | Layer 2 (Browser) | Playwright scraping with stealth | `crawlee_playwright.py`, anti-detection validation |
| 5 | Benchmark (5 hrs) | Crawlee vs Firecrawl on 20 sites | `benchmark_report.md`, CSV data |
| 6 | 3-Layer Escalation | HTTP → Browser → External | `orchestrator.py`, escalation tests |
| 7 | Proxy Integration | Tor + BrightData support | `proxy_config.py`, performance data |
| 8 | Optimization | Tuning, concurrency, pooling | `optimization_results.md`, >20 URLs/min |
| 9 | Error Handling | Resilient retries, edge cases | `error_handler.py`, 100% crash-free tests |
| 10 | Go/No-Go Decision | Aggregate data, recommendation | `migration_decision.md` |

**Decision Criteria**:
- ✅ Success rate ≥90%
- ✅ Latency ≤2x slower than Firecrawl
- ✅ Code <500 LoC (simpler than scraper.py)
- ✅ Team confidence high

**If Go**: Proceed to Iteration 2 (Weeks 3-4)
**If No-Go**: Document findings, pivot to Firecrawl optimization

### 3. Iteration 2: Weeks 3-4 (API Layer Foundation)

**Goal**: Build production-ready FastAPI with job queue, PostgreSQL, and authentication.

**Structure**: 10 days, working API by end of Week 4.

**Daily Breakdown**:

| Day | Task | Deliverable | Files |
|-----|------|-------------|-------|
| 11 | Project Structure | FastAPI app skeleton | `app/main.py`, `app/config.py` |
| 12 | PostgreSQL Schema | Multi-tenant DB + RLS | `app/database/schema.sql` |
| 13 | API Key Auth | Secure key generation/validation | `app/services/auth.py` |
| 14 | Job Queue (arq) | Job producer/consumer | `workers/crawlee_worker.py` |
| 15 | /v2/scrape Endpoint | Core API working | `app/api/v2/scrape.py` |
| 16 | Rate Limiting | Per-tenant quotas | `app/middleware/rate_limit.py` |
| 17 | Integration Tests | >80% code coverage | `tests/test_api/*.py` |
| 18 | Docker Setup | Full stack deployment | `docker/docker-compose.yaml` |
| 19 | Documentation | API guide + examples | `docs/API_GUIDE.md` |
| 20 | Demo & Retro | Record demo, write learnings | Demo video, `ITERATION_RETRO.md` |

**Output by End of Week 4**:
- ✅ Working API: POST /v2/scrape, GET /v2/scrape/{id}
- ✅ Multi-tenant: 3+ test tenants, RLS enforced
- ✅ Job queue: Async processing, <30s P95 latency
- ✅ Tests: >80% coverage, zero crashes
- ✅ Deployment: `docker compose up` runs everything
- ✅ Documentation: OpenAPI docs, usage guide, examples

---

## Key Features of This Plan

### 1. Extremely Detailed Day-by-Day Breakdown

Each day includes:
- **Objective** (what to achieve)
- **Time Estimate** (realistic hours)
- **Prerequisites** (what you need first)
- **Numbered Tasks** (exact steps)
- **Code Examples** (copy-paste ready)
- **Acceptance Criteria** (how to verify completion)
- **Common Issues & Solutions** (troubleshooting)
- **Output Files** (what gets created)
- **Risk & Mitigation** (what could go wrong)

### 2. Copy-Paste Ready Code

Code examples are production-quality, not pseudocode:
- Full FastAPI endpoints with validation
- SQLAlchemy ORM models with RLS
- Pytest fixtures and test cases
- Docker configurations
- All with realistic imports and error handling

### 3. Architecture Decisions Explained

For every major choice, you get:
- **Decision**: What we chose
- **Alternative**: What we considered
- **Rationale**: Why this is best
- **Trade-offs**: What we gave up
- **Contingency**: What if it doesn't work

Examples:
- Why arq instead of BullMQ? (Python-native, simpler ops)
- Why FastAPI instead of Node.js? (Team skill, auto-docs, type safety)
- Why API keys instead of OAuth? (Speed to market, defer to Month 7+)

### 4. Realistic Success Metrics

Not theoretical targets—actual measurable criteria:
- **Success rate**: ≥90% (not "should work")
- **Latency**: ≤2x Firecrawl (quantified trade-off)
- **Code complexity**: <500 LoC (vs 15,000 for Firecrawl)
- **Memory**: <300MB per browser (testable)
- **Throughput**: >20 URLs/min (benchmarked)

### 5. Risk Assessment & Contingencies

For each major risk:
- **Likelihood**: Low/Medium/High
- **Impact**: High/Medium/Low
- **Mitigation**: How to prevent
- **Contingency**: What if it happens anyway

Examples:
- Playwright memory leaks → Monitor usage, tune pool size
- arq insufficient features → Migrate to BullMQ Month 6+
- Team lacks bandwidth → Hire contractor for Weeks 5-6

---

## How to Use This Plan

### Week 1 (Iteration 1 Part 1)

**Monday (Day 1)**: 3-4 hours
```bash
# Follow SETUP_NOTES section
python3.11 -m venv venv
source venv/bin/activate
pip install 'crawlee[playwright]'
python examples/basic_crawler.py
```

**Tuesday (Day 2)**: 4-5 hours
```bash
# Implement crawlee_layer1.py (copy from plan)
python crawlee_layer1.py
# Compare with scraper.py
```

Continue through Day 10 (Friday Week 2 - Go/No-Go decision).

### Week 3 (Iteration 2 Part 1)

**Monday (Day 11)**: 4-5 hours
```bash
# Create project structure
mkdir -p /Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/api
# Follow main.py, config.py from plan
# Start FastAPI with `uvicorn app.main:app --reload`
```

Continue through Week 4 (Day 20 - Demo & Retrospective).

---

## Success Criteria Checklist

### By End of Week 2 (Iteration 1):

- [ ] Crawlee PoC achieves ≥90% success rate
- [ ] Latency acceptable (≤2x Firecrawl)
- [ ] Code <500 LoC (cleaner than scraper.py)
- [ ] Team confident in migration
- [ ] Go/No-Go decision documented
- **Decision**: Go → Proceed to Week 3

### By End of Week 4 (Iteration 2):

- [ ] FastAPI running on http://localhost:8000
- [ ] POST /v2/scrape returns job_id
- [ ] GET /v2/scrape/{id} returns results
- [ ] Authentication working (API keys)
- [ ] Jobs processed by arq worker
- [ ] PostgreSQL storing results
- [ ] Rate limiting enforced
- [ ] >80% test coverage
- [ ] Docker Compose deployment working
- [ ] OpenAPI docs at http://localhost:8000/docs
- **Demo**: Record 5-7 min demo, show full flow

---

## What's NOT in Weeks 1-4

### Deferred Features (Why & When):

| Feature | Why Deferred | When |
|---------|-------------|------|
| OAuth/JWT | API keys sufficient for MVP | Month 7+ |
| Scrapy | No high-volume need yet | Month 6+ (if >1M req/month) |
| Dashboard UI | API-first, Postman enough | Month 3+ |
| FlareSolverr | Only 5-10% sites need | Week 7-8 |
| BrightData Proxies | Free tier not needed yet | Month 2+ (paying customers) |
| Webhooks | Polling sufficient | Month 5+ |
| Bulk Upload | Single URL validation enough | Month 4+ |

---

## File Locations

**Main Plan Document**:
```
/Users/brianoh/Dev/01_Personal/04_crawler/iteration_1_weeks_1-4.md
```

**Code Output Locations**:

**Iteration 1 PoC** (`/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/`):
- `SETUP_NOTES.md` (Day 1)
- `crawlee_layer1.py` (Day 2)
- `challenge_detector.py` (Day 3)
- `crawlee_playwright.py` (Day 4)
- `benchmark_report.md` (Day 5)
- `orchestrator.py` (Day 6)
- `proxy_config.py` (Day 7)
- `migration_decision.md` (Day 10)

**Iteration 2 API** (`/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/api/`):
- `app/main.py` (Day 11)
- `app/database/schema.sql` (Day 12)
- `app/services/auth.py` (Day 13)
- `workers/crawlee_worker.py` (Day 14)
- `app/api/v2/scrape.py` (Day 15)
- `docker/docker-compose.yaml` (Day 18)
- `docs/API_GUIDE.md` (Day 19)

---

## Implementation Tips

### 1. Copy-Paste Code with Confidence
- All code examples are production-ready
- They include error handling, logging, type hints
- Adapt as needed, but don't skip the safety features

### 2. Follow the Day-by-Day Flow
- Don't skip ahead or combine days
- Each day builds on previous ones
- Integration tests in Day 17 catch early mistakes

### 3. Use the Acceptance Criteria
- Don't move to next day until all criteria pass
- Criteria are specific and measurable
- They define "done"

### 4. Document Issues as You Go
- Create a log file of problems + solutions
- Share with team weekly
- Informs future iterations

### 5. Commit to Git Frequently
- Commit at end of each day
- Makes it easy to revert if something breaks
- Enables parallel work in future

---

## Next Steps

1. **Read the full plan** (`iteration_1_weeks_1-4.md`)
2. **Gather team**: Review Week 1 approach, agree on timeline
3. **Set up environment** (Day 1 Monday): Create venv, install Crawlee
4. **Execute Week 1** (Mon-Fri): Complete PoC in 10 days
5. **Make Go/No-Go decision** (Friday Week 2): Based on real data
6. **Execute Week 3-4** (if Go): Build API layer
7. **Demo & decide next iteration** (Friday Week 4)

---

## Contact & Updates

- **Plan Version**: 1.0 (Feb 2, 2026)
- **Last Updated**: When each iteration completes
- **Owner**: Technical Product Manager #1
- **Next Review**: After Week 2 (Go/No-Go decision)

---

## Success Definition

By end of Week 4, if you can:

1. ✅ Run `docker compose up` and see all services start
2. ✅ Call `curl -X POST http://localhost:8000/v2/scrape -H "X-API-Key: sk-live-..." -d '{"url":"https://example.com"}'` and get a job ID
3. ✅ Poll the job status endpoint and see results
4. ✅ Access OpenAPI docs at http://localhost:8000/docs
5. ✅ Run pytest and see >80% code coverage
6. ✅ Record a 5-minute demo showing the entire flow

**Then you're ready for Weeks 5-6 (multi-tenancy, storage, analytics).**

---

Good luck! The plan is detailed enough that a junior developer can execute independently. The key is following the day-by-day structure and not skipping acceptance criteria.
