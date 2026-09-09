# Bot Development Roadmap — Theory + Building Plan

> **Goal**: Build increasingly autonomous bots that can understand requests, access data, use tools, make decisions, and safely take actions.
>
> **Progression**: Bot → AI Bot → RAG Bot → Tool-Using Agent → Autonomous Agent → Multi-Agent System

**Duration**: 12–16 weeks | **Projects**: ~15 | **Approach**: ~30% theory, ~70% building

---

## Overview Table

| Phase | Focus                    | Projects | Weeks   |
| ----- | ------------------------ | -------- | ------- |
| 1     | Bot fundamentals         | 2        | 1–2     |
| 2     | LLM-powered bots         | 2        | 3–4     |
| 3     | RAG & knowledge bots     | 2        | 5–6     |
| 4     | Tool-using agents        | 3        | 7–9     |
| 5     | Production agents        | 2        | 10–11   |
| 6     | Advanced agent patterns  | 2        | 12–13   |
| 7     | Multi-agent systems      | 1–2      | 14      |
| 8     | Production/business bots | Capstone | 15–16+  |

---

## Phase 1 — Bot Engineering Fundamentals (Weeks 1–2)

### Theory (~20%)
- Event-driven architecture (webhooks, event loops, async patterns)
- State management (sessions, persistence, user context)
- Bot lifecycle: Registration → Command handling → Response → State update
- Infrastructure: queues, background jobs, schedulers, retries, idempotency
- Rate limiting, authentication, audit logging

### Projects

**Project 1 — Telegram/Discord Bot (Week 1, no AI)**
```
User → /start → Bot → Command handler → Business logic → Database
```
- Commands: `/start`, `/help`, `/profile`, `/settings`
- User registration + persistent preferences
- Admin commands
- **Objective**: Understand the bot lifecycle

**Project 2 — Scheduled Automation Bot (Week 2)**
```
Scheduler → Fetch API data → Process → Generate report → Store → Send (Telegram/email)
```
- **Key insight**: Bots don't have to chat — they can observe → process → act

---

## Phase 2 — LLM-Powered Bots (Weeks 3–4)

### Theory (~30%)
- LLM fundamentals: system vs user messages, context windows, temperature
- Token management: cost tracking, context limits
- Structured output: JSON mode, function schemas
- Streaming responses
- Prompt engineering: system instructions, few-shot examples
- Model selection (speed vs capability), fallback strategies

### Projects

**Project 3 — Basic AI Chatbot (Week 3)**
```
User → Backend → LLM API → Response → User
```
- Conversation history, system instructions
- Streaming, token/cost tracking
- Error handling, conversation persistence

**Project 4 — Structured Output Bot (Week 4)**
- Example: Email/Resume Analyzer
- Input: raw text → Output: structured JSON
```json
{
  "intent": "complaint",
  "urgency": "high",
  "sentiment": "negative",
  "requires_human": true,
  "summary": "...",
  "suggested_reply": "..."
}
```
- **Key insight**: Use LLMs to produce structured data, not just prose

---

## Phase 3 — RAG & Knowledge Bots (Weeks 5–6)

### Theory (~40%)
- Embeddings: vector representations of text
- Chunking strategies: sentence, paragraph, semantic, overlap
- Vector databases: similarity search, metadata filtering
- Retrieval: top-k, reranking, hybrid search (keyword + semantic)
- Citation generation

### Projects

**Project 5 — PDF Knowledge Bot (Week 5)**
```
PDF → Extract text → Chunk → Embed → Vector DB → Retrieve → LLM → Answer
```
- Upload PDFs → ask questions with citations

**Project 6 — Company Knowledge Bot (Week 6)**
- Multi-format: PDFs, Markdown, web pages, FAQs, internal docs
- Access control: `Employee A → HR docs`, `Employee B → Eng docs`, `Admin → all`
- **Key insight**: Retrieval permissions must be enforced by your application, not trusted to the LLM

---

## Phase 4 — Tool-Using AI Agents (Weeks 7–9)

### Theory (~30%)
- Function calling: tool schemas, parameter validation
- Agent loops: ReAct pattern (Reason → Act → Observe)
- Tool orchestration, permissions, error recovery
- Multi-step planning, result synthesis

### Projects

**Project 7 — Tool-Calling Assistant (Week 7)**
```
User → AI → Tool → Result → AI → Answer
```
- Tools: `search_database()`, `get_weather()`, `calculate()`, `get_user()`
- Model decides which tool to call

**Project 8 — Database Agent (Week 8)**
```
Question → Intent → Generate query → Validate → Execute → Analyze → Answer
```
- **Critical**: Never blindly execute AI-generated operations
- Use: read-only connections, query validation, allowlisted operations, timeouts, row limits

**Project 9 — Research Agent (Week 9) — major project**
```
User → Research Agent → Search/Read/Extract → Analyze → Synthesize → Report
```
- Tools: `search_web()`, `fetch_page()`, `extract_content()`, `save_source()`
- Output: summary, findings, comparison, sources, recommendations
- **This is a true AI agent**

---

## Phase 5 — Production-Grade Agents (Weeks 10–11)

### Theory (~50%)
- Observability: logging, tracing, monitoring
- Evaluation: accuracy, hallucination detection, cost tracking
- Human handoff / escalation patterns
- Reliability: retries, circuit breakers, graceful degradation

### Projects

**Project 10 — Customer Support Agent (Week 10)**
```
Customer → Support Agent → Understand → Search KB → Check data → Resolve?
                                                              ↙       ↘
                                                            YES        NO
                                                             ↓          ↓
                                                          Answer     Human
```
- Tools: `get_customer()`, `get_order()`, `search_knowledge()`, `create_ticket()`, `send_email()`
- Auth, audit logs, human handoff, rate limiting, tool permissions, monitoring

**Project 11 — Agent Evaluation System (Week 11) — critical**
- Test cases with expected behaviors (e.g., "Delete all customers" → Refuse)
- Metrics: accuracy, tool-selection accuracy, hallucination rate, latency, cost, failure rate, retrieval quality
- **Key insight**: AI engineering = software engineering + probabilistic systems + evaluation

---

## Phase 6 — Advanced Agent Architecture (Weeks 12–13)

### Theory (~40%)
- Planning patterns: planner-executor separation
- Human-in-the-loop: approval gates for consequential actions
- State machines: explicit workflow control
- Reflection: agent self-critique

### Projects

**Project 12 — Planner + Executor Agent (Week 12)**
```
User → Planner → Task Plan → Executor → Tools → Results → Planner → Final Answer
```
- Example: "Prepare a market analysis for three competitors"

**Project 13 — Human-in-the-Loop Agent (Week 13)**
```
Generate email → Show user → APPROVE? → YES: Send / NO: Modify
```
- Approval gates for potentially consequential actions — a production requirement

---

## Phase 7 — Multi-Agent Systems (Week 14)

### Theory (~50%)
- Agent coordination: manager-worker patterns
- Specialization: role-based agents
- When NOT to use multi-agent: latency, cost, failure modes, debugging difficulty

### Projects

**Project 14 — Multi-Agent Research Team**
```
        Manager
           ↓
    ┌──────┼──────┐
    ↓      ↓      ↓
Researcher Analyst Critic
    └──────┼──────┘
           ↓
        Writer → Report
```

**Project 15 — Agent Swarm Experiment (optional)**
- Dynamic delegation: coordinator spawns agents as needed
- **Key insight**: A single well-designed agent with good tools is often better. Use multi-agent only when specialization or parallelism genuinely helps.

---

## Phase 8 — Build Something Real (Weeks 15–16+)

### Capstone — choose one:

1. **Business Automation Agent**
   ```
   Incoming request → Classification → Research → DB lookup → Decision
   → Generate response → Human approval → Action → Audit log
   ```

2. **Coding Agent**
   ```
   Read repo → Understand → Find files → Modify → Run tests
   → Inspect failures → Fix → Retest
   ```

3. **Data Analyst Agent**
   ```
   Load data → Understand schema → Analyze → Metrics → Charts
   → Anomalies → Report
   ```

---

## Critical Architectural Patterns

### 1. Event-Driven Bot
`User Event → Handler → Business Logic → State Update → Response`

### 2. RAG Pipeline
`Query → Embedding → Vector Search → Top-K → Rerank → Context → LLM → Answer + Citations`

### 3. ReAct Agent Loop
`Request → Thought → Action (tool) → Observation → Thought → ... → Final Answer`

### 4. Planner-Executor
`Request → Planner → Task Plan → Executor → Results → Planner (review) → Answer`

### 5. Human-in-the-Loop
`Agent Action → Consequential? → YES → Show user → Approve? → Execute / Modify / Cancel`

### 6. Multi-Agent Coordination
`Manager → Specialized agents → Synthesizer → Result`

---

## Core Concepts Checklist

### LLM Fundamentals
- [ ] Prompting (system/user/few-shot/CoT)
- [ ] Context windows & token management
- [ ] Structured output & tool calling
- [ ] Streaming
- [ ] Model selection & cost optimization

### RAG
- [ ] Embeddings
- [ ] Chunking strategies
- [ ] Retrieval (top-k, metadata filtering)
- [ ] Reranking & hybrid search
- [ ] Citation generation

### Agents
- [ ] Tool use & validation
- [ ] Planning (ReAct loops)
- [ ] State machines
- [ ] Memory (short-term & long-term)
- [ ] Human approval / reflection / delegation

### Software Engineering
- [ ] Async processing & queues
- [ ] Retries & idempotency
- [ ] Authentication & authorization
- [ ] Rate limiting
- [ ] Observability & testing

### AI-Specific Engineering
- [ ] Evaluation frameworks
- [ ] Hallucination detection
- [ ] Prompt/version management
- [ ] Guardrails
- [ ] Cost & latency optimization
- [ ] Failure recovery

---

## Technology Stack

| Layer       | Choice                                                        |
| ----------- | ------------------------------------------------------------- |
| Language    | Python (AI/agent work) + existing stack for app code          |
| Backend     | FastAPI (or existing framework)                               |
| LLM APIs    | OpenAI / Anthropic / open-source via Ollama                   |
| Database    | PostgreSQL + pgvector (vector search without separate DB)     |
| Cache/Queue | Redis + Celery (or equivalent)                                |
| Infra       | Docker, background workers, cron/schedulers                   |
| Monitoring  | Structured logging, Prometheus/Grafana or Datadog             |
| Frameworks  | **Start without one** → then evaluate LangGraph, OpenAI Agents SDK, LlamaIndex, CrewAI |

> Frameworks should make your architecture easier — not hide it from you.

---

## Project Documentation Template

Every project → GitHub repo with:

```
project-name/
├── README.md          # Overview, architecture diagram, setup, env vars,
│                      # usage examples, limitations
├── docs/
│   ├── architecture.md
│   ├── evaluation-results.md
│   └── failure-cases.md
├── src/
├── tests/
├── .env.example
└── docker-compose.yml
```

---

## Success Metrics (track per project)

- **Functional**: solves the problem, handles edge cases, fails gracefully
- **Quality**: accuracy, hallucination rate, tool-selection accuracy, latency (p50/p95/p99), cost per interaction
- **Engineering**: test coverage, error handling, observability, documentation

---

## Critical Lessons

1. **Don't trust AI blindly** — validate generated queries/actions; read-only DB connections; approval gates for consequential actions.
2. **Evaluation is not optional** — build eval systems alongside agents.
3. **Simplicity > complexity** — one well-designed agent > many poorly coordinated ones.
4. **Production is different** — observability, reliability, security, cost management.
5. **Retrieval permissions matter** — enforce access control in the application, never the LLM.

---

## Weekly Rhythm

- **Mon–Tue (~30%)**: Read docs/articles on the week's concepts; understand the *why*
- **Wed–Sun (~70%)**: Build, experiment, document, test, deploy

## Companion Files in This Repo

- `LEARNING_RESOURCES.md` — docs, papers, tutorials organized by phase
- `evals/` — reusable evaluation framework (`cd evals && python run_evals.py --cases cases/example_cases.json --target examples.demo_bot:bot`). Write a case file per project; wire into CI — exit code 0 only on full pass.

## Week 1 Action Plan

1. **Day 1–2**: Pick platform (Telegram/Discord), create bot account, set up env, read API docs (webhooks, commands, state)
2. **Day 3–5**: Command handlers (`/start`, `/help`, `/profile`), user registration + DB, preferences, admin commands
3. **Day 6–7**: Error handling, rate limiting, logging, docs, deploy
4. **Deliverable**: GitHub repo + working deployed bot + architecture diagram
