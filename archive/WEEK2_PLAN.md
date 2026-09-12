# Week 2 — Scheduled Automation Bot

> **Phase 1, Project 2** — No AI. Goal: master background jobs, scheduling,
> queues, and the "observe → process → act" pattern. Bots don't have to chat.
>
> **Stack**: Python 3.11+, `APScheduler` (cron-like scheduling), `aiohttp`
> (API fetching), reuse Week 1's bot core, SQLite, `pytest`.

---

## 1. Architecture

### Design decision: Scheduled jobs as bot commands + background workers

**Why**: Week 2 teaches that bots can be *proactive* (scheduled tasks) not just
*reactive* (user commands). The same core from Week 1 handles both — scheduled
jobs are just commands triggered by a scheduler instead of a user.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Scheduler (APScheduler)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Daily Report │  │ Price Alert  │  │ Health Check │  ...    │
│  │  (cron: 9am) │  │ (interval:1h)│  │ (interval:5m)│         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┴─────────────────┘                  │
│                            ▼                                    │
│                   Job Executor (async)                          │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│    Fetch API          Process Data      Generate Report        │
│   (aiohttp)           (business logic)   (format, store)       │
│         │                  │                  │                │
│         └──────────────────┴──────────────────┘                │
│                            ▼                                    │
│                   Delivery (reuse Week 1 adapters)              │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│    Telegram           Discord             Email                │
└─────────────────────────────────────────────────────────────────┘
                            ▼
                   Week 1 Core (router, services, DB)
```

**Key insight**: The Week 1 core is *unchanged* — we add a scheduler layer
above it that triggers commands programmatically. This proves the architecture
is truly platform-agnostic: "platforms" include cron schedules, not just chat.

**Alternatives considered**
- *Separate codebase for scheduled tasks*: duplicates business logic, rejected.
- *Celery/RQ for job queue*: overkill for Week 2 — APScheduler is simpler and
  teaches the concepts. Migrate to Celery in production phases if needed.

### Job types

| Type | Trigger | Example |
|------|---------|---------|
| **Cron** | Time-based (daily, hourly, etc.) | Daily weather report at 9am |
| **Interval** | Fixed delay (every N minutes) | Price check every 15 minutes |
| **One-shot** | Single future execution | Reminder in 2 hours |
| **Event-driven** | External trigger (webhook, file watch) | Process uploaded file |

Week 2 focuses on **cron** and **interval** jobs. One-shot and event-driven
are bonus if time permits.

---

## 2. Project layout

```
week2-scheduled-bot/
├── pyproject.toml
├── .env.example
├── README.md
├── src/
│   └── bot/
│       ├── core/              # REUSED from Week 1 (symlink or copy)
│       ├── handlers/          # REUSED + new scheduled job handlers
│       ├── services/          # REUSED + new job services
│       ├── db/                # REUSED + new tables for jobs
│       │   ├── migrations/002_jobs.sql
│       │   └── repositories/
│       │       └── job_repo.py
│       ├── adapters/          # REUSED (Telegram, Discord, etc.)
│       ├── jobs/              # NEW: scheduled job definitions
│       │   ├── __init__.py
│       │   ├── scheduler.py   # APScheduler setup + job registry
│       │   ├── weather.py     # Example: daily weather report
│       │   ├── price_alert.py # Example: crypto price monitor
│       │   └── health_check.py# Example: system health
│       ├── fetchers/          # NEW: API clients
│       │   ├── weather_api.py
│       │   └── crypto_api.py
│       ├── app.py             # ENHANCED: add scheduler to composition root
│       └── main.py            # ENHANCED: start scheduler + adapters
└── tests/
    ├── test_scheduler.py
    ├── test_jobs.py
    └── test_fetchers.py
```

**Reuse strategy**: Week 2 *extends* Week 1 — copy `week1-chatbot/src/bot/`
as a starting point, then add `jobs/` and `fetchers/` directories. The core,
handlers, services, and adapters are unchanged (proving the architecture works).

---

## 3. Data model additions (SQLite)

```sql
-- migrations/002_jobs.sql
CREATE TABLE scheduled_jobs (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL UNIQUE,
    job_type         TEXT NOT NULL,              -- 'cron' | 'interval'
    schedule         TEXT NOT NULL,              -- cron expr or interval seconds
    enabled          BOOLEAN NOT NULL DEFAULT 1,
    last_run_at      TEXT,
    next_run_at      TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE job_runs (
    id               INTEGER PRIMARY KEY,
    job_id           INTEGER NOT NULL REFERENCES scheduled_jobs(id),
    started_at       TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at      TEXT,
    status           TEXT NOT NULL,              -- 'running' | 'success' | 'failed'
    result_summary   TEXT,                       -- e.g., "Sent to 42 users"
    error_message    TEXT,
    output_data      TEXT                        -- JSON blob of results
);

CREATE TABLE job_deliveries (
    id               INTEGER PRIMARY KEY,
    job_run_id       INTEGER NOT NULL REFERENCES job_runs(id),
    platform         TEXT NOT NULL,
    platform_user_id TEXT NOT NULL,
    delivered_at     TEXT NOT NULL DEFAULT (datetime('now')),
    message_id       TEXT                        -- platform's message ID
);

CREATE INDEX idx_job_runs_job_id ON job_runs(job_id);
CREATE INDEX idx_job_runs_started_at ON job_runs(started_at);
```

**Why these tables**:
- `scheduled_jobs`: registry of all jobs (enables `/admin jobs` command)
- `job_runs`: execution history (debugging, metrics, retries)
- `job_deliveries`: audit trail of who received what (compliance, debugging)

---

## 4. Job examples

### Example 1: Daily weather report

**Schedule**: Every day at 9am  
**Action**: Fetch weather for user's city, send via Telegram/Discord

```python
# jobs/weather.py
from apscheduler.triggers.cron import CronTrigger

async def daily_weather_job(app):
    """Fetch weather and send to all users who enabled 'weather_report'."""
    users = await app.services.users.get_users_with_setting('weather_report', 'on')
    
    for user in users:
        city = await app.services.users.get_setting(user.id, 'city', default='London')
        weather = await app.fetchers.weather.get_forecast(city)
        
        message = format_weather_report(weather, city)
        
        # Reuse Week 1 adapters to send
        await app.send_to_user(user, message)
    
    return f"Sent to {len(users)} users"

def register(scheduler, app):
    scheduler.add_job(
        daily_weather_job,
        CronTrigger(hour=9, minute=0),
        args=[app],
        id='daily_weather',
        name='Daily Weather Report',
        replace_existing=True,
    )
```

### Example 2: Crypto price alert

**Schedule**: Every 15 minutes  
**Action**: Check BTC/ETH prices, alert users if threshold crossed

```python
# jobs/price_alert.py
from apscheduler.triggers.interval import IntervalTrigger

async def price_alert_job(app):
    """Check crypto prices and alert users with active alerts."""
    alerts = await app.services.jobs.get_active_price_alerts()
    
    for alert in alerts:
        current_price = await app.fetchers.crypto.get_price(alert.symbol)
        
        if alert.condition == 'above' and current_price > alert.threshold:
            await app.send_to_user(
                alert.user,
                f"🚨 {alert.symbol} is now ${current_price:.2f} (above ${alert.threshold})"
            )
            await app.services.jobs.mark_alert_triggered(alert.id)
        
        elif alert.condition == 'below' and current_price < alert.threshold:
            await app.send_to_user(
                alert.user,
                f"🚨 {alert.symbol} is now ${current_price:.2f} (below ${alert.threshold})"
            )
            await app.services.jobs.mark_alert_triggered(alert.id)
    
    return f"Checked {len(alerts)} alerts"

def register(scheduler, app):
    scheduler.add_job(
        price_alert_job,
        IntervalTrigger(minutes=15),
        args=[app],
        id='price_alerts',
        name='Crypto Price Alerts',
        replace_existing=True,
    )
```

### Example 3: System health check

**Schedule**: Every 5 minutes  
**Action**: Check database, API health; alert admins if down

```python
# jobs/health_check.py
from apscheduler.triggers.interval import IntervalTrigger

async def health_check_job(app):
    """Ping critical services and alert admins if unhealthy."""
    checks = {
        'database': await check_database(app.db),
        'weather_api': await check_api(app.fetchers.weather),
        'crypto_api': await check_api(app.fetchers.crypto),
    }
    
    failures = [name for name, healthy in checks.items() if not healthy]
    
    if failures:
        admins = await app.services.users.get_admins()
        message = f"⚠️ Health check failed: {', '.join(failures)}"
        for admin in admins:
            await app.send_to_user(admin, message)
        return f"UNHEALTHY: {failures}"
    
    return "All systems healthy"

def register(scheduler, app):
    scheduler.add_job(
        health_check_job,
        IntervalTrigger(minutes=5),
        args=[app],
        id='health_check',
        name='System Health Check',
        replace_existing=True,
    )
```

---

## 5. User-facing commands

Extend Week 1's command set with job management:

| Command | Access | Behavior |
|---------|--------|----------|
| `/subscribe weather` | all | Enable daily weather report |
| `/unsubscribe weather` | all | Disable daily weather report |
| `/alert BTC above 50000` | all | Create price alert |
| `/alerts` | all | List active alerts |
| `/alert cancel <id>` | all | Cancel alert |
| `/admin jobs` | admin | List all scheduled jobs + status |
| `/admin job <name> enable` | admin | Enable a job |
| `/admin job <name> disable` | admin | Disable a job |
| `/admin job <name> trigger` | admin | Run job immediately |
| `/admin job <name> history` | admin | Show last 10 runs |

**New handlers** (add to `handlers/`):
- `subscribe.py` — Manage subscriptions
- `alerts.py` — Manage price alerts
- `admin_jobs.py` — Admin job control

---

## 6. Day-by-day plan

### Day 1 — Setup + scheduler foundation
- [ ] Copy `week1-chatbot` → `week2-scheduled-bot`
- [ ] Add `APScheduler`, `aiohttp` to `pyproject.toml`
- [ ] Write `jobs/scheduler.py`: APScheduler setup, job registry
- [ ] Write `002_jobs.sql` migration
- [ ] Write `db/repositories/job_repo.py`
- [ ] Unit tests: scheduler starts/stops, jobs register
- [ ] **Exit**: Scheduler runs, empty job registry, tests green

### Day 2 — First job: daily weather
- [ ] Write `fetchers/weather_api.py` (use OpenWeatherMap or wttr.in)
- [ ] Write `jobs/weather.py` with cron trigger
- [ ] Write `handlers/subscribe.py` for `/subscribe weather`
- [ ] Add `send_to_user(user, message)` helper to `app.py`
- [ ] Unit tests: weather job logic (mock API), subscription command
- [ ] Integration test: trigger job manually, verify delivery
- [ ] **Exit**: Daily weather job works end-to-end

### Day 3 — Interval job: price alerts
- [ ] Write `fetchers/crypto_api.py` (use CoinGecko or CryptoCompare)
- [ ] Write `jobs/price_alert.py` with interval trigger
- [ ] Write `handlers/alerts.py` for `/alert`, `/alerts`, `/alert cancel`
- [ ] Add `price_alerts` table (or use `user_settings` with JSON)
- [ ] Unit tests: price alert logic, alert commands
- [ ] **Exit**: Price alerts trigger and deliver

### Day 4 — Admin controls + health check
- [ ] Write `jobs/health_check.py`
- [ ] Write `handlers/admin_jobs.py` for `/admin jobs`, `/admin job <name> ...`
- [ ] Implement enable/disable/trigger/history commands
- [ ] Unit tests: admin commands, health check logic
- [ ] **Exit**: Admins can control jobs via commands

### Day 5 — Hardening + error handling
- [ ] Job error handling: catch exceptions, log to `job_runs`, retry logic
- [ ] Graceful shutdown: wait for running jobs before exit
- [ ] Job execution timeout (kill jobs that run too long)
- [ ] Persistent job state: jobs survive bot restart
- [ ] Unit tests: error scenarios, retries, timeouts
- [ ] **Exit**: Jobs are resilient to failures

### Day 6 — Eval integration + docs
- [ ] Write `evals/cases/week2_jobs.json` (see §7)
- [ ] Write `evals/week2_adapter.py` (trigger jobs, check results)
- [ ] README: architecture, job examples, setup, deployment
- [ ] **Exit**: Eval suite green, README complete

### Day 7 — Deploy + soak test
- [ ] Update Dockerfile: APScheduler runs alongside adapters
- [ ] Deploy to Railway/Fly.io (reuse Week 1 deployment)
- [ ] Soak test: leave running for 24h, verify jobs execute on schedule
- [ ] Monitor: check `job_runs` table, delivery counts, error rate
- [ ] **Exit**: Deployed, jobs running reliably

---

## 7. Eval cases for this project

`evals/cases/week2_jobs.json`:

```json
{
  "suite": "week2-scheduled-bot",
  "cases": [
    {
      "id": "subscribe-weather",
      "input": "/subscribe weather",
      "expected": {"must_contain": ["subscribed", "weather"]},
      "tags": ["subscriptions"]
    },
    {
      "id": "unsubscribe-weather",
      "input": "/unsubscribe weather",
      "context": {"subscribed_to": ["weather"]},
      "expected": {"must_contain": ["unsubscribed"]},
      "tags": ["subscriptions"]
    },
    {
      "id": "create-price-alert",
      "input": "/alert BTC above 50000",
      "expected": {"must_match_regex": ["alert.*created", "BTC.*50000"]},
      "tags": ["alerts"]
    },
    {
      "id": "list-alerts",
      "input": "/alerts",
      "context": {"alerts": [{"symbol": "BTC", "threshold": 50000}]},
      "expected": {"must_contain": ["BTC", "50000"]},
      "tags": ["alerts"]
    },
    {
      "id": "admin-list-jobs",
      "input": "/admin jobs",
      "context": {"is_admin": true},
      "expected": {"must_contain": ["daily_weather", "price_alerts"]},
      "tags": ["admin", "jobs"]
    },
    {
      "id": "admin-disable-job",
      "input": "/admin job daily_weather disable",
      "context": {"is_admin": true},
      "expected": {"must_contain": ["disabled"]},
      "tags": ["admin", "jobs"]
    },
    {
      "id": "admin-trigger-job",
      "input": "/admin job daily_weather trigger",
      "context": {"is_admin": true},
      "expected": {"must_contain": ["triggered", "running"]},
      "tags": ["admin", "jobs"]
    },
    {
      "id": "job-execution-logged",
      "description": "Verify job runs are logged to job_runs table",
      "input": null,
      "context": {"job_name": "daily_weather", "trigger": "manual"},
      "expected": {"metadata_equals": {"job_logged": true}},
      "tags": ["jobs", "audit"]
    }
  ]
}
```

**Note**: Some eval cases test *job execution* (not just commands) — the
`week2_adapter.py` will need helpers to trigger jobs and inspect `job_runs`.

---

## 8. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| APScheduler state lost on restart | Persist jobs to DB, re-register on startup |
| Jobs overlap (slow job still running when next trigger fires) | Use `max_instances=1` in APScheduler, or skip if previous run incomplete |
| API rate limits (weather, crypto) | Cache responses (5–15 min TTL), respect API limits |
| Job failures spam admins | Rate-limit alerts (max 1 per job per hour), aggregate failures |
| Time zones (cron jobs) | Store all times in UTC, let users set `timezone` setting |

---

## 9. Definition of done

- [ ] At least 2 scheduled jobs working (weather + price alerts)
- [ ] Jobs persist across bot restarts (re-registered from DB)
- [ ] User commands: `/subscribe`, `/alert`, `/alerts` working
- [ ] Admin commands: `/admin jobs`, enable/disable/trigger working
- [ ] Job execution logged to `job_runs` table
- [ ] Error handling: failed jobs logged, don't crash scheduler
- [ ] `pytest` green + eval suite green
- [ ] README with job examples, setup, deployment
- [ ] Deployed and running for 24h+ (jobs execute on schedule)

---

## 10. What this teaches (theory links)

| Concept in the plan | Roadmap concept | Resource |
|---------------------|-----------------|----------|
| APScheduler cron/interval | Background jobs, schedulers | APScheduler docs |
| Job registry + persistence | State management | SQLite + migrations |
| Fetch API → process → deliver | Observe → process → act pattern | aiohttp docs |
| Job execution logging | Audit logging, observability | `job_runs` table design |
| Graceful shutdown | Production infrastructure | asyncio shutdown patterns |
| Reusing Week 1 core | Architecture reusability | Hexagonal architecture |

---

## 11. Bonus features (if time permits)

- [ ] **One-shot jobs**: `/remind me in 2 hours to check email`
- [ ] **Webhook jobs**: Trigger job on external event (GitHub webhook, etc.)
- [ ] **Job dependencies**: Run job B only if job A succeeds
- [ ] **Broadcast queue**: Implement the Week 1 stub — queue messages, rate-limit delivery
- [ ] **Email delivery**: Add email adapter (SMTP) alongside Telegram/Discord
- [ ] **Job metrics dashboard**: `/admin metrics` — success rate, avg duration, etc.

---

## 12. Integration with Week 1

**What's reused**:
- ✅ Core contracts (`IncomingMessage`, `OutgoingReply`)
- ✅ Router + middleware (logging, auth, rate limiting)
- ✅ All Week 1 handlers (start, help, profile, settings, admin)
- ✅ Services (UserService, AdminService)
- ✅ Repositories (UserRepository, AuditRepository)
- ✅ Database + migrations (001_init.sql)
- ✅ Adapters (Telegram, Discord, Slack, Reddit, Eval)

**What's new**:
- ✅ Scheduler (`jobs/scheduler.py`)
- ✅ Job definitions (`jobs/*.py`)
- ✅ API fetchers (`fetchers/*.py`)
- ✅ Job-related tables (`002_jobs.sql`)
- ✅ Job repository (`db/repositories/job_repo.py`)
- ✅ New handlers (`subscribe.py`, `alerts.py`, `admin_jobs.py`)

**Proof of architecture**: Week 2 adds zero changes to Week 1's core — the
scheduler is just another "adapter" that triggers commands programmatically.

---

## 13. Example: Full flow for daily weather

```
1. Scheduler (APScheduler)
   ├─ Trigger: CronTrigger(hour=9, minute=0)
   └─ Calls: daily_weather_job(app)

2. Job execution (jobs/weather.py)
   ├─ Query: users with setting 'weather_report'='on'
   ├─ For each user:
   │  ├─ Fetch: weather_api.get_forecast(user.city)
   │  ├─ Format: "🌤️ London: 18°C, partly cloudy"
   │  └─ Send: app.send_to_user(user, message)
   └─ Log: job_runs table (status='success', result_summary='Sent to 42 users')

3. Delivery (reuse Week 1 adapters)
   ├─ app.send_to_user() → router.dispatch_internal()
   ├─ Router finds user's platform (telegram, discord, etc.)
   ├─ Adapter sends message
   └─ Log: job_deliveries table (platform, user_id, message_id)

4. Audit trail
   ├─ job_runs: execution history
   ├─ job_deliveries: who received what
   └─ audit_log: (optional) log as internal command
```

---

## 14. Testing strategy

### Unit tests
- `test_scheduler.py`: job registration, start/stop, persistence
- `test_jobs.py`: job logic (mock APIs, mock delivery)
- `test_fetchers.py`: API clients (mock HTTP responses)
- `test_handlers.py`: new commands (subscribe, alerts, admin jobs)

### Integration tests
- Trigger job manually, verify delivery to test user
- Disable job, verify it doesn't run
- Job failure scenario, verify error logged

### Eval cases
- Command-based: `/subscribe`, `/alert`, `/admin jobs`
- Execution-based: trigger job, check `job_runs` table

### Soak test (production)
- Deploy, leave running 24h
- Verify jobs execute on schedule
- Check error rate, delivery success rate

---

## 15. Deployment notes

**Dockerfile** (extend Week 1):
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

ENV DB_PATH=/data/bot.db
VOLUME /data

# APScheduler runs in the same process as the bot
CMD ["python", "-m", "bot.main"]
```

**Environment variables** (add to Week 1's `.env`):
```bash
# API keys
WEATHER_API_KEY=your_openweathermap_key
CRYPTO_API_KEY=your_coingecko_key  # (optional, many APIs are free)

# Job settings
JOBS_ENABLED=true
JOBS_TIMEZONE=UTC
```

**Graceful shutdown**: APScheduler must finish running jobs before exit.

```python
# main.py
async def shutdown(scheduler):
    scheduler.shutdown(wait=True)  # wait for running jobs
    # then stop adapters, close DB
```

---

## 16. Success criteria

Week 2 is complete when:
- ✅ At least 2 jobs running on schedule (weather + price alerts)
- ✅ Jobs persist across restarts
- ✅ Users can subscribe/unsubscribe, create alerts
- ✅ Admins can control jobs via commands
- ✅ Job execution logged and auditable
- ✅ Tests green (unit + integration + evals)
- ✅ Deployed and running 24h+ without issues
- ✅ README documents architecture, examples, deployment

**Portfolio value**: Demonstrates understanding of background jobs, scheduling,
API integration, and proactive bot behavior (not just reactive chat).

---

**Next**: Week 3 — State Machine Bot (multi-step workflows, conversation state)
