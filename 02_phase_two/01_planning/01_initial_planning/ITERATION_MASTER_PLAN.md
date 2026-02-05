# Master Plan: Complete 12-Week Crawlee Migration

**Project:** Multi-Tenant Web Scraping Platform (Crawlee Migration)
**Timeline:** 12 weeks (3 iterations, 2 weeks each + buffer)
**Team Size:** 1-3 developers
**Status:** Ready for Execution
**Date:** 2026-02-02

---

## 🎯 Overview: What We're Building

### Vision
Transform from a complex, self-hosted Firecrawl setup (7 services, 18GB RAM, 50% team maintenance) to a lean, scalable Crawlee-based platform (4 services, 12GB RAM, 20% team maintenance) that can be monetized as a multi-tenant SaaS offering.

### Business Goals
- **Phase 1 (Months 1-6):** Internal data collection infrastructure
- **Phase 2 (Months 7-12):** Multi-tenant platform MVP with 50+ paying customers
- **Phase 3 (Months 13+):** Growth + AI/LLM features

### Technical Goals
- **Month 4:** Revenue-generating MVP
- **Month 12:** $5K+ MRR, 50+ customers
- **Month 18:** $30K+ MRR, 200+ customers

---

## 📋 Complete Timeline: 12 Weeks

```
Week  1-2:  ITERATION 1: Foundation & Validation (Proof of Concept)
       ↓
Week  3-4:  ITERATION 2: API Layer (REST API + Job Queue)
       ↓
Week  5-6:  ITERATION 3: Multi-Tenancy (Tenant Isolation + RLS)
       ↓
Week  7-8:  ITERATION 4: Anti-Detection (Layers 1-5)
       ↓
Week  9-10: ITERATION 5: Production Hardening (Monitoring + Load Testing)
       ↓
Week  11-12: ITERATION 6: Migration & Launch (Parallel Run + Cutover)
```

---

## 📊 Iteration 1: Weeks 1-2 (Foundation & Validation)

**Detailed Plan:** See `iteration_1_weeks_1-4.md` (Part 1)

### Objective
Validate that Crawlee can replace Firecrawl with ≥90% success rate before committing to full platform.

### Key Deliverables

| Day | Task | Output | Success Criteria |
|-----|------|--------|------------------|
| 1-2 | Crawlee Setup | `setup_notes.md`, environment ready | Install successful, examples run |
| 3-4 | Layer 1 HTTP | `curl_cffi_layer.py` | 60%+ success rate, <100ms latency |
| 5-6 | Layer 2 Browser | `crawlee_browser.py` | 85%+ JS detection, <5s latency |
| 7-8 | Challenge Detection | `challenge_detector.py` | Detects 80%+ challenges correctly |
| 9-10 | 3-Layer Escalation | `orchestrator.py` | Routes correctly, minimal re-tries |

### Success Metrics

- ✅ **Success Rate:** ≥90% across 20 test sites
- ✅ **Latency:** ≤2x slower than Firecrawl (acceptable trade-off)
- ✅ **Code Complexity:** <500 LoC (vs 15,000+ for Firecrawl)
- ✅ **Team Confidence:** High (unanimous yes to proceed)

### Go/No-Go Decision Gate

**If Success Rate ≥90%:**
- ✅ Proceed to Week 3-4 (API Layer)

**If Success Rate <90%:**
- 🔄 Debug for 2 additional days (Week 2, Days 9-10)
- 🔄 If still <90%: Abort migration, optimize Firecrawl instead
- ❌ Do NOT proceed to Week 3 without validation

### Architecture: 3-Layer Escalation

```
Input URL
    ↓
[Layer 1: curl_cffi]  ← TLS fingerprinting, 50ms, LOW cost
    ├─ Success? → Return content
    └─ Failed/Detected? ↓
[Layer 2: Crawlee HTTP] ← Session management, 200-500ms, LOW cost
    ├─ Success? → Return content
    └─ Failed/Challenge? ↓
[Layer 3: Crawlee Browser] ← Full Playwright, 2-5s, MEDIUM cost
    ├─ Success? → Return content
    └─ Failed/Cloudflare? ↓
[Layer 4: Proxies] ← Add BrightData IP rotation
[Layer 5: FlareSolverr] ← Last resort, 10-30s, HIGH cost
```

### Key Architectural Decision

**Decision: Challenge-Driven Escalation (not time-based)**

- **Why:** Minimize cost (only escalate when needed)
- **Alternative:** Time-based (Layer 1 for 1s, then Layer 2, then Layer 3)
- **Trade-off:** Complexity vs. cost (acceptable)
- **Contingency:** If challenges undetectable, switch to time-based

---

## 📋 Iterations 2-4: Weeks 3-8 (Core Platform)

**Detailed Plans:** See `iteration_1_weeks_1-4.md` (Part 2) and `iteration_2_weeks_5-8.md`

### Iteration 2: Weeks 3-4 (API Layer)

**Objective:** Build production-ready REST API with async job processing

**Key Deliverables:**
- FastAPI application skeleton
- PostgreSQL schema with Row-Level Security
- API key authentication
- BullMQ/Redis job queue
- /v2/scrape endpoint (Firecrawl-compatible)
- Rate limiting middleware
- Docker deployment stack

**Architecture Decision: Why arq over BullMQ?**

| Factor | arq | BullMQ | Winner |
|--------|-----|--------|--------|
| **Language** | Python | Node.js | arq (no Node.js needed) |
| **Data Store** | Redis | Redis | Tie |
| **Throughput** | 1000+ jobs/sec | 2000+ jobs/sec | BullMQ (overkill) |
| **Simplicity** | ⭐⭐ Simple | ⭐⭐⭐ More config | arq |
| **Team Expertise** | Python team | JS team | arq (Python-native) |

**Decision:** Use arq for MVP, migrate to BullMQ if throughput exceeds 1000 jobs/sec (Month 9+)

### Iteration 3: Weeks 5-6 (Multi-Tenancy)

**Objective:** Enable multiple customers to use platform securely

**Key Deliverables:**
- Tenant registration & API key management
- PostgreSQL Row-Level Security (RLS)
- Rate limiting (sliding window algorithm)
- Quota management & usage tracking
- S3 storage with tenant isolation

**Architecture Decision: Why PostgreSQL RLS?**

| Approach | Security | Maintainability | Performance | Verdict |
|----------|----------|-----------------|-------------|---------|
| **RLS (DB Layer)** | Bulletproof | Simple | -5% query slowdown | **BEST** |
| **Application Filter** | App-dependent | Complex | Fast | Risky |
| **Separate DB per Tenant** | Perfect | Complex ops | Fast | Expensive |

**Decision:** PostgreSQL RLS for MVP (database-enforced isolation, immune to app bugs)

### Iteration 4: Weeks 7-8 (Anti-Detection)

**Objective:** Port 3-layer escalation strategy from Firecrawl, add advanced anti-detection

**Key Deliverables:**
- curl_cffi Layer 1 (TLS fingerprinting)
- Crawlee Layers 2-3 (HTTP + Browser)
- BrightData proxy integration
- FlareSolverr Cloudflare solver
- Intelligent router (challenge-driven escalation)
- Site profiles database

**Architecture Decision: Why BrightData over Oxylabs/Smartproxy?**

| Provider | Cost/GB | Succ Rate | Speed | Anti-Detection | Best For |
|----------|---------|-----------|-------|----------------|----------|
| **BrightData** | $12.75 | 99.9% | Fast | Excellent | **Production** |
| **Oxylabs** | $15 | 99.8% | Fast | Good | Cost-agnostic |
| **Smartproxy** | $10 | 95% | Medium | OK | Budget-conscious |

**Decision:** BrightData for MVP (best success rate + anti-detection reputation)

---

## 📊 Iterations 5-6: Weeks 9-12 (Hardening & Launch)

**Detailed Plan:** See `iteration_3_weeks_9-12_synthesis.md` (to be created by Senior TPM)

### Iteration 5: Weeks 9-10 (Production Hardening)

**Objective:** Make platform production-ready with monitoring, testing, runbooks

**Key Deliverables:**
- Prometheus + Grafana monitoring stack
- Sentry error tracking
- Locust load testing (1000 concurrent users)
- Operational runbooks (incident response, on-call)
- Performance optimization (P99 <30s)

**Architecture Decision: Why Prometheus + Grafana over CloudWatch-only?**

| Aspect | Prometheus + Grafana | CloudWatch-only | Winner |
|--------|---------------------|-----------------|--------|
| **Cost** | $100/month | $150/month | Prometheus |
| **Vendor Lock-in** | None (portable) | AWS-only | Prometheus |
| **Visualization** | Excellent | Basic | Prometheus |
| **Self-hosted** | Yes | No | Prometheus |

**Decision:** Prometheus + Grafana for MVP (portable, cost-effective, excellent UX)

### Iteration 6: Weeks 11-12 (Migration & Launch)

**Objective:** Successfully migrate from Firecrawl to Crawlee without downtime

**Key Deliverables:**
- Staging deployment & smoke tests
- Parallel run infrastructure (load balancer routing)
- Gradual traffic shifting plan (20% → 100%)
- Rollback procedures
- Decommission Firecrawl

**Architecture Decision: Why gradual migration vs big bang?**

| Aspect | Gradual (20%→50%→80%→100%) | Big Bang |
|--------|---------------------------|----------|
| **Risk** | Low (catch issues early) | Very High |
| **Rollback** | <5 minutes (instant) | Hours |
| **Validation** | Continuous | None |
| **Cost** | $1K extra (2-week parallel) | $0 |
| **Confidence** | High | Low |

**Decision:** 2-week gradual migration (risk mitigation > $1K cost)

---

## 🏗️ Architecture Evolution: Week by Week

### Week 1-2: Validation
```
Crawlee Proof of Concept
    ├── Layer 1: curl_cffi (TLS fingerprinting)
    ├── Layer 2: HTTP crawler
    ├── Layer 3: Browser (Playwright)
    └── Challenge detection
```

### Week 3-4: Foundation API
```
FastAPI + PostgreSQL
    ├── /v2/scrape endpoint
    ├── API key auth
    ├── arq job queue
    └── Docker Compose stack
```

### Week 5-6: Multi-Tenant
```
Previous + Tenant Isolation
    ├── PostgreSQL RLS
    ├── Rate limiting (sliding window)
    ├── Quota tracking
    ├── S3 tenant buckets
    └── Billing integration
```

### Week 7-8: Anti-Detection
```
Previous + Advanced Anti-Detection
    ├── Layer 1: curl_cffi
    ├── Layer 2-3: Crawlee + fingerprint spoofing
    ├── Layer 4: BrightData proxies
    ├── Layer 5: FlareSolverr
    └── Intelligent router
```

### Week 9-10: Hardening
```
Previous + Production-Ready
    ├── Prometheus + Grafana
    ├── Sentry error tracking
    ├── Locust load tests
    ├── Operational runbooks
    └── Performance tuning
```

### Week 11-12: Launch
```
Migrate from Firecrawl
    ├── Parallel run infrastructure
    ├── Gradual traffic shifting (5 phases)
    ├── Rollback procedures
    ├── Post-launch validation
    └── Decommission old stack
```

---

## 📊 Success Metrics by Iteration

### Iteration 1 (Week 2 Gate)
- ✅ Success rate ≥90%
- ✅ Latency ≤2x Firecrawl
- ✅ Code <500 LoC
- ✅ Team confidence: High

### Iteration 2 (Week 4)
- ✅ 2 API endpoints working (POST /scrape, GET /scrape/{id})
- ✅ API key auth functional
- ✅ Job queue <30s P95 latency
- ✅ Test coverage >80%
- ✅ Docker stack runnable

### Iteration 3 (Week 6)
- ✅ 100% tenant isolation (zero cross-tenant leaks)
- ✅ Rate limiting >99% accurate
- ✅ Quota tracking 100% (no double-counting)
- ✅ S3 storage operational

### Iteration 4 (Week 8)
- ✅ Layer 1: >60% success (simple sites)
- ✅ Layer 3: >85% success (JS sites)
- ✅ Layer 5: >95% success (Cloudflare)
- ✅ Cost per scrape <$0.01
- ✅ Escalation latency <1s

### Iteration 5 (Week 10)
- ✅ Monitoring: All metrics collected
- ✅ Load test: >90% success at 1000 concurrent
- ✅ P99 latency: <30s
- ✅ Error rate: <5%
- ✅ Runbooks: Complete

### Iteration 6 (Week 12)
- ✅ Migration: Success rate ≥95% of Firecrawl baseline
- ✅ Zero downtime during cutover
- ✅ Rollback: <5 minutes
- ✅ Firecrawl decommissioned

---

## 🎯 Critical Path & Bottlenecks

### Critical Path (Cannot Parallelize)
```
PoC (Week 1-2)
  → API (Week 3-4)
    → Multi-Tenancy (Week 5-6)
      → Anti-Detection (Week 7-8)
        → Hardening (Week 9-10)
          → Launch (Week 11-12)
```

### Critical Bottlenecks

1. **Week 2 PoC Success:** If <90% success rate, entire project at risk
   - Mitigation: 2-day debug window (Week 2, Days 9-10)
   - Contingency: Abort, optimize Firecrawl instead

2. **Week 4 API Stability:** Must be solid foundation
   - Risk: Schema changes cause migration pain
   - Mitigation: Design schema for scale, test early

3. **Week 8 Anti-Detection:** Must achieve >80% success
   - Risk: Porting Firecrawl logic is complex
   - Mitigation: Allocate 4 days (Days 1-4 of Week 8) for debugging

4. **Week 10 Performance:** Must hit targets before migration
   - Risk: Optimization unknowns
   - Mitigation: Start load testing Week 8 (parallel with anti-detection work)

5. **Week 12 Migration:** Point of no return
   - Risk: Unforeseen regressions
   - Mitigation: 2-week parallel run, gradual traffic shift, instant rollback

---

## 🚨 Risk Mitigation: Week by Week

### Week 1-2: PoC Risk
- **Risk:** Crawlee PoC fails (<90% success)
- **Probability:** Low (Crawlee proven by Apify)
- **Impact:** High (entire project canceled)
- **Mitigation:** Allocate 2-day debug window (Days 9-10)
- **Contingency:** Abort migration, optimize Firecrawl instead

### Week 3-4: API Risk
- **Risk:** API schema incompatible with Week 5-6 multi-tenancy
- **Probability:** Medium
- **Impact:** High (1-2 week rework)
- **Mitigation:** Copy Firecrawl /v2/scrape schema exactly, E2E tests
- **Contingency:** Rollback to iterative schema, lose 1 week

### Week 5-6: Multi-Tenancy Risk
- **Risk:** RLS policies have security gaps (cross-tenant leaks)
- **Probability:** Low
- **Impact:** Very High (security breach)
- **Mitigation:** Security audit + penetration testing before Week 7
- **Contingency:** Rollback to application-level filtering (slower, safer)

### Week 7-8: Anti-Detection Risk
- **Risk:** Anti-detection logic fails to escalate correctly
- **Probability:** Medium (porting complexity)
- **Impact:** High (90%+ of sites unreachable)
- **Mitigation:** Port all Firecrawl patterns + challenge detection logic
- **Contingency:** Fall back to simple HTTP-only until fixed

### Week 9-10: Performance Risk
- **Risk:** Performance targets not met (P99 >30s)
- **Probability:** Medium
- **Impact:** High (unacceptable for production)
- **Mitigation:** Start profiling Week 7, iterate optimizations Week 8-9
- **Contingency:** Extend optimization sprint by 1 week (Week 10-11)

### Week 11-12: Migration Risk
- **Risk:** Migration regression (success rate drops to <85%)
- **Probability:** Low (parallel run catches issues)
- **Impact:** Very High (data loss, customer impact)
- **Mitigation:** Gradual traffic shift (20% → 50% → 80% → 100%), instant rollback
- **Contingency:** Immediate rollback, maintain parallel run longer

---

## 📋 Phase Gate Decisions

### Phase Gate 1: End of Week 2
**Decision:** Proceed with migration?

**Go Criteria:**
- Success rate ≥90%
- Latency ≤2x Firecrawl
- Team confidence: High

**No-Go Criteria:**
- Success rate <90% (after debug)
- Latency >2x Firecrawl
- Team confidence: Low

### Phase Gate 2: End of Week 4
**Decision:** API ready for multi-tenancy?

**Go Criteria:**
- 2 endpoints working
- Test coverage >80%
- Docker stack runs

**No-Go Criteria:**
- Schema incompatible with multi-tenancy
- Test coverage <60%
- Docker setup broken

### Phase Gate 3: End of Week 8
**Decision:** Anti-detection ready for production?

**Go Criteria:**
- Layer 1: >60% success
- Layer 3: >85% success
- Layer 5: >95% success
- Escalation logic working

**No-Go Criteria:**
- Any layer <50% success
- Escalation logic broken
- Cost per scrape >$0.02

### Phase Gate 4: End of Week 10
**Decision:** Ready to migrate?

**Go Criteria:**
- All success metrics met
- Load test: >90% success at 1K concurrent
- P99 <30s
- Monitoring operational

**No-Go Criteria:**
- Performance targets not met
- Monitoring incomplete
- Error rate >5%

### Phase Gate 5: End of Week 12
**Decision:** Cutover successful?

**Go Criteria:**
- Success rate ≥95% of baseline
- Zero critical incidents
- Rollback plan validated
- Team confident

**No-Go Criteria:**
- Success rate <85%
- Critical incident requiring rollback
- Performance degradation >2x

---

## 💰 Cost Breakdown

### Development Cost (12 weeks)

| Phase | Effort | Cost (1 dev @ $100/hr) |
|-------|--------|----------------------|
| Week 1-2: PoC | 80 hrs | $8K |
| Week 3-4: API | 80 hrs | $8K |
| Week 5-6: Multi-Tenancy | 80 hrs | $8K |
| Week 7-8: Anti-Detection | 90 hrs | $9K |
| Week 9-10: Hardening | 70 hrs | $7K |
| Week 11-12: Migration | 60 hrs | $6K |
| **Total** | **460 hrs** | **$46K** |

*(Assumes 1-2 developers at $100/hr; adjust for team size)*

### Infrastructure Cost

| Phase | Cost/Month | Notes |
|-------|------------|-------|
| Week 1-2: Dev only | $50 | Single instance |
| Week 3-4: Dev + DB | $200 | RDS small, ElastiCache |
| Week 5-6: PoC scale | $500 | Multiple workers |
| Week 7-8: Anti-detection testing | $800 | Proxy costs |
| Week 9-10: Load testing | $1,000 | Full stack + proxies |
| Week 11-12: Parallel run | $1,900 | Firecrawl + Crawlee |
| **Post-Migration** | **$965/month** | Ongoing ops |

**Total Infrastructure Cost (12 weeks):** ~$5,450 total + $965/month ongoing

---

## 📈 Business Metrics

### Phase 1 (Months 1-6): Internal Data Collection

**Technical:**
- Success rate: >90%
- Cost per scrape: <$0.01
- Availability: 99%+
- Team maintenance: 20% time

**Business:**
- Build 3+ internal scrapers
- Validate cost model
- Document learnings
- Prepare for Phase 2

### Phase 2 (Months 7-12): Multi-Tenant Platform MVP

**Technical:**
- 99.9% uptime
- <5% error rate
- Handle 10K+ jobs/day
- Auto-scaling proven

**Business:**
- 50+ paying customers
- $5K+ MRR
- <5% churn
- NPS >40

### Phase 3 (Months 13-18): Growth + AI

**Technical:**
- Handle 100K+ jobs/day
- LLM extraction available
- Vector search operational

**Business:**
- 200+ customers
- $30K+ MRR
- Gross margin >70%
- Product-market fit

---

## 🗂️ Detailed Plans Available

### Iteration 1 & 2: Weeks 1-4
📄 **File:** `iteration_1_weeks_1-4.md`
- Day-by-day breakdown (20 days)
- Architecture decisions with rationale
- Code examples (100+ snippets)
- Risk mitigation matrix
- Success criteria

### Iteration 3 & 4: Weeks 5-8
📄 **File:** `iteration_2_weeks_5-8.md`
- Multi-tenancy design (Weeks 5-6)
- Anti-detection integration (Weeks 7-8)
- Database migrations
- API contracts
- Testing strategies

### Iteration 5 & 6: Weeks 9-12
📄 **File:** `iteration_3_weeks_9-12_synthesis.md` *(to be created)*
- Production hardening (Weeks 9-10)
- Migration strategy (Weeks 11-12)
- Monitoring architecture
- Load testing plan
- Runbooks & checklists

---

## ✅ Next Steps

### Monday, Week 1
1. Read `iteration_1_weeks_1-4.md` (2 hours)
2. Execute Day 1 tasks (3-4 hours)
3. Commit code to git
4. Daily standup: Report progress

### Repeat for 12 Weeks
- Follow day-by-day plan
- Track metrics daily
- Report blockers weekly
- Proceed through phase gates

### Success Criteria
✅ By end of Week 12:
- Crawlee platform deployed to production
- Firecrawl decommissioned
- Team trained & confident
- Ready for customer onboarding

---

## 📞 Decision Makers & Ownership

| Role | Responsibility | Contact |
|------|-----------------|---------|
| **Senior TPM** | Strategic decisions, phase gates, risk mitigation | - |
| **TPM #1** | Week 1-4 execution, PoC validation, API design | - |
| **TPM #2** | Week 5-8 execution, multi-tenancy & anti-detection | - |
| **Dev Team** | Day-to-day implementation, testing, debugging | - |

---

## 🎯 Key Success Factors

1. **PoC Validation (Week 2):** Must hit ≥90% success rate
2. **API Design (Week 4):** Must support future multi-tenancy
3. **Multi-Tenancy Security (Week 6):** Must pass security audit
4. **Anti-Detection Porting (Week 8):** Must replicate Firecrawl behavior
5. **Performance (Week 10):** Must hit P99 <30s
6. **Migration Execution (Week 12):** Must achieve zero downtime

**Success = All 6 factors achieved on timeline**

---

## 📌 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-02 | Senior TPM Team | Initial comprehensive plan |

---

**Status:** 🟢 Ready for Execution
**Last Updated:** 2026-02-02
**Confidence Level:** ⭐⭐⭐⭐⭐ (High - based on comprehensive analysis and experienced TPM input)
