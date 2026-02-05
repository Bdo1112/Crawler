# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web scraping platform built on [Firecrawl](https://firecrawl.dev) with a custom 3-layer anti-detection system. The project is organized in phases:

- **01_phase_one/**: Firecrawl fork with anti-detection enhancements (Tor proxy, FlareSolverr, Patchright stealth browser)
- **02_phase_two/**: Future platform architecture (Apify-like actor/task system)

## Repository Structure

```
04_crawler/
├── 01_phase_one/
│   ├── firecrawler/firecrawl/    # Modified Firecrawl monorepo
│   │   ├── apps/api/             # Main API server (TypeScript/Express)
│   │   ├── apps/playwright-service-ts/  # Stealth browser service (Patchright)
│   │   ├── apps/js-sdk/          # JavaScript SDK
│   │   ├── apps/python-sdk/      # Python SDK
│   │   └── docker-compose.yaml   # Full stack with Tor + FlareSolverr
│   └── scripts/
│       └── scraper.py            # 3-layer Python orchestrator
└── 02_phase_two/                 # Platform architecture planning
```

## Development Commands

### Firecrawl API (apps/api/)

```bash
cd 01_phase_one/firecrawler/firecrawl/apps/api

# Install dependencies
pnpm install

# Development (requires Redis + PostgreSQL running)
pnpm start              # Start API + workers
pnpm workers            # Start queue workers only
pnpm nuq-worker         # Start NUQ-based worker

# Testing
pnpm harness jest path/to/test.ts    # Run tests with auto-managed server
pnpm test:snips                       # Run snippet tests
pnpm test:local-no-auth               # Run no-auth E2E tests

# Linting
pnpm knip               # Find unused code
pnpm format             # Prettier formatting
```

### Docker Full Stack

```bash
cd 01_phase_one/firecrawler/firecrawl

# Start all services (API, Playwright, Redis, Postgres, Tor, FlareSolverr)
docker compose up -d --build

# Verify services
docker compose ps
curl http://localhost:3002/test                    # API health
curl -x http://localhost:8118 https://httpbin.org/ip  # Tor proxy
curl http://localhost:8191/health                  # FlareSolverr
```

### Python Orchestrator

```bash
cd 01_phase_one/scripts

pip install -r requirements.txt

# Scrape with automatic layer escalation
python scraper.py "https://example.com"
python scraper.py "https://example.com" -o output.json
python scraper.py "https://protected-site.com" --layer 3  # Force FlareSolverr
```

## Architecture

### 3-Layer Scraping Strategy

The system escalates through layers by cost/capability:

1. **Layer 1: curl_cffi** (~50ms) - TLS fingerprint impersonation, no JS
2. **Layer 2: Firecrawl/Patchright** (~3-5s) - Full stealth browser with JS
3. **Layer 3: FlareSolverr** (~10-30s) - Dedicated Cloudflare challenge solver

Each layer can optionally route through Tor for IP rotation.

### Firecrawl API Flow

```
POST /v2/scrape → API Server → Queue Worker → Engine Selector → Playwright Service → Browser → Response
```

Key engine selection: `apps/api/src/scraper/scrapeURL/engines/index.ts`

### Anti-Detection Stack

| Service | Port | Purpose |
|---------|------|---------|
| firecrawl-api | 3002 | Main API |
| playwright-service | 3000 (internal) | Patchright stealth browser |
| tor-proxy | 8118 | Rotating Tor exit nodes |
| flaresolverr | 8191 | Cloudflare solver |

## Testing Conventions (Firecrawl API)

When modifying the API:

1. **Write E2E tests first** in `apps/api/src/__tests__/snips/`
   - Happy path + failure paths
   - Use `scrapeTimeout` from `./lib` for timeouts

2. **Gate tests by environment**:
   ```typescript
   if (process.env.TEST_SUITE_SELF_HOSTED) {
     // Skip Fire-engine only tests
   }
   if (!process.env.OPENAI_API_KEY && !process.env.OLLAMA_BASE_URL) {
     // Skip AI-dependent tests
   }
   ```

3. **Run with harness**: `pnpm harness jest path/to/test.ts`

4. Let CI run the full test suite.

## Key Files

### Firecrawl Core
- `apps/api/src/index.ts` - Server entry point
- `apps/api/src/routes/v2.ts` - V2 API routes
- `apps/api/src/services/queue-worker.ts` - Job processing
- `apps/api/src/scraper/WebScraper/index.ts` - Core scraping logic

### Anti-Detection
- `apps/playwright-service-ts/api.ts` - Stealth browser (Patchright + fingerprint spoofing + behavior simulation)
- `docker-compose.yaml` - Stack with Tor + FlareSolverr services
- `scripts/scraper.py` - Python orchestrator with layer escalation

## Environment Variables

Required in `apps/api/.env`:
```
PORT=3002
HOST=0.0.0.0
REDIS_URL=redis://localhost:6379
REDIS_RATE_LIMIT_URL=redis://localhost:6379
NUQ_DATABASE_URL=postgres://postgres:postgres@localhost:5433/postgres
USE_DB_AUTHENTICATION=false
BLOCK_MEDIA=true
```

Optional:
```
OPENAI_API_KEY=         # For LLM extraction features
PLAYWRIGHT_MICROSERVICE_URL=http://playwright-service:3000/scrape
TEST_API_KEY=           # For authenticated tests
```

## API Endpoints (V2)

- `POST /v2/scrape` - Scrape single URL
- `POST /v2/crawl` - Start crawl job
- `GET /v2/crawl/{id}` - Check crawl status
- `POST /v2/map` - List all URLs on a site
- `POST /v2/extract` - LLM-powered structured extraction
- `POST /v2/batch/scrape` - Batch scrape multiple URLs
