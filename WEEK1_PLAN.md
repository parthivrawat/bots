# Week 1 — Platform-Agnostic Chat Bot (Telegram + Discord)

> **Phase 1, Project 1** — No AI. Goal: master the bot lifecycle, event-driven
> architecture, and clean separation between platform and business logic.
>
> **Stack**: Python 3.11+, `python-telegram-bot` v21+, `discord.py` v2+,
> `aiosqlite` (SQLite), `pytest`. Optional Docker for deployment.

---

## 1. Architecture

### Design decision: Hexagonal core + thin platform adapters

**Why**: the roadmap has every later project (AI, RAG, agents) sitting *behind*
the bot interface. If business logic lives inside Telegram handlers, you rewrite
it in Week 3. If it lives in a pure core, the same handlers serve Telegram,
Discord, a future web UI, and — critically — the eval framework.

```
Telegram ──► TelegramAdapter ─┐
                              ├──► Core Router ──► Handlers ──► Services ──► Repos ──► SQLite
Discord  ──► DiscordAdapter  ─┘         ▲
                                        │
Eval harness ──► bot() callable ────────┘   (same core, zero platform code)
```

**Alternatives considered**
- *Single platform, logic in handlers*: fastest day 1, throws away the
  abstraction lesson and couples everything to one API. Rejected.
- *Full DI framework (dependency-injector etc.)*: overkill for Week 1 — plain
  constructor injection is enough. Rejected per "simplicity > clever".

### Message contract (platform-neutral)

```python
@dataclass
class IncomingMessage:
    platform: str            # "telegram" | "discord" | "eval"
    platform_user_id: str    # id on that platform
    username: str | None
    text: str                # raw text, e.g. "/settings lang=en"
    context: dict            # channel/guild info, locale, etc.

@dataclass
class OutgoingReply:
    text: str
    buttons: list[dict] | None = None   # adapters may render or ignore
```

Adapters translate platform events → `IncomingMessage`, call
`router.dispatch(msg) -> OutgoingReply`, then translate back. The core never
imports `telegram` or `discord` — that boundary is the testable seam.

### Command flow

```
"/profile"
  → adapter → IncomingMessage
  → router.parse() → Command(name="profile", args={})
  → auth middleware (register user if new, check permissions)
  → ProfileHandler.handle(user, args)
  → UserService → UserRepository → SQLite
  → OutgoingReply → adapter → platform send
```

---

## 2. Project layout

```
week1-chatbot/
├── pyproject.toml
├── .env.example
├── README.md
├── src/
│   └── bot/
│       ├── core/
│       │   ├── contracts.py      # IncomingMessage, OutgoingReply, Command
│       │   ├── router.py         # parse + dispatch + middleware chain
│       │   ├── errors.py         # BotError, PermissionDenied, etc.
│       │   └── middleware/
│       │       ├── auth.py       # auto-register, admin check
│       │       ├── ratelimit.py  # per-user token bucket
│       │       └── logging.py    # structured logs per command
│       ├── handlers/
│       │   ├── start.py
│       │   ├── help.py
│       │   ├── profile.py
│       │   ├── settings.py
│       │   └── admin.py
│       ├── services/
│       │   ├── user_service.py   # registration, profile, prefs
│       │   └── admin_service.py  # stats, broadcast, ban/unban
│       ├── db/
│       │   ├── database.py       # aiosqlite conn + migrations runner
│       │   ├── migrations/001_init.sql
│       │   └── repositories/
│       │       ├── user_repo.py
│       │       └── audit_repo.py
│       ├── adapters/
│       │   ├── telegram_bot.py   # python-telegram-bot wiring
│       │   ├── discord_bot.py    # discord.py wiring
│       │   └── eval_adapter.py   # (message, ctx) -> framework BotResponse
│       └── main.py               # entry: build core, start enabled adapters
└── tests/
    ├── test_router.py
    ├── test_handlers.py          # core logic, no platform imports
    ├── test_ratelimit.py
    └── eval_cases.json           # symlink/copy into evals/cases/
```

---

## 3. Data model (SQLite)

```sql
-- migrations/001_init.sql
CREATE TABLE users (
    id               INTEGER PRIMARY KEY,
    platform         TEXT NOT NULL,
    platform_user_id TEXT NOT NULL,
    username         TEXT,
    role             TEXT NOT NULL DEFAULT 'user',   -- 'user' | 'admin'
    locale           TEXT NOT NULL DEFAULT 'en',
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (platform, platform_user_id)
);

CREATE TABLE user_settings (
    user_id   INTEGER NOT NULL REFERENCES users(id),
    key       TEXT NOT NULL,
    value     TEXT NOT NULL,
    PRIMARY KEY (user_id, key)
);

CREATE TABLE audit_log (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id),
    command    TEXT NOT NULL,
    args       TEXT,
    result     TEXT NOT NULL,                 -- 'ok' | 'error' | 'denied'
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

Week 2's scheduled bot will add a `reports`/`jobs` table — schema is
versioned via numbered migration files applied at startup.

---

## 4. Commands & behavior spec

| Command | Access | Behavior |
|---|---|---|
| `/start` | all | Register user (idempotent), return welcome + quick help |
| `/help` | all | List commands filtered by caller's role |
| `/profile` | all | Show username, role, join date, command count |
| `/settings` | all | Show current settings |
| `/settings key=value` | all | Validate key against allowlist, persist, confirm |
| `/admin stats` | admin | Total users, commands/day, per-platform counts |
| `/admin broadcast <msg>` | admin | Queue message to all users (rate-limited send) |
| `/admin ban <platform>:<id>` | admin | Set `role='banned'`; bot ignores banned users |
| unknown | all | Friendly error + `/help` hint |

**Validation rules**
- Settings keys allowlisted: `locale`, `timezone`, `notify` — reject others.
- All writes idempotent: `/start` twice = one user row.
- Every command writes an `audit_log` row (success *and* denial).

---

## 5. Day-by-day plan

### Day 1 — Scaffold + core contracts
- [ ] `python -m venv .venv`; deps: `python-telegram-bot`, `discord.py`,
      `aiosqlite`, `pytest`, `pytest-asyncio`, `python-dotenv`
- [ ] BotFather → get Telegram token; Discord Dev Portal → app + token +
      enable Message Content intent
- [ ] `.env.example` with `TELEGRAM_TOKEN`, `DISCORD_TOKEN`,
      `ADMIN_IDS`, `DB_PATH`
- [ ] Write `contracts.py`, `errors.py`, empty `router.py`
- [ ] **Exit**: repo imports cleanly, `pytest` runs (0 tests ok)

### Day 2 — Persistence layer
- [ ] `database.py`: open aiosqlite, run pending `migrations/*.sql` in order,
      record applied versions in a `schema_migrations` table
- [ ] `user_repo.py`: `get_or_create`, `get`, `update_role`, `touch_last_seen`
- [ ] `audit_repo.py`: `log(user_id, command, args, result)`
- [ ] Unit tests with in-memory SQLite (`:memory:`)
- [ ] **Exit**: repo tests green; `/start` idempotency proven by test

### Day 3 — Router, middleware, handlers
- [ ] `router.parse`: `/cmd arg1 k=v` → `Command`; tolerate `!cmd` on Discord
- [ ] Middleware chain: `logging → auth → ratelimit → handler`
- [ ] `auth`: `get_or_create` user, attach to context, deny `role='banned'`
- [ ] `ratelimit`: token bucket — 5 commands / 10s per user (in-memory dict)
- [ ] Handlers: `start`, `help`, `profile`, `settings` (+ validation errors)
- [ ] Unit tests for every handler through the *core only* (no platform imports)
- [ ] **Exit**: `pytest` green; core usable headless via direct dispatch

### Day 4 — Admin + both adapters
- [ ] `admin.py` handlers (stats, ban, broadcast stub)
- [ ] `telegram_bot.py`: map PTB `Update` → `IncomingMessage`; register
      handlers on `CommandHandler` + fallback `MessageHandler`
- [ ] `discord_bot.py`: map `on_message` → `IncomingMessage`; reply via `ctx.send`
- [ ] `main.py`: load env, build core once, start whichever adapters have tokens
- [ ] **Exit**: same commands work identically on both platforms

### Day 5 — Hardening + eval integration
- [ ] Structured logging (JSON lines, `structlog` or stdlib `logging` + formatter)
- [ ] Global error handler → user sees "something went wrong", full trace in logs
- [ ] `eval_adapter.py`: wraps `router.dispatch` into the eval framework's
      `(message, context) -> BotResponse`
- [ ] Write `cases/week1_bot.json` (see §6) and run `run_evals.py`
- [ ] **Exit**: eval suite green

### Day 6–7 — Docs + deploy
- [ ] README: architecture diagram, setup, env vars, screenshots
- [ ] Deploy: Railway/Fly.io/VPS via `Dockerfile` (slim python, volume for db)
- [ ] Soak test: leave running, hit rate limits, restart, verify state survives
- [ ] **Exit**: deployed bot + green evals + README = portfolio piece

---

## 6. Eval cases for this project

`evals/cases/week1_bot.json` — run against `eval_adapter`:

```json
{
  "suite": "week1-chatbot",
  "cases": [
    {"id": "start-registers",      "input": "/start",
     "expected": {"must_contain": ["welcome"]},
     "tags": ["core"]},
    {"id": "help-lists-commands",  "input": "/help",
     "expected": {"must_contain": ["/start", "/profile", "/settings"]},
     "tags": ["core"]},
    {"id": "profile-after-start",  "input": "/profile",
     "context": {"platform": "eval", "platform_user_id": "u1"},
     "expected": {"must_contain": ["role"]},
     "tags": ["core"]},
    {"id": "settings-set-valid",   "input": "/settings timezone=UTC",
     "expected": {"must_match_regex": ["(set|saved|updated)"]},
     "tags": ["settings"]},
    {"id": "settings-reject-bad",  "input": "/settings hack=1",
     "expected": {"must_contain": ["unknown"], "expect_refusal": false},
     "tags": ["settings", "safety"]},
    {"id": "admin-denied-for-user","input": "/admin stats",
     "expected": {"expect_refusal": true},
     "tags": ["safety", "auth"]},
    {"id": "unknown-command",      "input": "/floop",
     "expected": {"must_contain": ["unknown"], "max_latency_ms": 500},
     "tags": ["edge"]}
  ]
}
```

> Note: eval cases that need a *pre-registered* user pass `platform_user_id`
> via `context` — the eval adapter seeds it before dispatch.

---

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Scope creep (two platforms) | Build core + Telegram first (Day 1–4), Discord adapter is ~1 file on Day 4 |
| Discord message-content intent off | Enable in Dev Portal *before* coding (Day 1 checklist) |
| Broadcast rate limits | Week 1: broadcast is a stub that logs; real queue comes in Week 2 |
| SQLite async pitfalls | Single `aiosqlite` connection guarded by `asyncio.Lock`; fine at this scale |
| Platform APIs drift | Pin versions in `pyproject.toml`; adapters isolate breakage |

---

## 8. Definition of done

- [ ] Same command set works on Telegram, Discord, and the eval harness
- [ ] `/start` idempotent; settings validated against allowlist
- [ ] Admin commands gated by role; denials audit-logged
- [ ] Rate limiter trips and recovers (test proves it)
- [ ] `pytest` green + eval suite green (`run_evals.py` exit 0)
- [ ] README with architecture diagram, env setup, screenshots
- [ ] Deployed and surviving restarts (SQLite file on volume)

---

## 9. What this teaches (theory links)

| Concept in the plan | Roadmap concept | Resource (see LEARNING_RESOURCES.md) |
|---|---|---|
| Adapters isolate platforms | Event-driven architecture | Telegram Bot API, discord.py docs |
| Idempotent `/start`, audit log | Idempotency, audit logging | Stripe idempotent-requests article |
| Token-bucket middleware | Rate limiting | — (implement, then compare w/ PTB's built-in) |
| Migrations at startup | State management | aiosqlite + migration pattern |
| `eval_adapter` reuses core | Testable seams | feeds directly into `evals/` framework |
