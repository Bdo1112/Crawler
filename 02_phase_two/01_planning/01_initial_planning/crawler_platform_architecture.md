# Crawler Platform Architecture

Building an Apify-like platform. This document outlines the core components and considerations.

---

## Core Components

### 1. Crawler Engine
The actual crawling runtime. Options:
- Build on Crawlee/Scrapy
- Or your own using Playwright/Puppeteer

### 2. Actor/Task System
A way to define reusable crawlers ("actors" in Apify terms):
- Standardized input/output schema
- Configuration (start URLs, depth, filters, etc.)
- Versioning
- Packaging (Docker containers or similar)

### 3. Job Orchestration
- Queue management (pending, running, completed, failed jobs)
- Scheduling (cron-like, or event-triggered)
- Concurrency control (how many crawls run at once)
- Retry logic

### 4. Storage Layer
- **Input storage**: configs, credentials
- **Output storage**: crawled data (JSON, files, screenshots)
- **Request queue**: URLs to crawl, deduplication
- **Key-value store**: session data, cookies, state

### 5. Proxy Management
- Proxy pool (residential, datacenter, Tor)
- Rotation strategies
- Health checking (remove dead proxies)
- Per-site proxy assignment

### 6. Anti-Bot / Browser Management
- Browser pool (reuse browsers, manage memory)
- Fingerprint rotation
- CAPTCHA solving integration
- Challenge detection

### 7. Marketplace (if you want that)
- Actor registry (upload, discover, fork)
- User accounts / auth
- Usage metering / billing (if commercial)
- Reviews, documentation

### 8. UI / API
- Dashboard: view jobs, results, logs
- API: trigger crawls programmatically
- Log streaming / real-time status

### 9. Infrastructure
- Container orchestration (Kubernetes, Docker Swarm)
- Auto-scaling based on queue depth
- Resource limits per job
- Isolation between jobs

---

## Rough Architecture

```
┌─────────────────────────────────────────────────────┐
│                      UI / API                        │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│                   Job Scheduler                      │
│            (cron, triggers, queue)                   │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│                  Worker Pool                         │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│    │ Worker  │  │ Worker  │  │ Worker  │  ...      │
│    │(Crawlee)│  │(Crawlee)│  │(Crawlee)│           │
│    └─────────┘  └─────────┘  └─────────┘           │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│              Shared Services                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │  Proxy   │ │ Browser  │ │ Storage  │            │
│  │  Pool    │ │   Pool   │ │  (S3/DB) │            │
│  └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────────┘
```

---

## Recommended Build Order

### Phase 1: Foundation
1. **Actor definition format** — JSON/YAML schema for defining a crawler
2. **Simple job runner** — takes an actor + input, runs it, stores output
3. **Storage** — local filesystem first, S3 later

### Phase 2: Orchestration
4. **Basic API** — trigger a job, get status, get results
5. **Queue** — Redis or PostgreSQL for job queue
6. **Scheduling** — cron-like scheduling for recurring jobs

### Phase 3: Scale & Reliability
7. **Worker pool** — multiple workers processing jobs
8. **Proxy management** — rotation, health checks
9. **Browser pool** — reuse browsers, manage memory

### Phase 4: Platform Features
10. **UI Dashboard** — view jobs, results, logs
11. **Marketplace** — actor registry, discovery
12. **User management** — accounts, permissions, usage tracking

---

## Technology Options

| Component | Options |
|-----------|---------|
| Crawler engine | Crawlee (Node), Scrapy (Python), Playwright |
| Job queue | Redis, PostgreSQL, RabbitMQ, BullMQ |
| Storage | Local FS → S3/MinIO → PostgreSQL for metadata |
| API | FastAPI (Python), Express/Fastify (Node) |
| Container orchestration | Docker Compose → Kubernetes |
| UI | React, Next.js, Vue |

---

## Open Questions

- [ ] What language/stack for the platform itself? (Node to match Crawlee, or Python?)
- [ ] Self-hosted only, or cloud offering eventually?
- [ ] Single-tenant or multi-tenant?
- [ ] What's the MVP scope?
