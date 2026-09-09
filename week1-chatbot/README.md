# week1-chatbot

Phase 1, Project 1 of the bot roadmap: a **platform-agnostic chat bot** whose
core command logic runs identically on Telegram, Discord, and a headless eval
harness. No AI — this project is about the bot lifecycle, persistence,
permissions, rate limiting, and clean seams.

## Architecture

```
Telegram ──► TelegramAdapter ─┐
                              ├──► Router ──► Middleware ──► Handlers ──► Services ──► Repos ──► SQLite
Discord  ──► DiscordAdapter  ─┘              (logging, auth, ratelimit)
Eval     ──► EvalAdapter     ─┘
```

- **Core** (`src/bot/core/`): contracts, router, errors, middleware. Zero
  platform imports — this is the testable seam every later project reuses.
- **Handlers** (`src/bot/handlers/`): one file per command; registered via
  `register_all()`.
- **Services** (`src/bot/services/`): business logic (user prefs, admin ops).
- **DB** (`src/bot/db/`): aiosqlite + numbered SQL migrations.
- **Adapters** (`src/bot/adapters/`): Telegram, Discord, eval-harness bridges.

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

## Setup

```powershell
cd week1-chatbot
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e .[dev]
copy .env.example .env   # fill in tokens
```

**Telegram**: talk to `@BotFather` → `/newbot` → paste token into `.env`.
**Discord**: Developer Portal → New Application → Bot → token; enable
*Message Content Intent* under Bot settings, invite with `Send Messages` scope.
**Admins**: set `ADMIN_IDS=telegram:<your-id>` (find your id via any id bot).

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

## Known limits / next steps

- Broadcast is a stub (needs a queue — Week 2)
- Rate limiting is in-memory (resets on restart)
- SQLite: fine up to moderate load; migrate to Postgres in later phases
