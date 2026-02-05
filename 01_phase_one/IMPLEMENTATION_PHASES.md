# Anti-Detection Crawling Workflow — Implementation Phases

## Overview

**Problem**: Firecrawl runs with no proxy, no stealth, default Playwright fingerprints. Sites block by IP and detect the bot.
**Goal**: Give a URL, get all data back reliably via a 3-layer escalation strategy.

**Expected Success Rates (post-implementation)**:

| Site Type | Success Rate | Notes |
|---|---|---|
| Unprotected (blogs, docs, news) | ~100% | Layer 1 direct, no proxy needed |
| Basic Cloudflare (JS challenge) | 70-85% | Tor exit nodes are flagged by CF — expect some failures |
| Advanced Cloudflare (managed rules) | 40-55% | FlareSolverr helps but Tor IPs limit success |
| PerimeterX/Zillow | 10-25% | $0-25 budget limits this; residential proxies would raise it |

> **Note on Tor limitations**: Tor exit node IPs are publicly listed and specifically flagged by Cloudflare, PerimeterX, and most commercial anti-bot services. The success rates above reflect this reality. Residential proxy services ($20-50/mo) would significantly improve rates but are outside the stated budget.

---

## Phase 1: Architecture Mapping

**Purpose**: Understand the full service architecture, data flow, config touch points, and current anti-detection gaps before writing any code.

**Agents**: `Explore` (x3 in parallel), then `architect-reviewer` (x1)

### Subtask 1.1 — Map service architecture and data flow

**What**: Trace a scrape request from `POST /v2/scrape` through the API server, into the queue worker, to the playwright-service, and back. Document every service hop and config variable involved.

**Key files to examine**:
- `firecrawler/firecrawl/docker-compose.yaml` (service definitions, networking, env passthrough)
- `firecrawler/firecrawl/apps/api/src/scraper/scrapeURL/engines/index.ts` (engine selection logic)
- `firecrawler/firecrawl/apps/api/src/scraper/scrapeURL/engines/playwright/index.ts` (how API calls playwright-service)
- `firecrawler/firecrawl/apps/playwright-service-ts/api.ts` (the actual browser automation)

**Deliverable**: A written data flow diagram (text-based) showing: HTTP request -> API -> Queue -> Engine selector -> Playwright-service -> Browser -> Response.

**How to test**: Review the diagram against actual code; confirm no missing hops.

### Subtask 1.2 — Audit current anti-detection capabilities

**What**: Document exactly what anti-detection exists today vs. what's missing. Check every env var, browser arg, and header being set.

**Key files to examine**:
- `firecrawler/firecrawl/apps/playwright-service-ts/api.ts` lines 88-146 (browser args, context creation, proxy config)
- `firecrawler/firecrawl/.env` (what's actually set)
- `firecrawler/firecrawl/apps/api/.env.example` (what's available but unused)

**Deliverable**: Gap analysis table: Feature | Current State | Target State.

**How to test**: Cross-reference with known detection vectors (TLS fingerprint, navigator.webdriver, WebGL, plugins, viewport uniformity).

### Subtask 1.3 — Validate Patchright compatibility

**What**: Confirm Patchright is a true drop-in replacement for the specific Playwright version used (`^1.55.1`). Check npm registry for matching patchright version. Verify API surface compatibility (chromium.launch, browser.newContext, page.goto, addInitScript, route).

**How to test**: `npm view patchright versions` -- confirm 1.55.x exists. Read Patchright docs/changelog for any breaking differences from Playwright.

**Rollback plan**: If Patchright is incompatible, revert `package.json` to `"playwright": "^1.55.1"`, revert import in `api.ts`, and revert Dockerfile install command. The stealth init scripts (Phase 3.4-3.5) still work with vanilla Playwright — only `navigator.webdriver` removal is lost.

### Execution Sequence

```
[PARALLEL] Subtask 1.1 (Explore) + Subtask 1.2 (Explore) + Subtask 1.3 (Explore)
     |       -- all three are independent research tasks
     v
[SEQUENTIAL] Architecture review (architect-reviewer agent) -- validates all findings
```

---

## Phase 2: Docker Infrastructure — Proxy & Challenge Solver

**Purpose**: Add IP rotation (Tor) and Cloudflare solving (FlareSolverr) to the Docker stack. After this phase, proxy and challenge-solving infrastructure is available but **not forced globally** — the orchestrator decides per-request whether to use proxy.

**Agents**: `devops-engineer` (x1)

### Subtask 2.1 — Add Tor rotating proxy service

**What**: Add a `tor-proxy` service to `docker-compose.yaml` using `dperson/torproxy` image. Must join `backend` network so playwright-service can reach it at `tor-proxy:8118`. Also expose port 8118 to the host so the Python orchestrator can route curl_cffi through it.

**File**: `firecrawler/firecrawl/docker-compose.yaml`

**Details**:
- Image: `dperson/torproxy`
- Environment: `LOCATION=US` (prefer US exit nodes)
- Network: `backend`
- Port mapping: `8118:8118` (needed by Python orchestrator on host)
- Expose Tor control port `9051` internally (for NEWNYM circuit rotation signals)
- Add resource limits and logging config matching existing services

**How to test**:
```bash
docker compose up -d tor-proxy
# From host (via exposed port):
curl -x http://localhost:8118 https://httpbin.org/ip
# Should return a non-local IP (Tor exit node)
# From inside Docker network:
docker compose exec api curl -x http://tor-proxy:8118 https://httpbin.org/ip
# Should also return a Tor exit IP
```

### Subtask 2.2 — Add FlareSolverr service

**What**: Add `flaresolverr` service to `docker-compose.yaml`. FlareSolverr runs its own headless browser that can solve Cloudflare JS challenges. Expose port 8191 for the Python orchestrator to call directly. Configure it to route through Tor to avoid leaking the host IP.

**File**: `firecrawler/firecrawl/docker-compose.yaml`

**Details**:
- Image: `ghcr.io/flaresolverr/flaresolverr:latest`
- Environment: `LOG_LEVEL=info`, `TZ=America/New_York`
- Proxy config: set `PROXY_URL=http://tor-proxy:8118` so FlareSolverr's browser routes through Tor (prevents real IP leak)
- Network: `backend`
- Port mapping: `8191:8191` (accessible from host for Python script)
- `depends_on: tor-proxy` (needs proxy available before starting)
- Resource note: adds ~500MB-1GB RAM usage

**How to test**:
```bash
docker compose up -d flaresolverr
curl http://localhost:8191/health
# Should return: {"status":"ok"}
```

### Subtask 2.3 — Configure environment variables

**What**: Set `BLOCK_MEDIA` in `.env`. **Do NOT set `PROXY_SERVER` globally** — proxy usage will be controlled per-request by the Python orchestrator to avoid penalizing easy targets with Tor latency and IP reputation.

**File**: `firecrawler/firecrawl/.env`

**Details**:
Add this line:
```env
BLOCK_MEDIA=true
```

`BLOCK_MEDIA=true` reduces bandwidth and detection surface by not loading images/video. This is safe to apply globally.

**Why not set PROXY_SERVER globally**: Tor exit nodes are publicly listed and flagged by most anti-bot services. Forcing all traffic through Tor hurts success rates on unprotected sites (unnecessary latency, potential blocks). Instead, the Python orchestrator will pass `proxy` in the Firecrawl API request body only when needed for protected sites.

**How to test**:
```bash
docker compose up -d
# Verify media blocking is active:
docker compose logs playwright-service | grep -i block
# Verify NO global proxy is set (intentional):
docker compose exec playwright-service env | grep PROXY
# Should show empty or unset PROXY_SERVER
```

### Execution Sequence

```
[PARALLEL] Subtask 2.1 (tor-proxy) + Subtask 2.2 (flaresolverr) -- independent services
     |
     v
[SEQUENTIAL] Subtask 2.3 (.env config) -- needs services defined first
     |
     v
[SEQUENTIAL] docker compose up -d --build -- full stack restart to verify
```

---

## Phase 3: Playwright Stealth — Patchright + Fingerprint Hardening + Behavior

**Purpose**: Replace Playwright with Patchright, add fingerprint spoofing, and add human-like behavior. This is a single phase because all changes target the same service (`playwright-service-ts`) and the same core file (`api.ts`). After this phase, the browser no longer identifies as automated and looks like a real user's Chrome.

**Agents**: `typescript-pro` (x1)

### Subtask 3.1 — Swap Playwright dependency for Patchright

**What**: Change the npm dependency from `playwright` to `patchright` in package.json. Patchright publishes versions matching Playwright, so the version constraint stays the same.

**File**: `firecrawler/firecrawl/apps/playwright-service-ts/package.json`

**Change**: `"playwright": "^1.55.1"` -> `"patchright": "^1.55.1"`

**How to test**:
```bash
cd firecrawler/firecrawl/apps/playwright-service-ts
npm install  # Should resolve without errors
npm ls patchright  # Should show installed version
```

### Subtask 3.2 — Update Dockerfile browser install

**What**: The Dockerfile runs `npx playwright install chromium --with-deps` to download browser binaries. Change this to use Patchright's patched Chromium.

**File**: `firecrawler/firecrawl/apps/playwright-service-ts/Dockerfile`

**Change**: Line 12: `npx playwright install chromium --with-deps` -> `npx patchright install chromium --with-deps`

**How to test**:
```bash
docker compose build playwright-service
# Build should complete without errors
# Patchright should install its patched Chromium binary
```

### Subtask 3.3 — Update TypeScript import and browser launch args

**What**: Change the import in `api.ts` from `playwright` to `patchright`. Also clean up browser launch args -- remove flags that are automation telltales, add anti-detection flag.

**File**: `firecrawler/firecrawl/apps/playwright-service-ts/api.ts`

**Changes**:

1. Line 3 -- Change import:
   ```typescript
   // FROM:
   import { chromium, Browser, ... } from 'playwright';
   // TO:
   import { chromium, Browser, ... } from 'patchright';
   ```

2. Lines 91-99 -- Update browser launch args:
   ```typescript
   args: [
     '--no-sandbox',
     '--disable-setuid-sandbox',
     '--disable-dev-shm-usage',
     '--disable-blink-features=AutomationControlled',
     '--disable-infobars',
     '--window-size=1920,1080',
     '--start-maximized',
   ]
   ```
   Removed: `--disable-accelerated-2d-canvas`, `--no-first-run`, `--no-zygote`, `--disable-gpu` (these are automation-telltale flags that detectors look for).

**How to test**:
```bash
docker compose build playwright-service && docker compose up -d
# Scrape bot.sannysoft.com through Firecrawl API:
curl -X POST http://localhost:3002/v2/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://bot.sannysoft.com/","formats":["html"]}'
# Check returned HTML: navigator.webdriver should NOT be "true"
```

### Subtask 3.4 — Randomize browser context with correlated UA/viewport

**What**: Enhance `createContext()` in api.ts to randomize viewport, locale, timezone, color scheme, and device scale factor. **Viewport and user-agent must be correlated** — a mobile UA must not be paired with a desktop viewport.

**File**: `firecrawler/firecrawl/apps/playwright-service-ts/api.ts` -- `createContext` function (lines 103-146)

**Details**:
```typescript
// Desktop profiles — viewport and scale factor are correlated
const desktopProfiles = [
  { viewport: { width: 1366, height: 768 }, deviceScaleFactor: 1 },
  { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 },
  { viewport: { width: 1536, height: 864 }, deviceScaleFactor: 1 },
  { viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 },
  { viewport: { width: 2560, height: 1440 }, deviceScaleFactor: 2 },
];
const profile = desktopProfiles[Math.floor(Math.random() * desktopProfiles.length)];

// Filter the random UA to desktop-only to match the viewport
// (the existing `user-agents` package already supports this)

// Add to contextOptions:
viewport: profile.viewport,
deviceScaleFactor: profile.deviceScaleFactor,
locale: 'en-US',
timezoneId: 'America/New_York',
colorScheme: 'light',
hasTouch: false,
javaScriptEnabled: true,
```

**How to test**: Make 5 scrape requests to `https://httpbin.org/headers` -- viewport/UA should vary between requests but always be consistent (desktop UA + desktop viewport).

### Subtask 3.5 — Add stealth init scripts

**What**: Use `newContext.addInitScript()` to inject JavaScript that spoofs fingerprint-checked APIs before any page loads. This runs before the target site's JavaScript.

**File**: `firecrawler/firecrawl/apps/playwright-service-ts/api.ts` -- inside `createContext()`, after `browser.newContext()` but before the route handlers

**Details** -- add after `const newContext = await browser.newContext(contextOptions);`:
```typescript
await newContext.addInitScript(() => {
  // Spoof WebGL vendor/renderer (sites fingerprint GPU info)
  const getParameter = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
    return getParameter.call(this, parameter);
  };

  // Realistic plugins array (headless Chrome has empty plugins)
  Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
  });

  // Realistic languages
  Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
  });

  // Chrome runtime object (missing in automation)
  if (!(window as any).chrome) {
    (window as any).chrome = { runtime: {} };
  }
});
```

**How to test**:
```bash
# Scrape the bot detection test page:
curl -X POST http://localhost:3002/v2/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://bot.sannysoft.com/","formats":["html"]}'
# In returned HTML, check:
#   - WebGL Vendor: should show "Intel Inc."
#   - Plugins: should NOT be empty
#   - Chrome: should show as present
```

### Subtask 3.6 — Add configurable human-like behavior simulation

**What**: After `page.goto()` but before extracting content, simulate minimal human behavior -- random mouse movement and page scroll. Make this **opt-in via a request parameter** so it can be skipped for known-unprotected sites (avoids adding 0.5-1.2s latency to every scrape).

**File**: `firecrawler/firecrawl/apps/playwright-service-ts/api.ts` -- `scrapePage` function (lines 163-195)

**Details** -- insert after `const response = await page.goto(...)` and before the `waitAfterLoad` check:
```typescript
// Simulate human behavior if requested (adds ~0.5-1.2s per scrape)
if (params.humanBehavior !== false) {
  try {
    await page.mouse.move(
      100 + Math.random() * 500,
      100 + Math.random() * 400
    );
    await page.waitForTimeout(300 + Math.random() * 700);
    await page.evaluate(() => window.scrollBy(0, 300 + Math.random() * 200));
    await page.waitForTimeout(200 + Math.random() * 500);
  } catch (e) {
    // Non-critical, don't fail the scrape
  }
}
```

Default: **enabled** (most scrapes benefit from it). The Python orchestrator can disable it for known-easy targets by passing `humanBehavior: false` in the request body.

**How to test**: Scrape `https://example.com` with and without `humanBehavior: false` in the POST body. Verify content returns correctly in both cases, and the version without behavior sim is ~1s faster.

### Execution Sequence

```
[SEQUENTIAL] Subtask 3.1 (package.json) -- must be first
     |
     v
[PARALLEL] Subtask 3.2 (Dockerfile) + Subtask 3.3 (api.ts import + args)
     |
     v
[SEQUENTIAL] Subtask 3.4 (correlated context randomization)
     |
     v
[SEQUENTIAL] Subtask 3.5 (stealth init scripts)
     |
     v
[SEQUENTIAL] Subtask 3.6 (behavior sim)
     |
     v
[SEQUENTIAL] docker compose build playwright-service -- full rebuild + test against bot.sannysoft.com
```

---

## Phase 4: Python Orchestrator — Core & Challenge Detection

**Purpose**: Create the foundation of the Python scraper script with challenge page detection and content validation. After this phase, the script can call Firecrawl and detect when it gets blocked.

**Agents**: `python-pro` (x1)

> **Note**: The existing `results/request.py` is a prototype. The new orchestrator goes in `scripts/scraper.py` to separate source code from output data. `results/` remains for scrape output only.

### Subtask 4.1 — Create scraper.py with core utilities

**What**: Create `scripts/scraper.py` with the `ScrapeResult` dataclass, challenge detection, and content validation. These are needed by all layers.

**File**: `scripts/scraper.py` (new file)

**Details**:
- `ScrapeResult` dataclass: success, content, method, status_code, error, elapsed
- `is_challenge_page(html)` -- detection signatures:
  - Cloudflare: "cf-browser-verification", "Just a moment...", "Checking your browser", "ray ID"
  - PerimeterX: "px-captcha", "_px", "perimeterx"
  - DataDome: "datadome", "dd_challenge"
  - Generic: "Access denied", "bot detection", "Attention Required"
- `is_content_meaningful(html, min_length=500)` -- strip HTML tags, collapse whitespace, check length
- `rotate_tor_circuit()` -- send NEWNYM signal to Tor control port (localhost:9051) to get a fresh exit node

**How to test**:
```python
# Challenge detection:
assert is_challenge_page("<div>Just a moment...</div>") == True
assert is_challenge_page("<div>Hello world article content</div>") == False

# Content validation:
assert is_content_meaningful("<html><body><p>Hello</p></body></html>", min_length=3) == True
assert is_content_meaningful("<html><body></body></html>", min_length=10) == False

# Tor rotation:
# rotate_tor_circuit() -- should complete without error (verify with two httpbin.org/ip calls)
```

### Subtask 4.2 — Layer 1: curl_cffi with TLS impersonation (fast, cheap)

**What**: Implement `try_curl_cffi(url, use_proxy=False)` as **Layer 1** — the fastest, cheapest layer. Uses `curl_cffi` to make HTTP requests impersonating Chrome's TLS fingerprint. No JS rendering. Optionally routes through Tor.

**File**: `scripts/scraper.py`

**Details**:
- Impersonate `chrome131` TLS fingerprint
- Set realistic browser headers (Accept, Accept-Language, Sec-Fetch-*, etc.)
- `use_proxy` param: when True, route through `http://localhost:8118` (Tor)
- Use challenge detection + content validation on response
- Gracefully handle missing `curl_cffi` dependency (print warning, skip layer)

**Why Layer 1**: curl_cffi is ~50ms per request vs. ~3-5s for a full browser. For sites that don't use JS challenges (most blogs, docs, APIs), this is sufficient and much faster. No point launching a full browser if a simple HTTP request works.

**How to test**:
```bash
pip install curl_cffi
python -c "
from scraper import try_curl_cffi
result = try_curl_cffi('https://httpbin.org/headers')
print(result.success, result.content[:200])
"
# Headers should show Chrome-like TLS fingerprint
```

### Subtask 4.3 — Layer 2: Firecrawl API (full stealth browser)

**What**: Implement `try_firecrawl(url, use_proxy=False, human_behavior=True)` as **Layer 2** — full browser rendering with all stealth hardening from Phase 3. This handles sites that require JS execution.

**File**: `scripts/scraper.py`

**Details**:
- POST to `localhost:3002/v2/scrape` with formats=[markdown, html], timeout=60000, waitFor=3000
- When `use_proxy=True`, include `proxy: "http://tor-proxy:8118"` in the request body (Firecrawl supports per-request proxy)
- Pass `humanBehavior` param through to control behavior simulation
- Use challenge detection + content validation on response
- Handle HTTP errors, API errors, and timeouts gracefully

**How to test**:
```bash
# Ensure Firecrawl is running
python -c "
from scraper import try_firecrawl
result = try_firecrawl('https://example.com')
print(result.success, result.method, len(result.content))
"
# Should print: True firecrawl <content length>
```

### Execution Sequence

```
[SEQUENTIAL] Subtask 4.1 (core utilities) -- must exist first
     |
     v
[PARALLEL] Subtask 4.2 (curl_cffi Layer 1) + Subtask 4.3 (Firecrawl Layer 2)
     |       -- both are independent scraping functions that use 4.1 utilities
     v
[SEQUENTIAL] Wire challenge detection + content validation into both layers' response handling
```

---

## Phase 5: Python Orchestrator — FlareSolverr Layer & Escalation Logic

**Purpose**: Add Layer 3 (FlareSolverr) and build the orchestrator that chains all three layers with smart escalation and retry logic.

**Agents**: `python-pro` (x1)

### Subtask 5.1 — Layer 3: FlareSolverr integration (challenge solver)

**What**: Implement `try_flaresolverr(url)` as **Layer 3** — the last resort for Cloudflare JS challenges. FlareSolverr runs its own browser, solves challenges, and returns the page content. Already configured to route through Tor (Phase 2.2).

**File**: `scripts/scraper.py`

**Details**:
- POST to `http://localhost:8191/v1` with `{"cmd": "request.get", "url": url, "maxTimeout": 60000}`
- Extract solution HTML from response
- Validate content meaningfulness
- Handle FlareSolverr-specific error responses

**How to test**:
```bash
# Ensure FlareSolverr is running
docker compose ps flaresolverr
python -c "
from scraper import try_flaresolverr
result = try_flaresolverr('https://nowsecure.nl/')
print(result.success, result.method, len(result.content))
"
```

### Subtask 5.2 — Orchestrator with smart escalation + retry + CLI

**What**: Build the main `scrape(url)` function that chains Layer 1 -> 2 -> 3 with escalation and Tor circuit rotation between retries. Add CLI argument parsing.

**File**: `scripts/scraper.py`

**Details — Escalation strategy**:
```
1. Try curl_cffi WITHOUT proxy (fastest path for unprotected sites)
     |
     v -- if challenge page or blocked:
2. Try curl_cffi WITH Tor proxy (different IP, same TLS impersonation)
     |
     v -- if challenge page or needs JS rendering:
3. Try Firecrawl WITHOUT proxy (full browser, no proxy overhead)
     |
     v -- if blocked by IP:
4. Rotate Tor circuit, try Firecrawl WITH proxy (full browser + new IP)
     |
     v -- if Cloudflare JS challenge detected:
5. Try FlareSolverr (dedicated challenge solver, already routes through Tor)
```

**Details — CLI**:
- Positional `url` arg
- `--output/-o` for output file (JSON)
- `--quiet/-q` to suppress progress
- `--layer` to force a specific layer (skip escalation, useful for testing)
- `--proxy/--no-proxy` to force proxy on/off

**Details — Output**:
- JSON: url, timestamp, result metadata (method, layer, elapsed, attempts), content
- Log each attempt with method name, elapsed time, proxy status, and error

**Details — Site profiles** (optional optimization):
```python
SITE_PROFILES = {
    "zillow.com": {"start_layer": 2, "use_proxy": True},
    "example.com": {"start_layer": 1, "use_proxy": False, "human_behavior": False},
}
```
Known-hard sites skip straight to higher layers. Known-easy sites skip proxy and behavior sim.

**How to test**:
```bash
# Full end-to-end:
python scripts/scraper.py "https://example.com" -o results/test_basic.json
python scripts/scraper.py "https://nowsecure.nl/" -o results/test_cf.json
python scripts/scraper.py "https://www.zillow.com/" -o results/test_zillow.json
# Check output JSON structure and escalation logging
# Verify easy sites resolve at Layer 1 without proxy
```

### Execution Sequence

```
[SEQUENTIAL] Subtask 5.1 (FlareSolverr layer)
     |
     v
[SEQUENTIAL] Subtask 5.2 (orchestrator + CLI) -- needs all layers defined
```

---

## Phase 6: Requirements & Integration Testing

**Purpose**: Create the requirements file, install dependencies, and run end-to-end tests across a variety of target sites. Document real-world success rates.

**Agents**: `test-automator` (x1), `code-reviewer` (x1 in parallel)

### Subtask 6.1 — Create requirements.txt and install

**What**: Create `scripts/requirements.txt` with Python dependencies, install them, verify imports work.

**File**: `scripts/requirements.txt` (new file)

**Content**:
```
requests>=2.31.0
curl_cffi>=0.7.0
```

(Only two external dependencies. `json`, `re`, `argparse`, `dataclasses`, `time`, `socket` are all stdlib.)

**How to test**:
```bash
pip install -r scripts/requirements.txt
python -c "import requests; from curl_cffi import requests as cr; print('OK')"
```

### Subtask 6.2 — End-to-end integration tests

**What**: Run the full pipeline against a suite of test URLs covering different protection levels. Document actual success rates.

**Test matrix**:

| URL | Protection | Expected Layer | Pass Criteria |
|---|---|---|---|
| `https://example.com` | None | Layer 1 (curl_cffi, no proxy) | Content > 500 chars, no challenge, < 1s |
| `https://httpbin.org/headers` | None | Layer 1 (curl_cffi) | Returns JSON with headers |
| `https://bot.sannysoft.com/` | None | Layer 2 (Firecrawl) | HTML shows stealth markers passing |
| `https://nowsecure.nl/` | Cloudflare | Layer 2-3 | Real page content, not challenge |
| `https://www.dogdrip.net/` | Korean anti-bot | Layer 1-2 | Korean content returned |
| `https://www.zillow.com/` | PerimeterX | Any | Document actual result (may fail) |

**How to test**: Run each URL and record which layer succeeded, elapsed time, proxy used, and content length. Compare against expected success rates in Overview table.

### Subtask 6.3 — Code review and cleanup

**What**: Review all modified files for security issues, error handling gaps, and code quality. Ensure no credentials are hardcoded, no unnecessary dependencies added.

**Files to review**:
- `firecrawler/firecrawl/docker-compose.yaml`
- `firecrawler/firecrawl/.env`
- `firecrawler/firecrawl/apps/playwright-service-ts/api.ts`
- `firecrawler/firecrawl/apps/playwright-service-ts/package.json`
- `firecrawler/firecrawl/apps/playwright-service-ts/Dockerfile`
- `scripts/scraper.py`
- `scripts/requirements.txt`

**Review checklist**:
- [ ] No hardcoded credentials or API keys
- [ ] Tor control port authentication configured (not open)
- [ ] FlareSolverr not exposed beyond localhost
- [ ] Error handling covers all network failure modes
- [ ] Timeouts set on all HTTP requests (no hanging)
- [ ] No sensitive data logged to stdout

**How to test**: Agent reviews each file and produces findings. Any critical issues block completion.

### Execution Sequence

```
[SEQUENTIAL] Subtask 6.1 (requirements install)
     |
     v
[SEQUENTIAL] Full stack rebuild: docker compose up -d --build
     |
     v
[PARALLEL] Subtask 6.2 (integration tests) + Subtask 6.3 (code review)
```

---

## Full Execution Dependency Graph

```
Phase 1: Architecture Mapping
  [1.1 + 1.2 + 1.3 all parallel] -> [architect review]
     |
     v
Phase 2: Docker Infrastructure          Phase 3: Patchright + Stealth (merged)
  [2.1 + 2.2 parallel] -> [2.3]            [3.1] -> [3.2 + 3.3 parallel] -> [3.4] -> [3.5] -> [3.6]
     |                                        |
     +------------------+---------------------+
                         |
                         v
                 Phase 4: Python Core + Layers 1-2
                   [4.1] -> [4.2 + 4.3 parallel]
                         |
                         v
                 Phase 5: FlareSolverr + Orchestrator
                   [5.1] -> [5.2]
                         |
                         v
                 Phase 6: Testing & Review
                   [6.1] -> [rebuild] -> [6.2 + 6.3 parallel]
```

**Note**: Phase 2 and Phase 3 can run in parallel (they modify different files). Phase 4-5 need Phase 2 done (Docker services must be running for testing). Phase 4-5 also need Phase 3 done (stealth browser must be built).

---

## Agent Assignment Summary

| Phase | Agent(s) | Why |
|---|---|---|
| Phase 1 | `Explore` (x3), `architect-reviewer` (x1) | Codebase exploration + architecture validation |
| Phase 2 | `devops-engineer` (x1) | Docker Compose, networking, env config |
| Phase 3 | `typescript-pro` (x1) | TypeScript — Patchright swap, stealth scripts, fingerprint hardening, behavior sim |
| Phase 4 | `python-pro` (x1) | Python — core utilities, curl_cffi Layer 1, Firecrawl Layer 2 |
| Phase 5 | `python-pro` (x1) | Python — FlareSolverr Layer 3, orchestrator, CLI |
| Phase 6 | `test-automator` (x1), `code-reviewer` (x1) | E2E testing + security/quality review |

---

## Files Modified (Complete)

| File | Phase | Change |
|---|---|---|
| `firecrawler/firecrawl/docker-compose.yaml` | 2 | Add tor-proxy (with port 8118 exposed) + flaresolverr (with Tor proxy config) services |
| `firecrawler/firecrawl/.env` | 2 | Add BLOCK_MEDIA (no global PROXY_SERVER — controlled per-request) |
| `firecrawler/firecrawl/apps/playwright-service-ts/package.json` | 3 | playwright -> patchright |
| `firecrawler/firecrawl/apps/playwright-service-ts/Dockerfile` | 3 | playwright -> patchright install command |
| `firecrawler/firecrawl/apps/playwright-service-ts/api.ts` | 3 | Import swap, launch args, correlated context randomization, stealth scripts, configurable behavior sim |
| `scripts/scraper.py` | 4, 5 | New file — 3-layer orchestrator with smart escalation, retry, Tor rotation, CLI |
| `scripts/requirements.txt` | 6 | New file — Python dependencies |

---

## Key Changes from v1 of This Plan

| Issue | v1 | v2 (this version) |
|---|---|---|
| Escalation order | Firecrawl → curl_cffi → FlareSolverr | curl_cffi → Firecrawl → FlareSolverr (escalate by cost/capability) |
| Proxy strategy | Global `PROXY_SERVER` forces all traffic through Tor | Per-request proxy — easy sites skip Tor entirely |
| Tor port mapping | No host port exposed | Port 8118 exposed (Python orchestrator needs it) |
| FlareSolverr proxy | Unspecified — would leak host IP | Configured to route through Tor |
| Tor circuit rotation | Not mentioned | `rotate_tor_circuit()` between retry attempts |
| UA/viewport correlation | Independent randomization | Correlated desktop profiles (UA matches viewport) |
| Behavior simulation | Always on, ~1s added to every scrape | Configurable via `humanBehavior` param, skippable for easy targets |
| Phase 3 + Phase 4 | Separate phases (same file, same concern) | Merged into single Phase 3 |
| Subtask 1.3 dependency | Sequential after 1.1/1.2 | Parallel with 1.1/1.2 (independent research) |
| Scraper location | `results/scraper.py` (mixed with output) | `scripts/scraper.py` (source code separate from output) |
| Success rate estimates | Optimistic (80-90% for basic CF) | Adjusted for Tor IP reputation reality (70-85%) |
| Patchright rollback | Not documented | Rollback plan in Subtask 1.3 |
