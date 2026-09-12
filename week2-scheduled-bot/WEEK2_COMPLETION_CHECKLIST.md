# Week 2 Completion Checklist

Scheduled automation bot extending the Week 1 core with background jobs, API integration, and proactive messaging.

## Core Functionality

- [x] **Scheduler layer (APScheduler)**
  - [x] `src/bot/jobs/scheduler.py` wraps `AsyncIOScheduler`
  - [x] Cron and interval triggers supported
  - [x] Job persistence in `scheduled_jobs` table
  - [x] Manual enable / disable / trigger / history admin controls

- [x] **Scheduled jobs**
  - [x] `daily_weather` — daily at 9:00 AM UTC (wttr.in)
  - [x] `price_alerts` — every 15 minutes (CoinGecko)
  - [x] `health_check` — every 5 minutes (database connectivity)

- [x] **API fetchers**
  - [x] `src/bot/fetchers/weather_api.py` (wttr.in, no key)
  - [x] `src/bot/fetchers/crypto_api.py` (CoinGecko, no key)

- [x] **New user commands**
  - [x] `/subscribe weather`
  - [x] `/unsubscribe weather`
  - [x] `/alert <SYMBOL> <above|below> <PRICE>`
  - [x] `/alerts`
  - [x] `/alert cancel <ID>`

- [x] **New admin commands**
  - [x] `/admin jobs`
  - [x] `/admin job <name> enable`
  - [x] `/admin job <name> disable`
  - [x] `/admin job <name> trigger`
  - [x] `/admin job <name> history`

## Persistence

- [x] `migrations/002_jobs.sql` adds:
  - [x] `scheduled_jobs`
  - [x] `job_runs`
  - [x] `job_deliveries`
  - [x] `price_alerts`
- [x] Indexes on run history, deliveries, and alerts
- [x] `JobRepository` and `JobService` for job and alert CRUD

## Architecture

- [x] Week 1 core reused unchanged
- [x] Scheduler plugs into `App` via `build_app()`
- [x] Graceful shutdown: scheduler stopped before adapters and DB
- [x] `send_to_user()` seam defined for job-to-user delivery

## Testing

- [x] Existing Week 1 tests retained
- [x] New Week 2 tests in `tests/test_week2.py`:
  - [x] `/subscribe weather` and `/unsubscribe weather`
  - [x] `/alert`, `/alerts`, and `/alert cancel`
  - [x] `/admin jobs`, `/admin job ... enable/disable/trigger`
- [x] `pytest` green: 29/29 passing

## Documentation

- [x] `README.md` with architecture diagram, commands, setup, and deployment
- [x] `.env.example` updated with Week 2 settings
- [x] `Dockerfile` configured for scheduler in same process

## Deployment

- [x] `pyproject.toml` names the package `week2-scheduled-bot`
- [x] `Dockerfile` with persistent `/data` volume
- [x] Environment variables: `JOBS_ENABLED`, `JOBS_TIMEZONE`

## Known Limitations

- `App.send_to_user()` routes to the correct adapter by platform. Telegram and Discord implement real DM delivery; Slack and Reddit `send()` methods log the message (full platform sending is a future enhancement).

---

Generated: 2026-09-12
