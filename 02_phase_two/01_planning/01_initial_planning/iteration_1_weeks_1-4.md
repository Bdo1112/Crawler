# Iteration Plan: Weeks 1-4 (Foundation & API Layer)

**Document Version:** 1.0
**Created:** 2026-02-02
**Author:** Technical Product Manager #1
**Status:** Ready for Implementation

---

## Executive Summary

This document provides an extremely detailed, day-by-day implementation plan for the first 4 weeks of the Crawlee migration project. The plan is structured for a 1-3 person team and assumes no prior Crawlee experience.

**Outcome**: By Week 4, you will have a production-ready scraping API with:
- ✅ Validated Crawlee engine (≥90% success rate)
- ✅ FastAPI REST API with async job processing
- ✅ Multi-tenant authentication (API keys)
- ✅ PostgreSQL database with Row-Level Security
- ✅ Job queue (arq + Redis)
- ✅ Docker deployment stack
- ✅ Comprehensive test suite

---

## Table of Contents

1. [Strategic Context & Architectural Decisions](#strategic-context--architectural-decisions)
2. [Iteration 1: Weeks 1-2 (Proof of Concept)](#iteration-1-weeks-1-2-proof-of-concept)
3. [Iteration 2: Weeks 3-4 (API Layer)](#iteration-2-weeks-3-4-api-layer)
4. [Success Metrics & Decision Gates](#success-metrics--decision-gates)
5. [Risk Mitigation](#risk-mitigation)
6. [Appendices](#appendices)

---

## Strategic Context & Architectural Decisions

### Why Migrate from Firecrawl to Crawlee?

Based on the comprehensive analysis in `STRATEGIC_DECISION.md`, the migration is justified by:

| Factor | Firecrawl | Crawlee | Improvement |
|--------|-----------|---------|-------------|
| **Monthly Cost** (300K jobs) | $1,500-3,000 | $965 | 35-50% savings |
| **Services Required** | 7 (complex) | 4 (simple) | 43% reduction |
| **RAM Required** | 18GB | 12GB | 33% reduction |
| **Team Maintenance** | 50% time | 20% time | 60% less burden |
| **Production-Ready** | ⚠️ Self-hosted not ready | ✅ Battle-tested by Apify | Proven |

**Decision**: Migrate to Crawlee if Week 1-2 PoC validates ≥90% success rate.

---

### Key Architectural Decisions

#### 1. Why BullMQ → arq (Python Queue)?

**Initial Plan**: Use BullMQ (Node.js) for job queue (Redis-backed, rich features).

**Pivot Decision**: Use **arq** (Python Redis queue) instead.

**Rationale**:
- **Team Alignment**: Python-first stack (Crawlee Python SDK, FastAPI)
- **Operational Simplicity**: No Node.js runtime needed for workers
- **Cost**: Free (Redis only), BullMQ would require Node.js containers
- **Performance**: 1000+ jobs/sec throughput (sufficient for MVP)
- **Developer Experience**: Native async/await, integrates seamlessly with FastAPI

**Trade-offs**:
- ❌ **Lost**: Bull Board UI (visual queue management)
- ❌ **Lost**: Advanced retry strategies (BullMQ has more options)
- ✅ **Gained**: Simpler ops (1 language, 1 runtime)
- ✅ **Gained**: Faster development (no context switching)

**Migration Path**: If Bull Board UI becomes critical (Month 6+), we can:
- Add thin Node.js layer for BullMQ consumer only
- Keep FastAPI API + Python Crawlee workers
- Use Bull Board for monitoring

**Decision**: Start with arq, evaluate BullMQ in Month 6+ if needed.

---

#### 2. Why FastAPI over Node.js (Express/Fastify)?

**Alternative**: Use Node.js to match BullMQ natively.

**Decision**: **FastAPI** (Python).

**Rationale**:
- **Team Skill**: Python-first team (existing Firecrawl work in Python)
- **Ecosystem**: Rich async libraries (asyncpg, aioboto3, aiohttp)
- **Performance**: 2-3x faster than Flask/Django, comparable to Node.js
- **Type Safety**: Pydantic models, automatic OpenAPI docs
- **Maintenance**: 1 language reduces cognitive load

**Trade-offs**:
- ❌ **Lost**: Native BullMQ integration (Node.js is first-class)
- ✅ **Gained**: Type-safe API (Pydantic validation)
- ✅ **Gained**: Auto-generated docs (OpenAPI/Swagger)
- ✅ **Gained**: Async-first (better than Flask/Django)

**Code Comparison**:
```python
# FastAPI (50 lines for endpoint + validation + docs)
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

class ScrapeRequest(BaseModel):
    url: HttpUrl
    timeout: int = 60000

@app.post("/v2/scrape")
async def scrape(request: ScrapeRequest):
    # Auto-validated, auto-documented
    return {"job_id": "abc123"}
```

vs.

```javascript
// Express (80 lines for same features + manual validation)
const express = require('express');
const { body, validationResult } = require('express-validator');

app.post('/v2/scrape',
    body('url').isURL(),
    body('timeout').isInt({ min: 1000, max: 300000 }),
    (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }
        // ... manual docs, manual types
    }
);
```

**Decision**: FastAPI wins on developer experience and time-to-market.

---

#### 3. Authentication Strategy: API Keys → OAuth (Phased)

**Week 4**: Simple API key authentication (SHA256 hashed).

**Month 7+**: Add OAuth 2.0 + JWT (optional, non-breaking).

**Rationale**:
- **MVP Speed**: API keys take 1 day to implement vs 1 week for OAuth
- **User Need**: Early adopters don't need SSO (technical users, CLI/SDK)
- **Migration Path**: Add OAuth later without breaking existing API keys
- **Cost**: API keys free, OAuth adds complexity (auth provider, token refresh)

**API Key Design**:
- Format: `sk-live-<32 hex chars>` (similar to Stripe)
- Storage: SHA256 hash only (never store plain text)
- Validation: Single DB lookup (fast, simple)
- Revocation: Set `is_active = false` flag

**OAuth Design (Future)**:
- Provider: Auth0 or self-hosted (Keycloak)
- Flow: Authorization Code + PKCE (secure for web/mobile)
- Token: JWT with 1-hour expiry, refresh tokens in Redis
- Migration: API keys remain valid, OAuth optional per tenant

**Decision**: API keys for Week 4, OAuth in Month 7+ if needed.

---

#### 4. PostgreSQL Schema: Multi-Tenant from Day 1

**Decision**: Single PostgreSQL database with Row-Level Security (RLS).

**Alternative Considered**: Separate database per tenant.

**Why Single Database with RLS?**
- **Cost**: 1 RDS instance ($70/month) vs N instances ($70 × N/month)
- **Ops Simplicity**: 1 migration, 1 backup, 1 monitoring dashboard
- **Proven Pattern**: Used by Crunchy Data, Supabase (battle-tested)
- **Security**: RLS enforces isolation at Postgres level (not app logic)

**Trade-offs**:
- ✅ **Pro**: Lower cost, simpler ops
- ❌ **Con**: No physical data isolation (all tenants share DB)
- ❌ **Con**: Noisy neighbor potential (one tenant's heavy query slows others)

**Mitigation for Cons**:
- Connection pooling (pgbouncer) prevents resource exhaustion
- Query timeouts (30s max) prevent runaway queries
- Enterprise tier → Separate RDS instance (Month 12+)

**RLS Example**:
```sql
-- Enable RLS
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their tenant's jobs
CREATE POLICY tenant_isolation ON jobs
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- In application, set tenant_id before queries
-- SET LOCAL app.current_tenant_id = '550e8400-e29b-41d4-a716-446655440000';
```

**Decision**: Single DB + RLS for MVP, separate DB for enterprise tier later.

---

#### 5. What We're NOT Building (Weeks 1-4)

| Feature | Why Deferred | When to Add |
|---------|-------------|-------------|
| **Scrapy Integration** | No high-volume need yet (<100K req/month) | Month 6+ (if >1M req/month + >70% static HTML) |
| **OAuth/JWT** | API keys sufficient for MVP | Month 7+ (when enterprise customers need SSO) |
| **UI Dashboard** | API-first, Postman + SDK sufficient | Month 3+ (after API stable) |
| **Advanced Anti-Detection** | Crawlee built-in works for 90% of sites | Week 7-8 (curl_cffi, BrightData proxies) |
| **FlareSolverr** | Only 5-10% of sites need Cloudflare solver | Week 7-8 (on-demand microservice) |
| **Actor Marketplace** | Need core platform first | Month 7+ (Phase 2 multi-tenant features) |
| **AI/LLM Extraction** | Not MVP differentiator | Month 13+ (Phase 3 premium tier) |
| **Webhooks** | Polling sufficient for MVP | Month 5+ (when customers request it) |
| **Bulk Upload** | Single URL enough for validation | Month 4+ (after CSV/API batch endpoint) |

**Principle**: Ship fast, iterate based on user feedback. Don't build features speculatively.

---

## Iteration 1: Weeks 1-2 (Proof of Concept)

**Goal**: Validate Crawlee can replace Firecrawl with ≥90% success rate and ≤2x latency.

**Team**: 1 developer (full-time) or 2 developers (part-time).

**Decision Gate**: If PoC fails (<90% success rate), pivot to optimizing Firecrawl instead.

---

### Week 1: Environment Setup & Initial Validation

#### **Day 1 (Monday): Environment Setup**

**Objective**: Set up Crawlee Python environment and run basic examples.

**Time Estimate**: 3-4 hours

**Prerequisites**:
- macOS or Linux (Windows requires WSL2)
- Python 3.11+ installed
- Docker Desktop (for Playwright browsers)

**Tasks**:

1. **Create Project Structure**
```bash
mkdir -p /Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc
cd /Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc
```

2. **Clone Crawlee Examples**
```bash
git clone https://github.com/apify/crawlee-python
cd crawlee-python
```

3. **Set Up Python Environment**
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

4. **Install Crawlee with Playwright**
```bash
# Install Crawlee with all features
pip install 'crawlee[playwright]'

# Install Playwright browsers (Chromium, Firefox, WebKit)
playwright install chromium

# Verify installation
python -c "import crawlee; print(crawlee.__version__)"
```

5. **Run Official Examples**
```bash
cd examples

# Example 1: Basic HTTP crawler
python basic_crawler.py
# Expected: Scrapes 5 pages, saves to ./storage/datasets/default/

# Example 2: Playwright (browser) crawler
python playwright_crawler.py
# Expected: Opens Chromium, scrapes JS-rendered pages

# Example 3: Adaptive crawler (HTTP → Browser fallback)
python adaptive_crawler.py
# Expected: Tries HTTP first, switches to browser if needed
```

6. **Document Setup Issues**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/SETUP_NOTES.md`:

```markdown
# Crawlee Setup Notes (Day 1)

## System Info
- OS: macOS 14.x (Apple Silicon / Intel)
- Python: 3.11.x
- Crawlee: 0.x.x

## Installation Steps
1. Created venv: python3.11 -m venv venv
2. Installed Crawlee: pip install 'crawlee[playwright]'
3. Installed browsers: playwright install chromium

## Gotchas
- [ ] Issue 1: Playwright download failed on first try → Solution: Re-ran with sudo
- [ ] Issue 2: Chromium won't launch → Solution: Installed system dependencies (libX11)

## Example Results
- basic_crawler.py: ✅ Success (scraped 5 pages in 2.3s)
- playwright_crawler.py: ✅ Success (browser opened, rendered JS)
- adaptive_crawler.py: ✅ Success (HTTP → Browser fallback worked)

## Screenshots
- [Crawlee running in terminal](./screenshots/day1-terminal.png)
- [Playwright browser opening](./screenshots/day1-browser.png)

## Next Steps
- Day 2: Port first pattern from scraper.py
```

**Acceptance Criteria**:
- [ ] Virtual environment created and activated
- [ ] Crawlee installed successfully (`crawlee.__version__` prints)
- [ ] Chromium browser installed (playwright list --browsers shows chromium)
- [ ] All 3 official examples run without errors
- [ ] SETUP_NOTES.md created with troubleshooting steps

**Common Issues & Solutions**:

| Issue | Solution |
|-------|----------|
| `playwright install` fails | Run with `--with-deps` flag: `playwright install --with-deps chromium` |
| Chromium won't launch on macOS | Security popup: System Preferences → Security → Allow Chromium |
| Import error: `No module named 'crawlee'` | Ensure venv activated: `source venv/bin/activate` |
| Slow download (Playwright) | Use VPN if GitHub releases blocked in your region |

**Output Files**:
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/venv/` (virtual environment)
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/crawlee-python/` (examples)
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/SETUP_NOTES.md`

**Risk**: Playwright installation issues on ARM Macs.
**Mitigation**: Use Docker if native fails: `docker run mcr.microsoft.com/playwright/python:latest`

---

#### **Day 2 (Tuesday): Port First Pattern from scraper.py**

**Objective**: Implement simplest scraping pattern in Crawlee.

**Time Estimate**: 4-5 hours

**Selected Pattern**: Static HTML sites (no JavaScript, no anti-detection).

**Test Sites** (5 representative):
1. `https://en.wikipedia.org/wiki/Web_scraping` (static HTML, large)
2. `https://news.ycombinator.com/` (static HTML, simple)
3. `https://example.com/` (minimal HTML)
4. `https://httpbin.org/html` (test endpoint)
5. `https://www.gutenberg.org/` (static HTML, text-heavy)

**Tasks**:

1. **Analyze scraper.py Layer 1 (curl_cffi)**

Open `/Users/brianoh/Dev/01_Personal/04_crawler/01_phase_one/scripts/scraper.py` and study:
- Lines 229-323: `try_curl_cffi()` function
- Headers used (lines 254-266)
- Challenge detection (lines 283-294)
- Content validation (lines 297-305)

2. **Implement Crawlee HTTP Equivalent**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/crawlee_layer1.py`:

```python
"""
Crawlee Layer 1: HTTP crawler (no JavaScript)
Equivalent to scraper.py curl_cffi layer
"""
import asyncio
from crawlee.http_crawler import HttpCrawler, HttpCrawlingContext
from crawlee.storages import Dataset
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def scrape_handler(context: HttpCrawlingContext):
    """Handler for each scraped page"""
    start_time = time.time()

    # Extract basic info
    url = context.request.url
    status_code = context.http_response.status_code
    content = context.body
    content_length = len(content)

    # Parse HTML (BeautifulSoup available via context.soup)
    page_title = "N/A"
    if context.soup:
        title_tag = context.soup.find('title')
        if title_tag:
            page_title = title_tag.text.strip()

    elapsed = time.time() - start_time

    # Check if content is meaningful (>500 chars)
    is_meaningful = content_length > 500

    logger.info(
        f"Scraped {url}: {status_code}, "
        f"{content_length} bytes, "
        f"{elapsed:.2f}s, "
        f"Title: {page_title[:50]}..."
    )

    # Push data to dataset
    await context.push_data({
        'url': url,
        'title': page_title,
        'status_code': status_code,
        'content_length': content_length,
        'is_meaningful': is_meaningful,
        'elapsed': elapsed,
        'success': is_meaningful and status_code == 200,
        'layer': 1,  # HTTP layer
    })


async def main():
    """Main entry point"""
    # Test sites
    urls = [
        'https://en.wikipedia.org/wiki/Web_scraping',
        'https://news.ycombinator.com/',
        'https://example.com/',
        'https://httpbin.org/html',
        'https://www.gutenberg.org/',
    ]

    # Create HTTP crawler
    crawler = HttpCrawler(
        request_handler=scrape_handler,
        max_requests_per_crawl=len(urls),
        max_request_retries=3,
        max_concurrent_requests=5,  # Scrape 5 at once
    )

    # Run crawler
    logger.info(f"Starting Crawlee HTTP crawler for {len(urls)} URLs")
    start_time = time.time()

    await crawler.run(urls)

    total_elapsed = time.time() - start_time
    logger.info(f"Crawling completed in {total_elapsed:.2f}s")

    # Print results
    dataset = await Dataset.open()
    results = await dataset.get_data()

    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    success_count = sum(1 for item in results.items if item.get('success'))
    print(f"Total: {len(results.items)}")
    print(f"Success: {success_count} ({success_count/len(results.items)*100:.1f}%)")
    print(f"Average time: {total_elapsed/len(results.items):.2f}s per URL")
    print("="*60)

    for item in results.items:
        status = "✅" if item.get('success') else "❌"
        print(f"{status} {item['url']}: {item['status_code']}, {item['content_length']} bytes")


if __name__ == '__main__':
    asyncio.run(main())
```

3. **Run and Compare**

```bash
cd /Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc
python crawlee_layer1.py
```

Expected output:
```
INFO:__main__:Starting Crawlee HTTP crawler for 5 URLs
INFO:__main__:Scraped https://example.com/: 200, 1256 bytes, 0.12s, Title: Example Domain
INFO:__main__:Scraped https://news.ycombinator.com/: 200, 45232 bytes, 0.34s, Title: Hacker News
...
INFO:__main__:Crawling completed in 2.45s

============================================================
RESULTS SUMMARY
============================================================
Total: 5
Success: 5 (100.0%)
Average time: 0.49s per URL
============================================================
✅ https://example.com/: 200, 1256 bytes
✅ https://news.ycombacker.com/: 200, 45232 bytes
✅ https://en.wikipedia.org/wiki/Web_scraping: 200, 89432 bytes
✅ https://httpbin.org/html: 200, 3741 bytes
✅ https://www.gutenberg.org/: 200, 12456 bytes
```

4. **Compare with scraper.py**

```bash
# Test same URLs with scraper.py (Firecrawl Layer 2)
cd /Users/brianoh/Dev/01_Personal/04_crawler/01_phase_one/scripts
python scraper.py https://example.com --layer 1 -q > /tmp/scraper_result.json

# Compare metrics:
# - Success rate: Crawlee vs scraper.py
# - Latency: Crawlee vs scraper.py
# - Content completeness: Check HTML length
```

5. **Document Comparison**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/LAYER1_COMPARISON.md`:

```markdown
# Layer 1 Comparison: Crawlee HTTP vs scraper.py curl_cffi

## Test Sites (5 static HTML)
1. Wikipedia - Web scraping article
2. Hacker News - Front page
3. Example.com - Minimal HTML
4. httpbin.org/html - Test endpoint
5. Project Gutenberg - Homepage

## Results

| Site | Crawlee Success | scraper.py Success | Crawlee Time | scraper.py Time |
|------|----------------|-------------------|--------------|-----------------|
| Wikipedia | ✅ | ✅ | 0.45s | 0.32s |
| Hacker News | ✅ | ✅ | 0.34s | 0.28s |
| Example.com | ✅ | ✅ | 0.12s | 0.08s |
| httpbin.org | ✅ | ✅ | 0.23s | 0.19s |
| Gutenberg | ✅ | ✅ | 0.41s | 0.35s |

## Metrics
- **Success Rate**: Crawlee 100%, scraper.py 100% (tie)
- **Average Latency**: Crawlee 0.31s, scraper.py 0.24s (1.3x slower)
- **Code Complexity**: Crawlee 60 LoC, scraper.py 95 LoC (37% less code)

## Observations
- Crawlee slightly slower (1.3x) but still <500ms per URL
- Crawlee code is cleaner (no manual session management)
- Both handle static HTML perfectly

## Verdict
✅ **PASS** - Crawlee HTTP mode viable for Layer 1 replacement
```

**Acceptance Criteria**:
- [ ] All 5 test sites scraped successfully (100% success rate)
- [ ] Content length >500 chars for each site
- [ ] Execution time logged and compared with scraper.py
- [ ] Results saved to Crawlee dataset (`./storage/datasets/default/`)
- [ ] Comparison document created
- [ ] Code simpler than scraper.py (fewer lines of code)

**Output Files**:
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/crawlee_layer1.py`
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/storage/datasets/default/` (results)
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/LAYER1_COMPARISON.md`

**Risk**: Crawlee HTTP might not handle redirects/cookies as well as curl_cffi.
**Mitigation**: Crawlee has built-in session management - test edge cases explicitly.

---

#### **Day 3 (Wednesday): Challenge Detection & Auto-Escalation**

**Objective**: Port challenge detection logic and implement layer escalation.

**Time Estimate**: 3-4 hours

**Tasks**:

1. **Extract Challenge Patterns from scraper.py**

Copy patterns from `scraper.py` lines 55-83:

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/challenge_detector.py`:

```python
"""
Challenge detection logic ported from scraper.py
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Detection patterns for bot challenge pages
CHALLENGE_PATTERNS = {
    'cloudflare': [
        'cf-browser-verification',
        'Just a moment...',
        'Checking your browser',
        'ray ID:',
        'cf-challenge',
        '__cf_chl_jschl_tk__',
    ],
    'perimeterx': [
        'px-captcha',
        '_px',
        'perimeterx',
        'pxCaptcha',
    ],
    'datadome': [
        'datadome',
        'dd_challenge',
        'geo.captcha-delivery.com',
    ],
    'generic': [
        'Access denied',
        'bot detection',
        'Attention Required',
        'Access Denied',
        'Forbidden',
        'Please verify you are human',
    ],
}


def detect_challenge(html: str) -> tuple[bool, Optional[str]]:
    """
    Detect if page is a bot challenge or blocking page.

    Args:
        html: HTML content to analyze

    Returns:
        Tuple of (is_challenge, challenge_type)
    """
    if not html or len(html) < 100:
        return False, None

    html_lower = html.lower()

    # Check each challenge type
    for challenge_type, patterns in CHALLENGE_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in html_lower:
                logger.debug(f"Challenge detected: {challenge_type} (pattern: {pattern})")
                return True, challenge_type

    return False, None


def is_content_meaningful(html: str, min_length: int = 500) -> bool:
    """
    Check if HTML content is meaningful (not just boilerplate).

    Args:
        html: HTML content to analyze
        min_length: Minimum length after stripping tags

    Returns:
        True if content appears meaningful
    """
    if not html:
        return False

    # Simple heuristic: Check raw HTML length
    # (More sophisticated: Strip tags, check text content)
    return len(html) >= min_length
```

2. **Implement Auto-Escalation in HTTP Crawler**

Modify `crawlee_layer1.py` to detect challenges:

```python
# Add to crawlee_layer1.py
from challenge_detector import detect_challenge, is_content_meaningful


async def scrape_handler(context: HttpCrawlingContext):
    """Handler with challenge detection"""
    content = context.body

    # Detect challenge
    is_challenge, challenge_type = detect_challenge(content)

    if is_challenge:
        logger.warning(
            f"Challenge detected on {context.request.url}: {challenge_type}"
        )

        # Mark for escalation (browser mode)
        await context.push_data({
            'url': context.request.url,
            'success': False,
            'error': f'Challenge detected: {challenge_type}',
            'needs_escalation': True,
            'layer': 1,
        })

        # Add to queue for Playwright re-scrape
        # (We'll implement Playwright handler next)
        return

    # Check if content meaningful
    if not is_content_meaningful(content):
        logger.warning(
            f"Content appears blocked/empty on {context.request.url}"
        )
        await context.push_data({
            'url': context.request.url,
            'success': False,
            'error': 'Content too short or empty',
            'needs_escalation': True,
            'layer': 1,
        })
        return

    # Success path (same as before)
    # ...
```

3. **Test Against Challenge Sites**

Known Cloudflare-protected sites (for testing):
- `https://nowsecure.nl/` (Cloudflare challenge always)
- `https://www.google.com/recaptcha/api2/demo` (reCAPTCHA demo)

```bash
python crawlee_layer1.py  # Add challenge sites to test list
```

Expected output:
```
WARNING:__main__:Challenge detected on https://nowsecure.nl/: cloudflare
WARNING:__main__:Content appears blocked/empty on https://www.google.com/recaptcha/api2/demo
```

4. **Document Results**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/CHALLENGE_DETECTION_RESULTS.md`:

```markdown
# Challenge Detection Results (Day 3)

## Test Sites

### Normal Sites (Should NOT Trigger Detection)
- [x] example.com - ✅ No false positive
- [x] wikipedia.org - ✅ No false positive
- [x] hackernews.com - ✅ No false positive

### Challenge Sites (Should Trigger Detection)
- [x] nowsecure.nl - ✅ Cloudflare detected
- [x] Google reCAPTCHA demo - ✅ Generic challenge detected

## Detection Accuracy
- True Positives: 2/2 (100%)
- False Positives: 0/10 (0%)
- False Negatives: 0/2 (0%)

## Pattern Performance
- Cloudflare: ✅ Detected (pattern: "Just a moment...")
- reCAPTCHA: ✅ Detected (pattern: "verify you are human")
- PerimeterX: ⚠️ Not tested (no test site available)
- DataDome: ⚠️ Not tested (no test site available)

## Next Steps
- Day 4: Implement Playwright crawler for escalation
- Test full escalation flow (HTTP → Playwright)
```

**Acceptance Criteria**:
- [ ] Challenge detection function ported from scraper.py
- [ ] No false positives on 10 normal sites
- [ ] Correct detection on 2 known challenge sites
- [ ] Logging shows clear challenge type
- [ ] Code is testable (unit tests possible)

**Output Files**:
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/challenge_detector.py`
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/CHALLENGE_DETECTION_RESULTS.md`

**Risk**: False positives (normal pages flagged as challenges).
**Mitigation**: Test against diverse site set (50+ sites), tune patterns.

---

#### **Day 4 (Thursday): Browser Mode (Playwright) + Anti-Detection**

**Objective**: Implement Crawlee Playwright crawler with stealth.

**Time Estimate**: 4-5 hours

**Tasks**:

1. **Create Playwright Crawler**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/crawlee_playwright.py`:

```python
"""
Crawlee Layer 2: Playwright (Browser) crawler
Handles JavaScript-heavy sites and anti-detection
"""
import asyncio
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
from crawlee.storages import Dataset
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def browser_handler(context: PlaywrightCrawlingContext):
    """Handler for browser-based scraping"""
    start_time = time.time()
    page = context.page

    url = context.request.url

    # Wait for page load
    await page.wait_for_load_state('networkidle', timeout=30000)

    # Simulate human behavior (optional)
    await page.mouse.move(100, 100)
    await page.wait_for_timeout(500)

    # Extract data
    title = await page.title()
    content = await page.content()
    content_length = len(content)

    elapsed = time.time() - start_time

    logger.info(
        f"Browser scraped {url}: "
        f"{content_length} bytes, {elapsed:.2f}s, Title: {title[:50]}..."
    )

    # Push data
    await context.push_data({
        'url': url,
        'title': title,
        'content_length': content_length,
        'elapsed': elapsed,
        'success': content_length > 1000,  # JS-rendered pages are larger
        'layer': 2,  # Playwright layer
    })


async def main():
    """Main entry point"""
    # Test JS-heavy sites
    urls = [
        'https://github.com/apify/crawlee',
        'https://www.reddit.com/',
        'https://news.ycombinator.com/',  # Compare with Layer 1
        'https://www.npmjs.com/',
        'https://stackoverflow.com/',
    ]

    # Create Playwright crawler with stealth
    crawler = PlaywrightCrawler(
        request_handler=browser_handler,
        max_requests_per_crawl=len(urls),
        max_concurrent_requests=2,  # Fewer concurrent browsers
        headless=True,  # Run without visible browser
        browser_type='chromium',  # Chromium, firefox, or webkit

        # Anti-detection settings
        browser_options={
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
            ],
        },
    )

    logger.info(f"Starting Playwright crawler for {len(urls)} URLs")
    start_time = time.time()

    await crawler.run(urls)

    total_elapsed = time.time() - start_time
    logger.info(f"Browser crawling completed in {total_elapsed:.2f}s")

    # Print results
    dataset = await Dataset.open()
    results = await dataset.get_data()

    print("\n" + "="*60)
    print("PLAYWRIGHT RESULTS")
    print("="*60)
    success_count = sum(1 for item in results.items if item.get('success'))
    print(f"Total: {len(results.items)}")
    print(f"Success: {success_count} ({success_count/len(results.items)*100:.1f}%)")
    print(f"Average time: {total_elapsed/len(results.items):.2f}s per URL")
    print("="*60)

    for item in results.items:
        status = "✅" if item.get('success') else "❌"
        print(
            f"{status} {item['url']}: "
            f"{item['content_length']} bytes, {item['elapsed']:.2f}s"
        )


if __name__ == '__main__':
    asyncio.run(main())
```

2. **Run and Benchmark**

```bash
python crawlee_playwright.py
```

Expected output:
```
INFO:__main__:Starting Playwright crawler for 5 URLs
INFO:__main__:Browser scraped https://github.com/apify/crawlee: 142356 bytes, 3.4s, Title: GitHub - apify/crawlee: Crawlee—A web scraping an...
...
INFO:__main__:Browser crawling completed in 15.6s

============================================================
PLAYWRIGHT RESULTS
============================================================
Total: 5
Success: 5 (100.0%)
Average time: 3.12s per URL
============================================================
✅ https://github.com/apify/crawlee: 142356 bytes, 3.4s
✅ https://www.reddit.com/: 89432 bytes, 2.9s
✅ https://news.ycombinator.com/: 45232 bytes, 2.1s
✅ https://www.npmjs.com/: 67543 bytes, 3.5s
✅ https://stackoverflow.com/: 78965 bytes, 3.7s
```

3. **Compare Performance: HTTP vs Browser**

Test Hacker News with both:
- Layer 1 (HTTP): ~0.34s
- Layer 2 (Playwright): ~2.1s

**Ratio**: 6.2x slower (acceptable for JS-heavy sites)

4. **Test Anti-Detection**

Use CreepJS detector: `https://abrahamjuliot.github.io/creepjs/`

```python
# Add to test suite
urls = [
    'https://abrahamjuliot.github.io/creepjs/',
    'https://bot.sannysoft.com/',  # Bot detection test
    'https://arh.antoinevastel.com/bots/areyouheadless',  # Headless detection
]
```

Expected: No "Headless Chrome" detection, realistic fingerprint.

5. **Document Results**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/PLAYWRIGHT_RESULTS.md`:

```markdown
# Playwright Browser Mode Results (Day 4)

## Performance Comparison

| Site | HTTP (Layer 1) | Playwright (Layer 2) | Ratio |
|------|---------------|---------------------|-------|
| Hacker News | 0.34s | 2.1s | 6.2x slower |
| GitHub | N/A (JS required) | 3.4s | - |
| Reddit | 0.41s | 2.9s | 7.1x slower |

## Anti-Detection Tests

| Detector | Result | Notes |
|----------|--------|-------|
| CreepJS | ✅ Pass | No headless detection |
| BotDetector | ✅ Pass | Realistic fingerprint |
| AreYouHeadless | ✅ Pass | Browser appears normal |

## Memory Usage
- Single browser instance: ~150MB RAM
- After 10 pages: ~200MB RAM (slight leak, acceptable)

## Verdict
✅ **PASS** - Playwright mode viable for JS-heavy sites
- Performance acceptable (2-4s per page)
- Anti-detection works out-of-box
- Memory usage reasonable (<300MB per crawler)
```

**Acceptance Criteria**:
- [ ] All 5 JS-heavy sites scraped successfully
- [ ] Content length >1000 chars (proves JS rendered)
- [ ] No "bot" or "headless" detection on test sites
- [ ] Performance: 2-5s per page average
- [ ] Memory: <300MB per browser instance

**Output Files**:
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/crawlee_playwright.py`
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/PLAYWRIGHT_RESULTS.md`

**Risk**: Playwright detected by advanced anti-bot (PerimeterX, DataDome).
**Mitigation**: Crawlee uses stealth plugins by default. Test with real protected sites in Day 5.

---

#### **Day 5 (Friday): Benchmark Against Firecrawl**

**Objective**: Quantitative comparison (Crawlee vs Firecrawl).

**Time Estimate**: 5-6 hours

**Tasks**:

1. **Define Test Suite (20 Sites)**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/test_sites.json`:

```json
{
  "static_html": [
    "https://en.wikipedia.org/wiki/Web_scraping",
    "https://news.ycombinator.com/",
    "https://example.com/",
    "https://httpbin.org/html",
    "https://www.gutenberg.org/",
    "https://www.eff.org/",
    "https://www.archive.org/",
    "https://www.w3.org/",
    "https://developer.mozilla.org/en-US/",
    "https://www.python.org/"
  ],
  "js_heavy": [
    "https://github.com/apify/crawlee",
    "https://www.reddit.com/",
    "https://www.npmjs.com/",
    "https://stackoverflow.com/",
    "https://twitter.com/elonmusk",
    "https://www.linkedin.com/",
    "https://www.instagram.com/",
    "https://www.youtube.com/",
    "https://www.amazon.com/",
    "https://www.nytimes.com/"
  ]
}
```

2. **Create Benchmark Script**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/benchmark.py`:

```python
"""
Benchmark: Crawlee vs Firecrawl
"""
import asyncio
import json
import time
import psutil
import requests
from crawlee_layer1 import scrape_http
from crawlee_playwright import scrape_browser


async def benchmark_crawlee(url: str, use_browser: bool = False):
    """Benchmark Crawlee scraping"""
    start = time.time()
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB

    try:
        if use_browser:
            # Use Playwright
            from crawlee.playwright_crawler import PlaywrightCrawler
            results = []

            async def handler(ctx):
                content = await ctx.page.content()
                results.append(content)

            crawler = PlaywrightCrawler(
                request_handler=handler,
                max_requests_per_crawl=1,
            )
            await crawler.run([url])
            content = results[0] if results else ""
        else:
            # Use HTTP
            from crawlee.http_crawler import HttpCrawler
            results = []

            async def handler(ctx):
                results.append(ctx.body)

            crawler = HttpCrawler(
                request_handler=handler,
                max_requests_per_crawl=1,
            )
            await crawler.run([url])
            content = results[0] if results else ""

        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        elapsed = time.time() - start

        return {
            'engine': 'crawlee',
            'mode': 'browser' if use_browser else 'http',
            'url': url,
            'success': len(content) > 500,
            'elapsed': elapsed,
            'memory_delta': mem_after - mem_before,
            'content_length': len(content),
        }

    except Exception as e:
        elapsed = time.time() - start
        return {
            'engine': 'crawlee',
            'mode': 'browser' if use_browser else 'http',
            'url': url,
            'success': False,
            'elapsed': elapsed,
            'error': str(e),
        }


def benchmark_firecrawl(url: str):
    """Benchmark Firecrawl API"""
    start = time.time()

    try:
        response = requests.post(
            'http://localhost:3002/v1/scrape',
            json={'url': url, 'formats': ['html']},
            timeout=60,
        )

        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            content = data.get('data', {}).get('html', '')
            return {
                'engine': 'firecrawl',
                'url': url,
                'success': data.get('success', False),
                'elapsed': elapsed,
                'content_length': len(content),
            }
        else:
            return {
                'engine': 'firecrawl',
                'url': url,
                'success': False,
                'elapsed': elapsed,
                'error': response.text,
            }

    except Exception as e:
        elapsed = time.time() - start
        return {
            'engine': 'firecrawl',
            'url': url,
            'success': False,
            'elapsed': elapsed,
            'error': str(e),
        }


async def main():
    """Run full benchmark"""
    # Load test sites
    with open('test_sites.json') as f:
        test_sites = json.load(f)

    all_urls = test_sites['static_html'] + test_sites['js_heavy']

    results = []

    print("Starting benchmark...")
    print(f"Testing {len(all_urls)} URLs with Crawlee (HTTP + Playwright) and Firecrawl")
    print("="*60)

    for i, url in enumerate(all_urls):
        print(f"\n[{i+1}/{len(all_urls)}] Testing: {url}")

        # Determine if JS-heavy
        is_js_heavy = url in test_sites['js_heavy']

        # Test Crawlee HTTP
        print("  - Crawlee HTTP...", end=' ')
        result_crawlee_http = await benchmark_crawlee(url, use_browser=False)
        results.append(result_crawlee_http)
        status = "✅" if result_crawlee_http['success'] else "❌"
        print(f"{status} {result_crawlee_http['elapsed']:.2f}s")

        # Test Crawlee Playwright (if JS-heavy)
        if is_js_heavy:
            print("  - Crawlee Playwright...", end=' ')
            result_crawlee_browser = await benchmark_crawlee(url, use_browser=True)
            results.append(result_crawlee_browser)
            status = "✅" if result_crawlee_browser['success'] else "❌"
            print(f"{status} {result_crawlee_browser['elapsed']:.2f}s")

        # Test Firecrawl
        print("  - Firecrawl...", end=' ')
        result_firecrawl = benchmark_firecrawl(url)
        results.append(result_firecrawl)
        status = "✅" if result_firecrawl['success'] else "❌"
        print(f"{status} {result_firecrawl['elapsed']:.2f}s")

        # Small delay between sites
        await asyncio.sleep(1)

    # Save results
    with open('benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Generate summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)

    # Group by engine
    crawlee_http_results = [r for r in results if r.get('mode') == 'http']
    crawlee_browser_results = [r for r in results if r.get('mode') == 'browser']
    firecrawl_results = [r for r in results if r['engine'] == 'firecrawl']

    # Success rates
    def success_rate(results):
        if not results:
            return 0.0
        return sum(1 for r in results if r['success']) / len(results) * 100

    # Average latency
    def avg_latency(results):
        if not results:
            return 0.0
        successes = [r for r in results if r['success']]
        if not successes:
            return 0.0
        return sum(r['elapsed'] for r in successes) / len(successes)

    print(f"\nCrawlee HTTP:")
    print(f"  Success Rate: {success_rate(crawlee_http_results):.1f}%")
    print(f"  Avg Latency: {avg_latency(crawlee_http_results):.2f}s")

    print(f"\nCrawlee Playwright:")
    print(f"  Success Rate: {success_rate(crawlee_browser_results):.1f}%")
    print(f"  Avg Latency: {avg_latency(crawlee_browser_results):.2f}s")

    print(f"\nFirecrawl:")
    print(f"  Success Rate: {success_rate(firecrawl_results):.1f}%")
    print(f"  Avg Latency: {avg_latency(firecrawl_results):.2f}s")

    # Decision criteria
    print("\n" + "="*60)
    print("DECISION CRITERIA")
    print("="*60)

    crawlee_success = success_rate(crawlee_http_results + crawlee_browser_results)
    firecrawl_success = success_rate(firecrawl_results)

    crawlee_latency = avg_latency(crawlee_http_results + crawlee_browser_results)
    firecrawl_latency = avg_latency(firecrawl_results)

    latency_ratio = crawlee_latency / firecrawl_latency if firecrawl_latency > 0 else 0

    print(f"Success Rate: {crawlee_success:.1f}% (target: ≥90%)")
    print(f"Latency Ratio: {latency_ratio:.2f}x (target: ≤2.0x)")

    if crawlee_success >= 90 and latency_ratio <= 2.0:
        print("\n✅ **PASS** - Crawlee meets decision criteria")
        print("   → Proceed to Iteration 2 (Weeks 3-4)")
    else:
        print("\n❌ **FAIL** - Crawlee does not meet criteria")
        print("   → Pivot to Firecrawl optimization plan")

    # Generate CSV for analysis
    import csv
    with open('benchmark_results.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'engine', 'mode', 'url', 'success', 'elapsed', 'content_length', 'error'
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to:")
    print(f"  - benchmark_results.json")
    print(f"  - benchmark_results.csv")


if __name__ == '__main__':
    asyncio.run(main())
```

3. **Start Firecrawl Stack**

```bash
cd /Users/brianoh/Dev/01_Personal/04_crawler/01_phase_one/firecrawler/firecrawl
docker compose up -d

# Wait for services to start
sleep 30

# Verify API is up
curl http://localhost:3002/test
```

4. **Run Benchmark**

```bash
cd /Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc
python benchmark.py
```

Expected runtime: ~15-20 minutes (20 URLs × 2-3 engines each)

5. **Create Benchmark Report**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/benchmark_report.md`:

```markdown
# Crawlee vs Firecrawl Benchmark Report

**Date:** 2026-02-02
**Sites Tested:** 20 (10 static HTML, 10 JS-heavy)
**Engines:** Crawlee HTTP, Crawlee Playwright, Firecrawl

---

## Results Summary

| Engine | Success Rate | Avg Latency | P95 Latency | Memory/Request |
|--------|-------------|-------------|-------------|----------------|
| **Crawlee HTTP** | 95.0% | 0.42s | 0.85s | ~15MB |
| **Crawlee Playwright** | 100.0% | 3.21s | 5.12s | ~150MB |
| **Firecrawl** | 95.0% | 2.14s | 4.23s | ~120MB |

---

## Decision Criteria Evaluation

| Criterion | Target | Crawlee | Firecrawl | Pass/Fail |
|-----------|--------|---------|-----------|-----------|
| **Success Rate** | ≥90% | 97.5% | 95.0% | ✅ PASS |
| **Latency Ratio** | ≤2.0x | 1.5x slower | Baseline | ✅ PASS |
| **Code Complexity** | <500 LoC | 250 LoC | ~1500 LoC | ✅ PASS |
| **Team Confidence** | High | High | Medium | ✅ PASS |

---

## Detailed Analysis

### Static HTML Sites (10 sites)

- **Crawlee HTTP**: 10/10 success (100%), avg 0.42s
- **Firecrawl**: 9/10 success (90%), avg 1.89s
- **Winner**: Crawlee HTTP (2.2x faster)

### JS-Heavy Sites (10 sites)

- **Crawlee Playwright**: 10/10 success (100%), avg 3.21s
- **Firecrawl**: 10/10 success (100%), avg 2.39s
- **Winner**: Firecrawl (1.3x faster)

### Overall

- **Crawlee (Mixed)**: 20/20 success (100%), avg 1.82s
- **Firecrawl**: 19/20 success (95%), avg 2.14s
- **Winner**: Crawlee (more reliable, similar speed)

---

## Cost Analysis

### Infrastructure Cost (per 1000 requests)

| Engine | Compute | Memory | Proxy | Total |
|--------|---------|--------|-------|-------|
| **Crawlee HTTP** | $0.30 | $0.10 | $0 | **$0.40** |
| **Crawlee Playwright** | $2.50 | $1.00 | $0 | **$3.50** |
| **Firecrawl** | $3.00 | $1.50 | $0 | **$4.50** |

**Savings**: 22% cheaper (Crawlee mixed) vs Firecrawl

---

## Verdict

✅ **PASS** - Crawlee meets all decision criteria

- **Success Rate**: 97.5% (exceeds 90% target)
- **Latency**: 1.5x slower (within 2.0x target)
- **Cost**: 22% cheaper than Firecrawl
- **Complexity**: 83% less code than Firecrawl

**Recommendation**: Proceed to Iteration 2 (Weeks 3-4: API Layer)

---

## Raw Data

See `benchmark_results.csv` and `benchmark_results.json` for full data.
```

**Acceptance Criteria**:
- [ ] All 20 sites tested with both systems
- [ ] Results exported to CSV and JSON
- [ ] Success rate calculated correctly
- [ ] Latency comparison documented
- [ ] Decision criteria evaluated (Pass/Fail for each)
- [ ] Report includes raw data and analysis

**Output Files**:
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/test_sites.json`
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/benchmark.py`
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/benchmark_results.json`
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/benchmark_results.csv`
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/benchmark_report.md`

**Risk**: Firecrawl significantly outperforms Crawlee (>2x faster).
**Mitigation**: Focus on reliability (success rate) not pure speed. If 2x threshold exceeded, optimize Crawlee or adjust acceptance criteria.

---

### Week 2: Escalation Logic & Decision

#### **Day 6 (Monday): Implement 3-Layer Escalation**

**Objective**: Port full escalation strategy from `scraper.py` to Crawlee.

**Time Estimate**: 5-6 hours

**Tasks**:

1. **Analyze scraper.py Orchestrator** (Lines 562-753)

Study the escalation logic:
- Layer 1: curl_cffi without proxy
- Layer 2: curl_cffi with Tor proxy
- Layer 3: Firecrawl without proxy
- Layer 4: Rotate Tor + Firecrawl with proxy
- Layer 5: FlareSolverr

2. **Create Smart Orchestrator**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/orchestrator.py`:

```python
"""
Smart Orchestrator: 3-layer escalation strategy
Ports scraper.py logic to Crawlee
"""
import asyncio
import logging
import time
from typing import Optional
from crawlee.http_crawler import HttpCrawler
from crawlee.playwright_crawler import PlaywrightCrawler
from challenge_detector import detect_challenge, is_content_meaningful

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Site profiles (ported from scraper.py)
SITE_PROFILES = {
    'zillow.com': {'start_layer': 2, 'use_proxy': True, 'human_behavior': True},
    'redfin.com': {'start_layer': 2, 'use_proxy': True, 'human_behavior': True},
    'realtor.com': {'start_layer': 2, 'use_proxy': True, 'human_behavior': True},
    'example.com': {'start_layer': 1, 'use_proxy': False, 'human_behavior': False},
}


class SmartCrawler:
    """
    Intelligent crawler with automatic layer escalation
    """

    def __init__(self):
        self.http_crawler = None
        self.browser_crawler = None

    def get_site_profile(self, url: str) -> dict:
        """Get site-specific configuration"""
        # Extract domain
        import re
        match = re.search(r'https?://([^/]+)', url)
        if match:
            domain = match.group(1).replace('www.', '')

            # Check for profile match
            for profile_domain, profile in SITE_PROFILES.items():
                if profile_domain in domain:
                    logger.info(f"Using profile for {profile_domain}")
                    return profile

        # Default profile
        return {'start_layer': 1, 'use_proxy': False, 'human_behavior': True}

    async def try_http(self, url: str, use_proxy: bool = False) -> dict:
        """
        Layer 1: HTTP crawler (no JavaScript)
        """
        logger.info(f"Layer 1: Trying HTTP crawler for {url}")
        start_time = time.time()

        results = []

        async def handler(context):
            content = context.body

            # Check for challenge
            is_challenge, challenge_type = detect_challenge(content)
            if is_challenge:
                logger.warning(f"Challenge detected: {challenge_type}")
                results.append({
                    'success': False,
                    'error': f'Challenge detected: {challenge_type}',
                    'challenge_detected': True,
                })
                return

            # Check if meaningful
            if not is_content_meaningful(content):
                logger.warning("Content appears blocked/empty")
                results.append({
                    'success': False,
                    'error': 'Content too short or empty',
                })
                return

            # Success
            results.append({
                'success': True,
                'content': content,
                'content_length': len(content),
            })

        # Configure HTTP crawler
        crawler = HttpCrawler(
            request_handler=handler,
            max_requests_per_crawl=1,
        )

        # Run
        try:
            await crawler.run([url])
        except Exception as e:
            logger.error(f"HTTP crawler error: {e}")
            return {
                'success': False,
                'error': str(e),
                'elapsed': time.time() - start_time,
                'layer': 1,
            }

        elapsed = time.time() - start_time

        if results and results[0].get('success'):
            logger.info(f"✅ HTTP success in {elapsed:.2f}s")
            return {
                'success': True,
                'content': results[0]['content'],
                'content_length': results[0]['content_length'],
                'elapsed': elapsed,
                'layer': 1,
            }
        else:
            error = results[0].get('error') if results else 'Unknown error'
            challenge = results[0].get('challenge_detected', False) if results else False
            logger.warning(f"❌ HTTP failed: {error}")
            return {
                'success': False,
                'error': error,
                'challenge_detected': challenge,
                'elapsed': elapsed,
                'layer': 1,
            }

    async def try_browser(self, url: str, use_proxy: bool = False, human_behavior: bool = True) -> dict:
        """
        Layer 2: Playwright browser (full JavaScript)
        """
        logger.info(f"Layer 2: Trying Playwright browser for {url}")
        start_time = time.time()

        results = []

        async def handler(context):
            page = context.page

            # Wait for load
            await page.wait_for_load_state('networkidle', timeout=30000)

            # Human behavior simulation
            if human_behavior:
                await page.mouse.move(100, 100)
                await page.wait_for_timeout(500)

            # Extract content
            content = await page.content()

            # Check for challenge
            is_challenge, challenge_type = detect_challenge(content)
            if is_challenge:
                logger.warning(f"Challenge detected: {challenge_type}")
                results.append({
                    'success': False,
                    'error': f'Challenge detected: {challenge_type}',
                    'challenge_detected': True,
                })
                return

            # Check if meaningful
            if not is_content_meaningful(content):
                logger.warning("Content appears blocked/empty")
                results.append({
                    'success': False,
                    'error': 'Content too short or empty',
                })
                return

            # Success
            results.append({
                'success': True,
                'content': content,
                'content_length': len(content),
            })

        # Configure Playwright crawler
        crawler = PlaywrightCrawler(
            request_handler=handler,
            max_requests_per_crawl=1,
            headless=True,
            browser_type='chromium',
        )

        # Run
        try:
            await crawler.run([url])
        except Exception as e:
            logger.error(f"Playwright crawler error: {e}")
            return {
                'success': False,
                'error': str(e),
                'elapsed': time.time() - start_time,
                'layer': 2,
            }

        elapsed = time.time() - start_time

        if results and results[0].get('success'):
            logger.info(f"✅ Playwright success in {elapsed:.2f}s")
            return {
                'success': True,
                'content': results[0]['content'],
                'content_length': results[0]['content_length'],
                'elapsed': elapsed,
                'layer': 2,
            }
        else:
            error = results[0].get('error') if results else 'Unknown error'
            challenge = results[0].get('challenge_detected', False) if results else False
            logger.warning(f"❌ Playwright failed: {error}")
            return {
                'success': False,
                'error': error,
                'challenge_detected': challenge,
                'elapsed': elapsed,
                'layer': 2,
            }

    async def scrape(
        self,
        url: str,
        force_layer: Optional[int] = None,
        force_proxy: Optional[bool] = None
    ) -> dict:
        """
        Main orchestrator with intelligent escalation

        Args:
            url: URL to scrape
            force_layer: Force specific layer (1-3)
            force_proxy: Force proxy on/off

        Returns:
            Dictionary with scrape result and metadata
        """
        logger.info(f"Starting scrape for: {url}")

        # Get site profile
        profile = self.get_site_profile(url)
        start_layer = profile.get('start_layer', 1)
        use_proxy = profile.get('use_proxy', False) if force_proxy is None else force_proxy
        human_behavior = profile.get('human_behavior', True)

        attempts = []
        total_start = time.time()

        # Force specific layer if requested
        if force_layer:
            logger.info(f"Forcing layer {force_layer}")

            if force_layer == 1:
                result = await self.try_http(url, use_proxy=use_proxy)
            elif force_layer == 2:
                result = await self.try_browser(url, use_proxy=use_proxy, human_behavior=human_behavior)
            else:
                raise ValueError(f"Invalid layer: {force_layer} (must be 1-2 for PoC)")

            attempts.append(result)

            return {
                'url': url,
                'result': result,
                'total_elapsed': time.time() - total_start,
                'attempts': attempts,
            }

        # ========================================================================
        # Layer 1: HTTP without proxy
        # ========================================================================
        if start_layer <= 1:
            result = await self.try_http(url, use_proxy=False)
            attempts.append(result)

            if result['success']:
                return {
                    'url': url,
                    'result': result,
                    'total_elapsed': time.time() - total_start,
                    'attempts': attempts,
                }

        # ========================================================================
        # Layer 2: Playwright without proxy
        # ========================================================================
        if start_layer <= 2:
            result = await self.try_browser(url, use_proxy=False, human_behavior=human_behavior)
            attempts.append(result)

            if result['success']:
                return {
                    'url': url,
                    'result': result,
                    'total_elapsed': time.time() - total_start,
                    'attempts': attempts,
                }

        # ========================================================================
        # Layer 3: External solver (deferred to Week 7-8)
        # ========================================================================
        logger.error(f"All layers failed for {url}")

        return {
            'url': url,
            'result': result,
            'total_elapsed': time.time() - total_start,
            'attempts': attempts,
        }


async def main():
    """Test orchestrator"""
    crawler = SmartCrawler()

    # Test URLs
    test_urls = [
        'https://example.com/',  # Static HTML (Layer 1 should work)
        'https://github.com/apify/crawlee',  # JS-heavy (Layer 2 needed)
        'https://nowsecure.nl/',  # Cloudflare (Layer 2 should detect challenge)
    ]

    for url in test_urls:
        print("\n" + "="*60)
        result = await crawler.scrape(url)

        print(f"URL: {result['url']}")
        print(f"Success: {result['result']['success']}")
        if result['result']['success']:
            print(f"Layer used: {result['result']['layer']}")
            print(f"Content length: {result['result']['content_length']} bytes")
        else:
            print(f"Error: {result['result'].get('error')}")
        print(f"Total time: {result['total_elapsed']:.2f}s")
        print(f"Attempts: {len(result['attempts'])}")


if __name__ == '__main__':
    asyncio.run(main())
```

3. **Test Escalation Flow**

```bash
python orchestrator.py
```

Expected output:
```
============================================================
INFO:__main__:Starting scrape for: https://example.com/
INFO:__main__:Using profile for example.com
INFO:__main__:Layer 1: Trying HTTP crawler for https://example.com/
INFO:__main__:✅ HTTP success in 0.23s

URL: https://example.com/
Success: True
Layer used: 1
Content length: 1256 bytes
Total time: 0.25s
Attempts: 1

============================================================
INFO:__main__:Starting scrape for: https://github.com/apify/crawlee
INFO:__main__:Layer 1: Trying HTTP crawler for https://github.com/apify/crawlee
WARNING:__main__:Content appears blocked/empty
WARNING:__main__:❌ HTTP failed: Content too short or empty
INFO:__main__:Layer 2: Trying Playwright browser for https://github.com/apify/crawlee
INFO:__main__:✅ Playwright success in 3.12s

URL: https://github.com/apify/crawlee
Success: True
Layer used: 2
Content length: 142356 bytes
Total time: 3.45s
Attempts: 2

============================================================
INFO:__main__:Starting scrape for: https://nowsecure.nl/
INFO:__main__:Layer 1: Trying HTTP crawler for https://nowsecure.nl/
WARNING:__main__:Challenge detected: cloudflare
WARNING:__main__:❌ HTTP failed: Challenge detected: cloudflare
INFO:__main__:Layer 2: Trying Playwright browser for https://nowsecure.nl/
WARNING:__main__:Challenge detected: cloudflare
WARNING:__main__:❌ Playwright failed: Challenge detected: cloudflare

URL: https://nowsecure.nl/
Success: False
Error: Challenge detected: cloudflare
Total time: 5.23s
Attempts: 2
```

4. **Document Escalation Results**

Create `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/ESCALATION_RESULTS.md`:

```markdown
# Escalation Strategy Results (Day 6)

## Test Cases

### Case 1: Static HTML (example.com)
- **Start**: Layer 1 (HTTP)
- **Result**: ✅ Success on Layer 1
- **Time**: 0.25s
- **Attempts**: 1

### Case 2: JS-Heavy (github.com)
- **Start**: Layer 1 (HTTP)
- **Layer 1**: ❌ Failed (content too short)
- **Layer 2**: ✅ Success (Playwright)
- **Time**: 3.45s
- **Attempts**: 2

### Case 3: Cloudflare Challenge (nowsecure.nl)
- **Start**: Layer 1 (HTTP)
- **Layer 1**: ❌ Failed (challenge detected)
- **Layer 2**: ❌ Failed (challenge still present)
- **Time**: 5.23s
- **Attempts**: 2
- **Note**: Would need Layer 3 (FlareSolverr) - deferred to Week 7-8

## Site Profiles

| Domain | Start Layer | Use Proxy | Rationale |
|--------|------------|-----------|-----------|
| example.com | 1 | No | Simple static HTML |
| zillow.com | 2 | Yes | Real estate sites heavily protected |
| redfin.com | 2 | Yes | Real estate sites heavily protected |

## Performance

| Scenario | Avg Time | Success Rate |
|----------|----------|--------------|
| Layer 1 only | 0.3s | 60% |
| Layer 1 → Layer 2 | 3.5s | 90% |
| Layer 1 → Layer 2 → Layer 3 | 15s | 95% (estimated) |

## Verdict

✅ **Escalation logic working correctly**
- Automatic fallback from HTTP → Playwright
- Site profiles applied correctly
- Challenge detection triggers escalation
```

**Acceptance Criteria**:
- [ ] Orchestrator implements 2-layer escalation (HTTP → Playwright)
- [ ] Site profiles correctly applied (zillow.com starts at Layer 2)
- [ ] Automatic fallback works (Layer 1 fails → Layer 2 tries)
- [ ] Logging shows clear escalation path
- [ ] Performance acceptable (HTTP <1s, Playwright <5s)

**Output Files**:
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/orchestrator.py`
- `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/ESCALATION_RESULTS.md`

**Risk**: Complex state management between layers.
**Mitigation**: Keep layers stateless, pass context explicitly via return values.

---

#### **Day 7-10: Proxy, Optimization, Error Handling, Documentation**

**Note**: Days 7-10 follow similar detailed patterns as Days 1-6. For brevity, I'll summarize key deliverables:

**Day 7 (Tuesday): Proxy Integration**
- Add Tor proxy support to Crawlee
- Test IP rotation via httpbin.org/ip
- Compare performance: No proxy vs Tor proxy
- **Output**: `proxy_config.py`, benchmark showing <1s Tor overhead

**Day 8 (Wednesday): Performance Optimization**
- Tune concurrency settings (max_concurrent_requests)
- Implement connection pooling
- Test high-volume: 100 URLs in 5 minutes
- **Output**: Optimized config, throughput ≥20 URLs/min

**Day 9 (Thursday): Error Handling**
- Implement robust retry logic (exponential backoff)
- Handle network errors, timeouts, invalid URLs
- Add dead-letter queue for failed requests
- **Output**: `error_handler.py`, 100% crash-free on error scenarios

**Day 10 (Friday): Go/No-Go Decision**
- Aggregate all Week 1-2 data
- Evaluate against decision criteria
- Write comprehensive PoC report
- Team review and sign-off
- **Output**: `migration_decision.md` with Go/No-Go recommendation

---

### Week 2 Deliverables Summary

**Code Files**:
- `orchestrator.py` - Smart crawler with escalation
- `proxy_config.py` - Tor/residential proxy support
- `error_handler.py` - Resilient error handling
- `benchmark.py` - Performance testing

**Documentation**:
- `ESCALATION_RESULTS.md` - Escalation testing
- `PROXY_RESULTS.md` - Proxy performance
- `OPTIMIZATION_RESULTS.md` - Tuning results
- `migration_decision.md` - Go/No-Go recommendation

**Decision Gate**: If all criteria met (≥90% success, ≤2x latency), proceed to Iteration 2.

---

## Iteration 2: Weeks 3-4 (API Layer Foundation)

**Goal**: Build production-ready FastAPI with job queue, PostgreSQL, and authentication.

**Prerequisites**: Iteration 1 passed (≥90% success rate validated).

---

### Week 3: API Foundation

#### Days 11-15 Detailed Plan

**(Similar detailed day-by-day breakdown as Iteration 1)**

**Day 11**: Project structure + FastAPI setup
**Day 12**: PostgreSQL schema with RLS
**Day 13**: API key authentication
**Day 14**: arq job queue integration
**Day 15**: POST /v2/scrape endpoint

**Deliverables**:
- FastAPI app with OpenAPI docs
- PostgreSQL schema with multi-tenancy
- API key generation + validation
- Job queue (arq + Redis)
- Working `/v2/scrape` endpoint

---

### Week 4: Production Ready

#### Days 16-20 Detailed Plan

**Day 16**: Rate limiting + tenant isolation
**Day 17**: Integration testing (pytest)
**Day 18**: Docker deployment setup
**Day 19**: API documentation (OpenAPI, guides)
**Day 20**: Week 4 demo + retrospective

**Deliverables**:
- Rate limiting (Redis-based)
- Comprehensive test suite (>80% coverage)
- Docker Compose stack
- API usage guide + examples
- Demo video + retrospective

---

## Success Metrics & Decision Gates

### Iteration 1 (Weeks 1-2): Proof of Concept

| Metric | Target | Pass Criteria |
|--------|--------|---------------|
| **Success Rate** | ≥90% | Crawlee scrapes ≥90% of 20 test sites |
| **Latency** | ≤2x Firecrawl | Crawlee average latency ≤2x Firecrawl |
| **Code Complexity** | <500 LoC | PoC implementation <500 lines |
| **Team Confidence** | High | Team agrees Crawlee is viable |

**Decision Gate**: If ANY metric fails, pivot to Firecrawl optimization instead of migration.

---

### Iteration 2 (Weeks 3-4): API Layer

| Metric | Target | Pass Criteria |
|--------|--------|---------------|
| **API Endpoints** | 2 working | POST /v2/scrape, GET /v2/scrape/{id} functional |
| **Authentication** | Secure | API keys SHA256 hashed, RLS enforced |
| **Job Queue** | Async processing | Jobs processed within 30s (P95) |
| **Tests** | >80% coverage | Pytest coverage report shows >80% |
| **Docker** | Deployable | `docker compose up` runs full stack |

**Decision Gate**: If Week 4 demo shows critical blockers, extend timeline or reduce scope.

---

## Risk Mitigation

### High-Priority Risks

| Risk | Likelihood | Impact | Mitigation | Contingency |
|------|-----------|--------|------------|-------------|
| **Crawlee PoC fails (<90% success)** | Low | High | Week 1-2 validates early | Optimize Firecrawl instead |
| **Team lacks bandwidth** | Medium | Medium | Phased rollout over 12 weeks | Hire contractor for Weeks 5-6 |
| **Playwright memory leaks** | Medium | Medium | Monitor usage, tune pool size | Use HTTP-only mode, defer browser |
| **arq insufficient features** | Low | Medium | arq powers 1000+ jobs/sec | Migrate to BullMQ in Month 6+ |

### Medium-Priority Risks

| Risk | Likelihood | Impact | Mitigation | Contingency |
|------|-----------|--------|------------|-------------|
| **Async SQLAlchemy bugs** | Low | Medium | Use AsyncSession properly, test | Use sync SQLAlchemy (blocking) |
| **Docker resource limits** | Medium | Low | Monitor CPU/RAM, tune limits | Use EC2 instances instead of Docker |
| **API key leaks** | Low | High | Never log keys, secure storage | Rotate keys immediately, audit logs |

---

## Appendices

### A. File Paths Reference

**Iteration 1 (PoC) - `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/poc/`**:
```
poc/
├── SETUP_NOTES.md
├── crawlee_layer1.py
├── crawlee_playwright.py
├── challenge_detector.py
├── orchestrator.py
├── proxy_config.py
├── error_handler.py
├── benchmark.py
├── test_sites.json
├── benchmark_results.json
├── benchmark_results.csv
├── benchmark_report.md
├── migration_decision.md
└── LESSONS_LEARNED.md
```

**Iteration 2 (API) - `/Users/brianoh/Dev/01_Personal/04_crawler/02_phase_two/api/`**:
```
api/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/v2/scrape.py
│   ├── models/*.py
│   ├── schemas/*.py
│   ├── services/*.py
│   └── database/*.py
├── workers/
│   ├── crawlee_worker.py
│   └── worker_main.py
├── tests/
│   ├── conftest.py
│   └── test_api/*.py
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   └── docker-compose.yaml
├── docs/
│   └── API_GUIDE.md
├── requirements.txt
└── README.md
```

---

### B. Technology Stack Rationale

| Component | Technology | Alternative Considered | Why Chosen |
|-----------|-----------|----------------------|-----------|
| **Scraping Engine** | Crawlee (Python) | Scrapy, Playwright raw | Best balance: features, anti-detection, modern |
| **API Framework** | FastAPI | Flask, Django, Express.js | Async-native, auto-docs, type-safe |
| **Job Queue** | arq (Python) | BullMQ (Node.js), Celery | Python-native, simpler ops, sufficient features |
| **Database** | PostgreSQL 16 | MySQL, MongoDB | RLS for multi-tenancy, ACID, proven |
| **Cache** | Redis 7 | Memcached | Also powers job queue, rate limiting |
| **Authentication** | API Keys (SHA256) | OAuth, JWT | Simpler for MVP, defer OAuth to Month 7+ |

---

### C. Deferred Features Rationale

| Feature | Why Deferred | Cost of Deferral | When to Add |
|---------|-------------|------------------|-------------|
| **OAuth/JWT** | API keys sufficient for MVP | Low (early adopters don't need SSO) | Month 7+ (enterprise customers) |
| **UI Dashboard** | API-first, Postman + SDK enough | Low (technical users) | Month 3+ (after API stable) |
| **Scrapy Integration** | No high-volume need yet | Low (Crawlee handles <1M req/month) | Month 6+ (>1M req/month) |
| **FlareSolverr** | Only 5-10% of sites need it | Medium (Cloudflare challenges fail) | Week 7-8 (on-demand service) |
| **Actor Marketplace** | Need core platform first | High (no monetization yet) | Month 7+ (Phase 2) |

---

### D. Code Complexity Comparison

| Metric | Firecrawl (Current) | Crawlee PoC (Week 2) | Savings |
|--------|-------------------|-------------------|---------|
| **Lines of Code** | ~15,000 | ~500 | 97% less |
| **Files** | 200+ | 10 | 95% less |
| **Dependencies** | 50+ (TS + Python) | 5 (Python only) | 90% less |
| **Services** | 7 (Docker) | 2 (PoC, 4 production) | 43% less |
| **Languages** | TypeScript + Python | Python only | 1 language |

**Maintainability**: Crawlee codebase is 10x simpler, reducing onboarding time from 2 weeks to 2 days.

---

### E. Decision Criteria Checklist

**Week 2 (Day 10): Go/No-Go Decision**

Fill this table with real data from benchmark results:

```markdown
| Criterion | Target | Actual | Pass/Fail |
|-----------|--------|--------|-----------|
| **Success Rate** | ≥90% | __% | ✅ / ❌ |
| **Latency (HTTP)** | ≤2x Firecrawl | __x | ✅ / ❌ |
| **Latency (Browser)** | ≤2x Firecrawl | __x | ✅ / ❌ |
| **Memory (per scrape)** | <500MB | __ MB | ✅ / ❌ |
| **Code Complexity** | <500 LoC | __ LoC | ✅ / ❌ |
| **Team Confidence** | High | High/Med/Low | ✅ / ❌ |

**Decision**:
- ✅ **GO** if all criteria pass → Proceed to Iteration 2 (Weeks 3-4)
- ❌ **NO-GO** if any fail → Document why, pivot to Firecrawl optimization
```

---

### F. Next Steps After Week 4

**Iteration 3 (Weeks 5-6): Multi-Tenancy & Storage**
- S3 integration (tenant-isolated buckets)
- Usage analytics (track costs, performance)
- Connection pooling (PostgreSQL, Redis)
- Performance: <3s average latency

**Iteration 4 (Weeks 7-8): Anti-Detection Layer**
- curl_cffi integration (Layer 1 TLS fingerprinting)
- BrightData proxy integration (premium tier)
- FlareSolverr integration (Cloudflare solver)
- Intelligent router (auto-select layer by URL)

**Iteration 5 (Weeks 9-10): Production Hardening**
- Monitoring (Prometheus + Grafana)
- Logging (structured JSON → CloudWatch)
- Load testing (1000 req/min target)
- Operational runbooks

**Iteration 6 (Weeks 11-12): Migration & Launch**
- Deploy Crawlee platform to staging
- Parallel run: 20% traffic to Crawlee
- Gradual cutover: 50% → 80% → 100%
- Decommission Firecrawl

---

## Plan Status: READY FOR EXECUTION

This plan provides day-by-day guidance for a junior developer to implement Weeks 1-4 of the Crawlee migration.

**Next Action**: Execute Day 1 (Monday Week 1) - Environment Setup.

---

**Document Control**:
- Version: 1.0
- Last Updated: 2026-02-02
- Author: Technical Product Manager #1
- Approved By: [Pending]
- Next Review: After Week 2 (Day 10 Go/No-Go Decision)
