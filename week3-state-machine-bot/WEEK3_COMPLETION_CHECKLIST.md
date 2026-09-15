# Week 3 Completion Checklist

Multi-step conversation state machine built on the Week 1 core.

## Core Functionality

- [x] **State machine engine (`src/bot/core/state_machine.py`)**
  - [x] `Workflow` and `Transition` dataclasses
  - [x] `StateMachine` supports `start` and `advance`
  - [x] `__done__` terminal state

- [x] **Conversation persistence (`src/bot/db/repositories/state_repo.py`)**
  - [x] `conversation_states` table via `migrations/003_state.sql`
  - [x] `start`, `get_active`, `update`, `set_status`

- [x] **State middleware (`src/bot/core/middleware/state.py`)**
  - [x] Detects active conversation
  - [x] Routes free-form text to `__state__` command
  - [x] Lets explicit commands (e.g. `/cancel`, `/help`) pass through

- [x] **StateService (`src/bot/services/state_service.py`)**
  - [x] `start`, `advance`, `cancel`
  - [x] Persists each state transition

- [x] **Workflows**
  - [x] `/report` — bug/feature/question report
  - [x] `/onboard` — city + language profile setup

- [x] **Wire-up**
  - [x] `app.py` registers `StateRepository`, `StateMachine`, `StateService`
  - [x] `Router` exposes `state_machine` attribute
  - [x] Middleware and `__state__` handler registered

## Testing

- [x] `tests/test_week3.py`:
  - [x] `/report` submits
  - [x] `/cancel` cancels
  - [x] `/onboard` saves city and language
- [x] `pytest` green: 32/32 passing

## Evals

- [x] `evals/cases/week3_state.json` with 4 cases
- [x] `evals/week3_adapter.py` target
- [x] `python run_evals.py --cases cases/week3_state.json --target week3_adapter:bot` passes 4/4

## Documentation

- [x] `README.md` with architecture, commands, examples, setup, and deployment
- [x] `pyproject.toml` names the package `week3-state-machine-bot`

## Deployment

- [x] `pyproject.toml` package name and dependencies updated
- [x] `Dockerfile` works without scheduled-job code

## Cleanup

- [x] Week 2 scheduled-bot files removed (jobs, fetchers, admin_jobs, alerts, subscribe, job_repo, job_service, migrations/002_jobs.sql, test_week2.py, WEEK2_COMPLETION_CHECKLIST.md)
- [x] Build artifacts removed (`debug.db`, old egg-info)

## Known Limitations

- One active conversation per user per workflow.
- Workflows are defined in handler files; a registry loader could be added later.
- State timeout/cleanup is not implemented.

---

Generated: 2026-09-14
