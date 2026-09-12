# week1-chatbot

Phase 1, Project 1 of the bot roadmap: a **platform-agnostic chat bot** whose
core command logic runs identically on Telegram, Discord, and a headless eval
harness. No AI — this project is about the bot lifecycle, persistence,
permissions, rate limiting, and clean seams.

## Architecture

**Hexagonal core + thin platform adapters** — business logic lives in a
platform-agnostic core, so the same commands work identically on Telegram,
Discord, Slack, Reddit, and the eval harness.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Platform Adapters                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ Telegram │  │ Discord  │  │  Slack   │  │  Reddit  │  │ Eval │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬──┘ │
│       │             │             │             │            │    │
│       └─────────────┴─────────────┴─────────────┴────────────┘    │
│                              ▼                                     │
│                     IncomingMessage (contract)                     │
└─────────────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Core (Platform-Free)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Router: parse command → dispatch → middleware chain          │  │
│  │   ├─ Logging middleware (structured JSON logs)               │  │
│  │   ├─ Auth middleware (auto-register, check banned)           │  │
│  │   └─ Rate limiter (token bucket, 5/10s per user)             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Handlers: /start, /help, /profile, /settings, /admin         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Services: UserService, AdminService                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Repositories: UserRepo, AuditRepo                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ▼                                      │
│                       SQLite (aiosqlite)                            │
│                   Migrations: 001_init.sql                          │
└─────────────────────────────────────────────────────────────────────┘
                               ▼
                      OutgoingReply (contract)
```

### Key design decisions

- **Platform-agnostic core**: Zero `telegram` or `discord` imports in
  `core/`, `handlers/`, `services/`, or `db/` — adapters translate platform
  events to/from `IncomingMessage`/`OutgoingReply` contracts.
- **Testable seam**: Unit tests exercise handlers through the router without
  any platform running; eval harness reuses the same core.
- **Middleware chain**: Logging, auth, and rate limiting run before every
  handler — handlers focus purely on business logic.
- **Audit log**: Every command (success, denial, error) writes to `audit_log`
  table for compliance and debugging.

### Directory structure

- **Core** (`src/bot/core/`): contracts, router, errors, middleware. Zero
  platform imports — this is the testable seam every later project reuses.
- **Handlers** (`src/bot/handlers/`): one file per command; registered via
  `register_all()`.
- **Services** (`src/bot/services/`): business logic (user prefs, admin ops).
- **DB** (`src/bot/db/`): aiosqlite + numbered SQL migrations.
- **Adapters** (`src/bot/adapters/`): Telegram, Discord, Slack, Reddit, eval-harness bridges.

## Commands

| Command | Access | Description |
|---|---|---|
| `/start` | all | Register + welcome (idempotent) |
| `/help` | all | Commands visible to your role |
| `/profile` | all | Username, role, join date, settings |
| `/settings` | all | Show settings |
| `/settings key=value` | all | Update `locale`, `timezone`, or `notify` |
| `/admin stats` | admin | User/command counts |
| `/admin ban <platform>:<id>` | admin | Ban a user |
| `/admin unban <platform>:<id>` | admin | Unban |
| `/admin broadcast <msg>` | admin | Stub — real delivery lands Week 2 |

### Example usage

```
User: /start
Bot:  Welcome! You're registered. Use /help to see available commands.

User: /profile
Bot:  Username: alice
      Role: user
      Joined: 2026-09-12 10:30:45
      Settings: locale=en, timezone=UTC, notify=on

User: /settings notify=off
Bot:  Setting saved: notify=off

User: /settings hack=1
Bot:  Unknown setting key: hack. Valid keys: locale, timezone, notify

User: /admin stats
Bot:  Permission denied — admin only.

Admin: /admin stats
Bot:   Total users: 42
       Commands today: 156
       Platforms: telegram=30, discord=10, slack=2
```

## Setup

```powershell
cd week1-chatbot
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e .[dev]
copy .env.example .env   # fill in tokens
```

- **Telegram**: talk to `@BotFather` → `/newbot` → paste token into `.env`.
- **Discord**: Developer Portal → New Application → Bot → token; enable
*Message Content Intent* under Bot settings, invite with `Send Messages` scope.
- **Slack**: api.slack.com → New App → Socket Mode ON → app-level token
(`connections:write`) → bot scopes `app_mentions:read`, `chat:write`,
`im:history`, `im:read` → install to workspace → both tokens into `.env`.
- **Reddit**: reddit.com/prefs/apps → "script" app → client id/secret +
account credentials into `.env`. The bot answers `u/<botname>` mentions,
DMs, and comment replies.
- **Admins**: set `ADMIN_IDS=telegram:<your-id>` (find your id via any id bot);
Slack ids look like `slack:U0XXXXXXX`, Reddit is `reddit:<username>`.

## Run

```powershell
python -m bot.main            # from src/ on PYTHONPATH, or after pip install -e .
```

## Test

```powershell
pytest                        # unit tests — core only, no platform needed
```

## Evaluate (uses E:\Bots\evals framework)

```powershell
cd ..\evals
python run_evals.py --cases cases/week1_bot.json --target week1_adapter:bot
```

where `evals/week1_adapter.py` bridges into this project (see that file).

## Deployment

### Option 1: Railway

1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Create project: `railway init`
4. Add environment variables:
   ```bash
   railway variables set TELEGRAM_TOKEN=your_token
   railway variables set DISCORD_TOKEN=your_token
   railway variables set ADMIN_IDS=telegram:123456
   ```
5. Deploy: `railway up`
6. Add volume for persistence: Railway dashboard → Settings → Volumes → mount at `/data`

### Option 2: Fly.io

1. Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
2. Login: `fly auth login`
3. Create app: `fly launch` (follow prompts, say yes to Dockerfile)
4. Create volume: `fly volumes create bot_data --size 1`
5. Set secrets:
   ```bash
   fly secrets set TELEGRAM_TOKEN=your_token
   fly secrets set DISCORD_TOKEN=your_token
   fly secrets set ADMIN_IDS=telegram:123456
   ```
6. Deploy: `fly deploy`

### Option 3: Docker on VPS

```bash
# Build image
docker build -t week1-chatbot .

# Create volume for persistence
docker volume create bot_data

# Run (replace tokens)
docker run -d \
  --name week1-chatbot \
  --restart unless-stopped \
  -v bot_data:/data \
  -e TELEGRAM_TOKEN=your_token \
  -e DISCORD_TOKEN=your_token \
  -e ADMIN_IDS=telegram:123456 \
  week1-chatbot
```

View logs: `docker logs -f week1-chatbot`

### Environment variables checklist

Required (at least one platform):
- `TELEGRAM_TOKEN` — from @BotFather
- `DISCORD_TOKEN` — from Discord Developer Portal
- `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN` — from api.slack.com
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `REDDIT_PASSWORD`, `REDDIT_USER_AGENT`

Optional:
- `ADMIN_IDS` — comma-separated, e.g. `telegram:123456,discord:789`
- `DB_PATH` — defaults to `bot.db` (set to `/data/bot.db` in Docker)
- `RATE_LIMIT_CAPACITY` — default `5`
- `RATE_LIMIT_WINDOW_S` — default `10`

## Known limits / next steps

- Broadcast is a stub (needs a queue — Week 2)
- Rate limiting is in-memory (resets on restart)
- SQLite: fine up to moderate load; migrate to Postgres in later phases
- Logs are JSON lines — pipe to a log aggregator (Loki, CloudWatch, etc.) in production
