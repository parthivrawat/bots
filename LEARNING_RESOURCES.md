# Learning Resources — Bot & Agent Development

Companion to `BOT_DEV_ROADMAP.md`. Organized by phase so you can read theory alongside each project.

> ⚠️ Note: Links verified at creation time (Sept 2026). If a link breaks, search the title — official docs and arXiv papers are easy to relocate.

---

## 📌 Essential Starting Points (Read First)

| Resource | Type | Why |
|---|---|---|
| [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | Article | **The** best overview of agent patterns. Read before Phase 4 and again before Phase 6. |
| [OpenAI API Documentation](https://platform.openai.com/docs) | Docs | Chat completions, function calling, structured output, embeddings |
| [Anthropic Docs](https://docs.anthropic.com/) | Docs | Claude API, tool use, prompt engineering guides |
| [OpenAI Cookbook](https://github.com/openai/openai-cookbook) | Code examples | Working examples for RAG, function calling, agents, evals |
| [Prompt Engineering Guide (DAIR.AI)](https://www.promptingguide.ai/) | Guide | Prompting techniques: CoT, ReAct, few-shot, etc. |

---

## Phase 1 — Bot Engineering Fundamentals

### Platform Docs
| Resource | Type |
|---|---|
| [Telegram Bot API](https://core.telegram.org/bots/api) | Official API reference |
| [Telegram Bots: An introduction](https://core.telegram.org/bots) | Getting started, BotFather |
| [python-telegram-bot docs](https://docs.python-telegram-bot.org/) | Python library (recommended) |
| [aiogram docs](https://docs.aiogram.dev/) | Async Python Telegram framework (alternative) |
| [discord.py docs](https://discordpy.readthedocs.io/) | Python Discord library |
| [Discord Developer Portal](https://discord.com/developers/docs) | Official Discord API docs |

### Concepts
| Resource | Type |
|---|---|
| [FastAPI docs](https://fastapi.tiangolo.com/) | If building webhooks with FastAPI |
| [Celery docs](https://docs.celeryq.dev/) | Background tasks & scheduled jobs |
| [APScheduler docs](https://apscheduler.readthedocs.io/) | Lightweight in-process scheduling |
| [MDN — Webhooks concept](https://docs.github.com/en/webhooks) | GitHub's webhook docs are a good conceptual intro |
| [Idempotency (Stripe engineering)](https://stripe.com/docs/idempotent-requests) | How Stripe handles idempotent APIs — pattern worth copying |

---

## Phase 2 — LLM-Powered Bots

| Resource | Type | Topic |
|---|---|---|
| [OpenAI — Text generation & prompting](https://platform.openai.com/docs/guides/text-generation) | Docs | Messages, system prompts, temperature |
| [OpenAI — Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) | Docs | JSON schema enforcement |
| [OpenAI — Streaming](https://platform.openai.com/docs/api-reference/streaming) | Docs | Server-sent events |
| [Anthropic — Prompt engineering overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) | Docs | Techniques that generalize across models |
| [Anthropic — Token counting & costs](https://docs.anthropic.com/en/docs/about-claude/models) | Docs | Models, context windows, pricing |
| [Chain-of-Thought Prompting (paper)](https://arxiv.org/abs/2201.11903) | Paper | Foundational reasoning technique |
| [OpenAI Tokenizer tool](https://platform.openai.com/tokenizer) | Tool | See how text becomes tokens |
| [DeepLearning.AI Short Courses](https://www.deeplearning.ai/short-courses/) | Courses | "ChatGPT Prompt Engineering", "Building Systems with the ChatGPT API" |

---

## Phase 3 — RAG & Knowledge Bots

| Resource | Type | Topic |
|---|---|---|
| [RAG paper (Lewis et al., 2020)](https://arxiv.org/abs/2005.11401) | Paper | The original RAG formulation |
| [OpenAI — Embeddings guide](https://platform.openai.com/docs/guides/embeddings) | Docs | Creating and using embeddings |
| [pgvector](https://github.com/pgvector/pgvector) | Repo | Vector search inside PostgreSQL — start here |
| [pgvector Python examples](https://github.com/pgvector/pgvector-python) | Repo | SQLAlchemy/psycopg usage |
| [Sentence Transformers docs](https://www.sbert.net/) | Docs | Open-source embedding models |
| [Pinecone Learning Center — RAG](https://www.pinecone.io/learn/retrieval-augmented-generation/) | Guide | RAG concepts explained well |
| [Pinecone — Chunking strategies](https://www.pinecone.io/learn/chunking-strategies/) | Guide | Chunk size, overlap, semantic chunking |
| [Qdrant docs](https://qdrant.tech/documentation/) | Docs | Alternative open-source vector DB |
| [Weaviate — Hybrid search](https://weaviate.io/developers/weaviate/search/hybrid) | Docs | Keyword + semantic search |
| [Cohere — Rerank](https://docs.cohere.com/docs/rerank-overview) | Docs | Reranking retrieved chunks |
| [DeepLearning.AI — "Building & Evaluating Advanced RAG"](https://www.deeplearning.ai/short-courses/) | Course | RAG triad: relevance, groundedness, context |

---

## Phase 4 — Tool-Using Agents

| Resource | Type | Topic |
|---|---|---|
| [ReAct paper (Yao et al., 2022)](https://arxiv.org/abs/2210.03629) | Paper | Reason + Act loop — **foundational, read fully** |
| [ReAct project page](https://react-lm.github.io/) | Site | Examples and intuition |
| [Toolformer paper](https://arxiv.org/abs/2302.04761) | Paper | Models learning to use tools |
| [OpenAI — Function calling](https://platform.openai.com/docs/guides/function-calling) | Docs | Tool schemas, parallel calls |
| [Anthropic — Tool use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview) | Docs | Claude's tool-use API |
| [MRKL Systems paper](https://arxiv.org/abs/2205.00445) | Paper | Modular reasoning + tools architecture |
| [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | Article | Re-read now — workflows vs agents |
| [OpenAI Cookbook — agents examples](https://github.com/openai/openai-cookbook) | Code | Tool-calling agent patterns |

---

## Phase 5 — Production-Grade Agents

| Resource | Type | Topic |
|---|---|---|
| [OpenAI Evals repo](https://github.com/openai/evals) | Repo | Evaluation framework + examples |
| [RAGAS docs](https://docs.ragas.io/) | Docs | RAG-specific evaluation metrics |
| [promptfoo](https://www.promptfoo.dev/) | Tool | Prompt/agent testing & eval CLI |
| [LangSmith](https://docs.smith.langchain.com/) | Docs | Tracing + evals (works beyond LangChain) |
| [OpenTelemetry docs](https://opentelemetry.io/docs/) | Docs | Standard tracing/metrics instrumentation |
| [OpenLLMetry](https://github.com/traceloop/openllmetry) | Repo | OTel instrumentation for LLM calls |
| [OWASP Top 10 for LLM Apps](https://owasp.org/www-project-top-10-for-large-language-model-applications/) | Security | **Required reading** — prompt injection, tool abuse |
| [Simon Willison's blog — prompt injection](https://simonwillison.net/series/prompt-injection/) | Blog | Best practical writing on injection attacks |
| [Anthropic — Claude agents / customer support patterns](https://docs.anthropic.com/en/docs/agents-and-tools/overview) | Docs | Production tool-use guidance |
| [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) | Guide | Principles for production-grade agents |

---

## Phase 6 — Advanced Agent Patterns

| Resource | Type | Topic |
|---|---|---|
| [LangGraph docs](https://docs.langchain.com/oss/python/langgraph/overview) | Docs | State machines, durable execution, human-in-the-loop |
| [LangGraph — Workflows & agents patterns](https://docs.langchain.com/oss/python/langgraph/workflows-agents) | Guide | Planner-executor, orchestrator-worker, evaluator-optimizer |
| [Reflexion paper](https://arxiv.org/abs/2303.11366) | Paper | Self-critique and memory for agents |
| [Plan-and-Solve paper](https://arxiv.org/abs/2305.04091) | Paper | Planning before execution |
| [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) | Docs | Handoffs, guardrails, tracing |
| [HumanLayer](https://github.com/humanlayer/humanlayer) | Repo | Human-in-the-loop approval infra |
| [Lilian Weng — LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) | Blog | Comprehensive agent architecture survey — **essential** |

---

## Phase 7 — Multi-Agent Systems

| Resource | Type | Topic |
|---|---|---|
| [Microsoft AutoGen docs](https://microsoft.github.io/autogen/) | Docs | Multi-agent conversation framework |
| [CrewAI docs](https://docs.crewai.com/) | Docs | Role-based agent crews |
| [CAMEL paper](https://arxiv.org/abs/2303.17760) | Paper | Communicative agents framework |
| [MetaGPT paper](https://arxiv.org/abs/2308.00352) | Paper | Multi-agent software company simulation |
| [OpenAI — Swarm (educational)](https://github.com/openai/swarm) | Repo | Minimal multi-agent orchestration example |
| [Anthropic — multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system) | Article | How Anthropic built their multi-agent system — real production lessons |

---

## Phase 8 — Production & Capstone

| Resource | Type | Topic |
|---|---|---|
| [Building LLM applications for production (Huyen Chip)](https://huyenchip.com/2023/04/11/llm-engineering.html) | Blog | LLM engineering challenges in prod |
| [What We've Learned from a Year of Building with LLMs (O'Reilly)](https://www.oreilly.com/radar/what-we-learned-from-a-year-of-building-with-llms-part-i/) | Article series | 3-part series: tactical, operational, strategic lessons — **essential** |
| [Anthropic — Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | Article | Designing effective agent tools |
| [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) | Spec | Standard for connecting agents to tools/data |
| [Docker docs](https://docs.docker.com/) | Docs | Containerizing your bots |
| [Temporal docs](https://docs.temporal.io/) | Docs | Durable workflow execution (for long-running agents) |

---

## 📄 Foundational Papers — Reading Order

1. **[Attention Is All You Need](https://arxiv.org/abs/1706.03762)** (2017) — Transformer architecture (skim for context)
2. **[Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)** (2022) — Eliciting reasoning
3. **[RAG](https://arxiv.org/abs/2005.11401)** (2020) — Retrieval-augmented generation
4. **[ReAct](https://arxiv.org/abs/2210.03629)** (2022) — Reasoning + acting loop ⭐
5. **[Toolformer](https://arxiv.org/abs/2302.04761)** (2023) — Self-supervised tool use
6. **[Reflexion](https://arxiv.org/abs/2303.11366)** (2023) — Agents that learn from feedback
7. **[Generative Agents](https://arxiv.org/abs/2304.03442)** (2023) — Memory + planning + reflection (Stanford smallville)
8. **[CAMEL](https://arxiv.org/abs/2303.17760)** (2023) — Multi-agent communication

---

## 📚 Books & Long-Form

| Resource | Notes |
|---|---|
| [AI Engineering — Chip Huyen (O'Reilly, 2025)](https://www.oreilly.com/library/view/ai-engineering/9781098166298/) | Best single book covering evals, RAG, agents, production |
| [Building LLMs for Production](https://www.amazon.com/dp/B0D4FFPFB8) | Prompting → RAG → agents, hands-on |
| [LLM Engineer's Handbook](https://www.amazon.com/dp/1836200062) | RAG pipelines + production deployment |
| [Hugging Face NLP Course](https://huggingface.co/learn/nlp-course) | Free — embeddings and transformers fundamentals |

---

## 📰 Blogs & Newsletters (Stay Current)

| Source | Focus |
|---|---|
| [Anthropic Engineering Blog](https://www.anthropic.com/engineering) | Agent design, production lessons |
| [OpenAI Blog](https://openai.com/index/) | New capabilities, guides |
| [Simon Willison's Weblog](https://simonwillison.net/) | Practical LLM engineering, security |
| [Lilian Weng — Lil'Log](https://lilianweng.github.io/) | Deep technical surveys |
| [Chip Huyen's Blog](https://huyenchip.com/) | ML systems, LLM production |
| [Eugene Yan's Blog](https://eugeneyan.com/) | Applied LLM/eval patterns |
| [Hamel Husain's Blog](https://hamel.dev/) | Evals and fine-tuning pragmatics |

---

## 🎓 Structured Courses (Optional)

| Course | Provider | Phase fit |
|---|---|---|
| [DeepLearning.AI Short Courses](https://www.deeplearning.ai/short-courses/) | DeepLearning.AI | Phases 2–6 (free, 1–2 hrs each) — search for "agents", "RAG", "evals" |
| [Hugging Face Agents Course](https://huggingface.co/learn/agents-course) | Hugging Face | Phases 4–7 — free, certificate |
| [Full Stack Deep Learning — LLM Bootcamp](https://fullstackdeeplearning.com/llm-bootcamp/) | FSDL | Phases 5–8 |

---

## 🛠️ Suggested Usage

1. **Before each phase**: read the linked docs/articles for that week (~2–3 hrs)
2. **During building**: keep the official API docs open; use the Cookbook for working code
3. **Papers**: read abstracts for all; full read only for ⭐ foundational ones (ReAct, RAG)
4. **Blogs**: subscribe to 2–3 (recommended: Willison, Anthropic, Weng) rather than all
5. **Security**: read the OWASP LLM Top 10 before deploying anything with tool use
