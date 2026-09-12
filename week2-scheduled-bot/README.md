# week2-scheduled-bot

Phase 1, Project 2 of the bot roadmap: a **scheduled automation bot** that extends Week 1's platform-agnostic core with background jobs, API integration, and proactive messaging.

**Key insight**: Bots don't have to chat — they can observe → process → act on schedules.

## Architecture

**Week 1 core (unchanged) + Scheduler layer**

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
            (router, middleware, handlers, services, DB)
```

### What's New in Week 2

- **Scheduler** (`src/bot/jobs/scheduler.py`): APScheduler wrapper with persistence
- **Jobs** (`src/bot/jobs/`): Daily weather, price alerts, health checks
- **API Fetchers** (`src/bot/fetchers/`): Weather (wttr.in), Crypto (CoinGecko)
- **Job Service** (`src/bot/services/job_service.py`): Job management logic
- **New Tables**: `scheduled_jobs`, `job_runs`, `job_deliveries`, `price_alerts`
- **New Commands**: `/subscribe`, `/alert`, `/alerts`, `/admin jobs`

### What's Reused from Week 1

- ✅ Core contracts (`IncomingMessage`, `OutgoingReply`)
- ✅ Router + middleware (logging, auth, rate limiting)
- ✅ All Week 1 handlers (start, help, profile, settings, admin)
- ✅ Services (UserService, AdminService)
- ✅ Repositories (UserRepository, AuditRepository)
- ✅ Database + migrations (001_init.sql)
- ✅ Adapters (Telegram, Discord, Slack, Reddit, Eval)

## Commands

### User Commands

| Command | Access | Description |
|---------|--------|-------------|
| `/subscribe weather` | all | Enable daily weather reports at 9:00 AM UTC |
| `/unsubscribe weather` | all | Disable weather reports |
| `/alert BTC above 50000` | all | Create price alert (triggers when threshold crossed) |
| `/alerts` | all | List your active price alerts |
| `/alert cancel <id>` | all | Cancel a price alert |

### Admin Commands

| Command | Access | Description |
|---------|--------|-------------|
| `/admin jobs` | admin | List all scheduled jobs + status |
| `/admin job <name> enable` | admin | Enable a job |
| `/admin job <name> disable` | admin | Disable a job |
| `/admin job <name> trigger` | admin | Run job immediately |
| `/admin job <name> history` | admin | Show last 10 runs |

### Example Usage

```
User: /subscribe weather
Bot:  ✅ Subscribed to weather
      
      Daily weather report at 9:00 AM UTC
      
      Use /unsubscribe weather to disable.

User: /alert BTC above 50000
Bot:  🚀 Price alert created!
      
      Symbol: BTC
      Condition: above $50,000.00
      Alert ID: 1
      
      You'll be notified when the price crosses this threshold.

User: /alerts
Bot:  Your Price Alerts:
      
      🚀 BTC above $50,000.00
         ID: 1 | ✅ Active
      
      Total: 1 alerts
      Cancel with: /alert cancel <ID>

Admin: /admin jobs
Bot:   Scheduled Jobs:
       
       daily_weather
         Type: cron | Schedule: 0 9 * * *
         Status: ✅ Enabled
         Last run: 2026-09-12 09:00:00
         Next run: 2026-09-13 09:00:00
       
       price_alerts
         Type: interval | Schedule: 900
         Status: ✅ Enabled
         Last run: 2026-09-12 14:30:00
         Next run: 2026-09-12 14:45:00
```

## Scheduled Jobs

### Daily Weather Report
- **Schedule**: Every day at 9:00 AM UTC (cron)
- **Action**: Fetches weather for each subscribed user's city and sends report
- **API**: wttr.in (free, no key required)
- **Subscription**: `/subscribe weather`

### Price Alerts
- **Schedule**: Every 15 minutes (interval)
- **Action**: Checks active price alerts, triggers if threshold crossed
- **API**: CoinGecko (free tier, no key required)
- **Supported**: BTC, ETH, USDT, BNB, SOL, XRP, ADA, DOGE
- **Create**: `/alert BTC above 50000`

### Health Check
- **Schedule**: Every 5 minutes (interval)
- **Action**: Checks database connectivity, alerts admins if unhealthy
- **Purpose**: System monitoring

## Setup

```powershell
cd week2-scheduled-bot
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e .[dev]
copy .env.example .env   # fill in tokens
```

### Environment Variables

Same as Week 1, plus:

```bash
# Week 2: Job scheduler settings (optional)
JOBS_ENABLED=true
JOBS_TIMEZONE=UTC
```

No API keys required! Weather (wttr.in) and crypto (CoinGecko) APIs work without keys.

## Run

```powershell
python -m bot.main
```

The scheduler starts automatically alongside the adapters.

## Test

```powershell
# Unit tests
pytest

# Eval suite
cd ..\evals
python run_evals.py --cases cases/week2_jobs.json --target week2_adapter:bot
```

## Database Schema

Week 2 adds 4 new tables via `migrations/002_jobs.sql`:

- **scheduled_jobs**: Job registry (name, type, schedule, enabled status)
- **job_runs**: Execution history (status, result, errors)
- **job_deliveries**: Audit trail of message deliveries
- **price_alerts**: User-created price alerts

## Deployment

Same as Week 1 (Railway, Fly.io, Docker/VPS). The scheduler runs in the same process as the bot.

### Dockerfile

```dockerfile
FROM python:3.11-slim

RUN useradd -m -u 1000 botuser

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

ENV DB_PATH=/data/bot.db
VOLUME /data
RUN mkdir -p /data && chown -R botuser:botuser /app /data

USER botuser

# Scheduler runs alongside adapters
CMD ["python", "-m", "bot.main"]
```

### Graceful Shutdown

The scheduler waits for running jobs to complete before shutting down:

```python
# Ctrl+C triggers:
1. Stop scheduler (wait for running jobs)
2. Stop adapters
3. Close database
```

## Job Execution Flow

```
1. APScheduler triggers job at scheduled time
   ↓
2. JobScheduler.execute_job()
   - Creates job_run record (status='running')
   - Calls job function (e.g., daily_weather_job)
   ↓
3. Job function
   - Fetches data from API
   - Processes data
   - Calls app.send_to_user() for each recipient
   ↓
4. Delivery
   - Logs to job_deliveries table
   - Sends via Week 1 adapters (Telegram, Discord, etc.)
   ↓
5. Completion
   - Updates job_run (status='success', result_summary)
   - Updates scheduled_jobs (last_run_at, next_run_at)
```

## Known Limits / Next Steps

- **send_to_user() is a stub**: Currently logs messages instead of delivering
  - Production version needs message queue or direct adapter access
- **Job overlap prevention**: `max_instances=1` prevents concurrent runs
- **API rate limits**: Cached responses recommended for production
- **Time zones**: All times in UTC; user timezone setting for display only

## What This Teaches

| Concept | Implementation |
|---------|----------------|
| **Background jobs** | APScheduler with cron and interval triggers |
| **Job persistence** | Jobs stored in DB, re-registered on startup |
| **API integration** | aiohttp for async HTTP requests |
| **Observe → process → act** | Jobs fetch data, process, and deliver proactively |
| **Graceful shutdown** | Scheduler waits for running jobs |
| **Architecture reuse** | Week 1 core unchanged, scheduler plugs in |

## Metrics

| Metric | Value |
|--------|-------|
| **New commands** | 6 (/subscribe, /unsubscribe, /alert, /alerts, /admin jobs, /admin job) |
| **Scheduled jobs** | 3 (weather, price alerts, health check) |
| **API integrations** | 2 (wttr.in, CoinGecko) |
| **New tables** | 4 |
| **New code** | ~1,000 lines |
| **Week 1 code changed** | 0 lines (pure extension) |

---

**Next**: Week 3 — State Machine Bot (multi-step workflows, conversation state)
