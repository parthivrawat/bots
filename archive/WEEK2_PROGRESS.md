# Week 2 — Scheduled Automation Bot — Progress Report

**Date:** 2026-09-12  
**Status:** 🚧 **IN PROGRESS** (Core infrastructure complete, commands pending)

---

## Overview

Week 2 extends Week 1's platform-agnostic bot with **scheduled background jobs**. The goal is to demonstrate that bots can be *proactive* (scheduled tasks) not just *reactive* (user commands).

**Key insight**: The Week 1 core is completely reused — the scheduler is just another "adapter" that triggers commands programmatically.

---

## Completed ✅

### 1. Project Structure ✅
- ✅ Copied Week 1 codebase as foundation
- ✅ Created `src/bot/jobs/` directory for scheduled job definitions
- ✅ Created `src/bot/fetchers/` directory for API clients
- ✅ Updated `pyproject.toml` with new dependencies (APScheduler, aiohttp)

### 2. Database Schema ✅
- ✅ Created `002_jobs.sql` migration with 4 new tables:
  - `scheduled_jobs` — Job registry (name, type, schedule, enabled status)
  - `job_runs` — Execution history (status, result, errors)
  - `job_deliveries` — Audit trail of message deliveries
  - `price_alerts` — User-created price alerts

### 3. Data Layer ✅
- ✅ **JobRepository** (`db/repositories/job_repo.py`):
  - CRUD for scheduled jobs
  - Job run tracking
  - Delivery logging
  - Price alert management
- ✅ **JobService** (`services/job_service.py`):
  - Business logic wrapper around repository
  - Validation for alerts (condition, threshold)

### 4. API Fetchers ✅
- ✅ **WeatherFetcher** (`fetchers/weather_api.py`):
  - Uses wttr.in (free, no API key required)
  - Returns temperature, condition, humidity, wind
  - Includes weather emoji mapping
- ✅ **CryptoFetcher** (`fetchers/crypto_api.py`):
  - Uses CoinGecko API (free tier, no key)
  - Supports BTC, ETH, and 6 other major coins
  - Returns current price in USD

### 5. Job Scheduler ✅
- ✅ **JobScheduler** (`jobs/scheduler.py`):
  - Wraps APScheduler for async job execution
  - Persists jobs to database
  - Tracks execution in `job_runs` table
  - Supports enable/disable/trigger operations
  - Graceful shutdown (waits for running jobs)

### 6. Job Implementations ✅
- ✅ **Daily Weather Job** (`jobs/weather.py`):
  - Runs daily at 9:00 AM UTC (cron trigger)
  - Sends weather to users with `weather_report=on` setting
  - Fetches city from user's `city` setting (default: London)
  
- ✅ **Price Alert Job** (`jobs/price_alert.py`):
  - Runs every 15 minutes (interval trigger)
  - Checks active price alerts
  - Triggers when threshold crossed (above/below)
  - Marks alerts as triggered after delivery
  
- ✅ **Health Check Job** (`jobs/health_check.py`):
  - Runs every 5 minutes (interval trigger)
  - Checks database connectivity
  - Alerts admins if unhealthy

### 7. Enhanced User Repository ✅
- ✅ Added `get_setting(user_id, key, default)` method
- ✅ Added `get_users_with_setting(key, value)` method
- ✅ Added `get_admins()` method

### 8. Enhanced User Service ✅
- ✅ Exposed new repository methods
- ✅ Ready for subscription/alert commands

---

## In Progress 🚧

### 9. User Commands (In Progress)
Need to implement:
- [ ] `/subscribe weather` — Enable daily weather reports
- [ ] `/unsubscribe weather` — Disable weather reports
- [ ] `/alert BTC above 50000` — Create price alert
- [ ] `/alerts` — List user's active alerts
- [ ] `/alert cancel <id>` — Cancel an alert

**Files to create**:
- `src/bot/handlers/subscribe.py`
- `src/bot/handlers/alerts.py`

---

## Pending 📋

### 10. Admin Commands
- [ ] `/admin jobs` — List all scheduled jobs + status
- [ ] `/admin job <name> enable` — Enable a job
- [ ] `/admin job <name> disable` — Disable a job
- [ ] `/admin job <name> trigger` — Run job immediately
- [ ] `/admin job <name> history` — Show last 10 runs

**Files to create**:
- `src/bot/handlers/admin_jobs.py`

### 11. Application Wiring
- [ ] Update `app.py` to include:
  - JobRepository in composition root
  - JobService in ServiceRegistry
  - JobScheduler initialization
  - `send_to_user()` helper method
- [ ] Update `main.py` to:
  - Start scheduler alongside adapters
  - Graceful shutdown (stop scheduler first)

### 12. Testing
- [ ] Unit tests for scheduler (`tests/test_scheduler.py`)
- [ ] Unit tests for jobs (`tests/test_jobs.py`)
- [ ] Unit tests for fetchers (`tests/test_fetchers.py`)
- [ ] Unit tests for new handlers
- [ ] Integration test: trigger job manually, verify delivery

### 13. Eval Framework Integration
- [ ] Create `evals/cases/week2_jobs.json` with 8+ cases
- [ ] Create `evals/week2_adapter.py` bridge
- [ ] Test cases for:
  - Subscribe/unsubscribe commands
  - Alert creation/listing/cancellation
  - Admin job control
  - Job execution logging

### 14. Documentation
- [ ] Update `README.md` with:
  - Week 2 architecture diagram
  - Job examples
  - New commands
  - Setup instructions
  - Deployment notes
- [ ] Create `.env.example` additions
- [ ] Update Dockerfile if needed

### 15. Deployment
- [ ] Test locally with real APIs
- [ ] Deploy to Railway/Fly.io
- [ ] Soak test: verify jobs run on schedule for 24h
- [ ] Monitor job execution logs

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    Scheduler (APScheduler)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Daily Weather│  │ Price Alerts │  │ Health Check │         │
│  │  (cron: 9am) │  │(interval:15m)│  │(interval: 5m)│         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┴─────────────────┘                  │
│                            ▼                                    │
│                   Job Executor (async)                          │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│    Fetch API          Process Data      Generate Report        │
│   (Weather/Crypto)    (check alerts)    (format message)       │
│         │                  │                  │                │
│         └──────────────────┴──────────────────┘                │
│                            ▼                                    │
│                   send_to_user() helper                         │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│    Telegram           Discord             Slack                │
│    (Week 1 adapters — completely reused)                       │
└─────────────────────────────────────────────────────────────────┘
                            ▼
                   Week 1 Core (unchanged)
```

---

## Files Created

### Data Layer
- ✅ `src/bot/db/migrations/002_jobs.sql` (2,227 bytes)
- ✅ `src/bot/db/repositories/job_repo.py` (8,459 bytes)
- ✅ `src/bot/services/job_service.py` (3,827 bytes)

### API Fetchers
- ✅ `src/bot/fetchers/__init__.py` (172 bytes)
- ✅ `src/bot/fetchers/weather_api.py` (3,027 bytes)
- ✅ `src/bot/fetchers/crypto_api.py` (4,323 bytes)

### Scheduler & Jobs
- ✅ `src/bot/jobs/__init__.py` (94 bytes)
- ✅ `src/bot/jobs/scheduler.py` (7,006 bytes)
- ✅ `src/bot/jobs/weather.py` (2,464 bytes)
- ✅ `src/bot/jobs/price_alert.py` (3,269 bytes)
- ✅ `src/bot/jobs/health_check.py` (2,246 bytes)

### Configuration
- ✅ `pyproject.toml` (updated with APScheduler, aiohttp)

### Documentation
- ✅ `WEEK2_PLAN.md` (23,065 bytes) — Comprehensive plan
- ✅ `WEEK2_PROGRESS.md` (this file)

**Total new code**: ~36,000 bytes (~1,000 lines)

---

## Next Steps (Priority Order)

1. **Implement user commands** (subscribe, alerts)
   - Create `handlers/subscribe.py`
   - Create `handlers/alerts.py`
   - Register with router

2. **Implement admin commands** (job control)
   - Create `handlers/admin_jobs.py`
   - Register with router

3. **Wire everything in app.py**
   - Add JobRepository, JobService
   - Initialize JobScheduler
   - Add `send_to_user()` helper

4. **Update main.py**
   - Start scheduler
   - Graceful shutdown

5. **Test locally**
   - Run scheduler
   - Trigger jobs manually
   - Verify deliveries

6. **Write tests**
   - Unit tests for all new code
   - Integration tests

7. **Eval framework**
   - Create eval cases
   - Bridge adapter

8. **Documentation**
   - README updates
   - Deployment guide

9. **Deploy & soak test**
   - Deploy to production
   - Monitor for 24h

---

## Estimated Completion

- **Core infrastructure**: ✅ 100% complete
- **Commands**: 🚧 0% complete (next priority)
- **Application wiring**: 📋 0% pending
- **Testing**: 📋 0% pending
- **Documentation**: 📋 0% pending
- **Deployment**: 📋 0% pending

**Overall progress**: ~40% complete

**Estimated time to completion**: 4-6 hours of focused work

---

## Key Learnings So Far

1. **Reusability works**: Week 1's core is completely unchanged — scheduler plugs in seamlessly
2. **APScheduler is simple**: Cron and interval triggers cover most use cases
3. **Free APIs exist**: wttr.in and CoinGecko provide real data without API keys
4. **Job persistence matters**: Storing jobs in DB enables admin control and audit trail
5. **Async context managers**: Clean pattern for API clients (auto-close sessions)

---

## Risks & Mitigations

| Risk | Status | Mitigation |
|------|--------|------------|
| API rate limits | ⚠️ Monitor | Cache responses, respect limits |
| Job overlap | ✅ Handled | `max_instances=1` in APScheduler |
| Scheduler state loss | ✅ Handled | Jobs persisted to DB, re-registered on startup |
| Time zones | ✅ Handled | All times in UTC, user can set timezone setting |

---

**Last updated**: 2026-09-12 18:00 UTC  
**Next session**: Implement user commands (subscribe, alerts)
