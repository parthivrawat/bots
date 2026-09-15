# week3-state-machine-bot

Phase 1, Project 3 of the bot roadmap: a **state-machine chatbot** with multi-step conversation workflows.

**Key insight**: Bots can remember where a user is in a flow and guide them through a sequence of prompts.

## Architecture

```
User message
    ▼
Adapter
    ▼
Router
    ▼
Auth middleware  ──►  creates/loads User
    ▼
State middleware ──►  if active workflow + free-form text:
                        rewrites command to __state__
    ▼
Rate limiter
    ▼
Command handler  ──►  /report, /onboard, /cancel, or __state__
    ▼
StateService ──►  StateMachine + StateRepository (SQLite)
    ▼
Workflow handler ──►  next state + reply
```

### What's New in Week 3

- **State machine engine** (`src/bot/core/state_machine.py`): reusable workflows, states, and transitions
- **Conversation persistence** (`src/bot/db/repositories/state_repo.py`): active, completed, and cancelled states
- **State middleware** (`src/bot/core/middleware/state.py`): captures free-form replies while in a workflow
- **StateService** (`src/bot/services/state_service.py`): starts, advances, and cancels conversations
- **Multi-step workflows**:
  - `/report` — bug/feature/question report
  - `/onboard` — city + language profile setup

### What's Reused from Week 1

- Core contracts (`IncomingMessage`, `OutgoingReply`, `Command`, `HandlerContext`)
- Router + middleware (logging, auth, rate limiting)
- Core handlers (`/start`, `/help`, `/profile`, `/settings`, `/admin`)
- Services (`UserService`, `AdminService`)
- Repositories (`UserRepository`, `AuditRepository`)
- Database + migrations (`001_init.sql`)
- Adapters (Telegram, Discord, Slack, Reddit, Eval)

## Commands

| Command | Description |
|---------|-------------|
| `/report` | Start a bug/feature/question report wizard |
| `/onboard` | Start the profile setup wizard (city + language) |
| `/cancel` | Cancel the active workflow |

### Example Usage

```
User: /report
Bot:  What category? (bug, feature, question)

User: bug
Bot:  Please describe the issue.

User: It does not start.
Bot:  Confirm report?
      Category: bug
      Description: It does not start.

      Reply 'yes' to submit or /cancel to abort.

User: yes
Bot:  Report submitted.
      Category: bug
      Description: It does not start.
```

## Setup

```powershell
cd week3-state-machine-bot
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e .[dev]
copy .env.example .env   # fill in tokens
```

No additional API keys are required for the state machine. Add platform tokens to enable Telegram/Discord/Slack/Reddit adapters.

## Run

```powershell
python -m bot.main
```

## Test

```powershell
pytest
```

## Database Schema

`migrations/003_state.sql` adds:

- **conversation_states**: workflow, state, data, status

## Deployment

The included `Dockerfile` works without changes.

## What This Teaches

| Concept | Implementation |
|---------|----------------|
| **Multi-step workflows** | `StateMachine` with `Workflow` and `Transition` |
| **Conversation state persistence** | `conversation_states` table |
| **Middleware-driven routing** | `state_middleware` rewrites free-form text to `__state__` |
| **Reusable state engine** | Same core serves `/report`, `/onboard`, and future workflows |
| **Graceful error handling** | Invalid inputs keep the user in the same state |

## Metrics

- New commands: 3 (`/report`, `/onboard`, `/cancel`)
- New workflows: 2
- New tables: 1
- New tests: 3
- Total tests: 32/32 passing
