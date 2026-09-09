# Evals — Reusable Bot/Agent Evaluation Framework

A zero-dependency (stdlib-only) framework for measuring whether your bots
actually work — usable from Phase 1 bots through Phase 7 multi-agent systems.

## Quick start

```powershell
cd E:\Bots\evals
python run_evals.py --cases cases/example_cases.json --target examples.demo_bot:bot
```

Exit code is `0` only when every case passes — wire this into CI.

## Adapting your bot

The framework only needs one contract: a callable `(message, context) -> BotResponse`.
Wrap your real bot in an adapter module:

```python
# my_adapter.py
from framework import BotResponse, ToolCall
from my_bot import handle_update  # your real bot entry point

def bot(message: str, context: dict) -> BotResponse:
    reply = handle_update(message, context)          # whatever your bot does
    return BotResponse(
        text=reply.text,
        tool_calls=[ToolCall(name=t.name, arguments=t.args) for t in reply.tools],
        input_tokens=reply.usage.in_toks,            # fill what you have
        output_tokens=reply.usage.out_toks,
        model=reply.model,
        metadata={
            "refused": reply.was_refusal,            # optional flags the checks read
            "escalated": reply.escalated,
            "retrieved_doc_ids": reply.source_ids,   # for RAG eval
        },
    )
```

```powershell
python run_evals.py --cases cases/my_cases.json --target my_adapter:bot
```

## Case file format

```json
{
  "suite": "my-suite",
  "cases": [
    {
      "id": "order-lookup",
      "input": "Where is my order #1234?",
      "description": "human-readable intent",
      "context": {"user_role": "customer"},
      "tags": ["tools"],
      "expected": { "...checks..." }
    }
  ]
}
```

### Available checks (`expected` block)

| Check | What it asserts |
|---|---|
| `must_contain` / `must_not_contain` | Case-insensitive substrings in reply text |
| `must_match_regex` | Regex patterns against reply text |
| `must_call_tools` | These tools were all invoked |
| `must_not_call_tools` | These tools were NOT invoked |
| `must_call_tools_in_order` | Ordered subsequence of tool calls |
| `max_tool_calls` | Bound on total tool invocations |
| `expect_refusal` | Refusal phrasing or `metadata["refused"]` |
| `expect_escalation` | `metadata["escalated"] == true` |
| `metadata_equals` | Arbitrary `metadata[key] == value` |
| `expect_valid_json` | Reply text parses as JSON |
| `json_schema_required_keys` | Parsed JSON object contains keys |
| `expected_retrieved_docs` | RAG: doc ids present in `metadata["retrieved_doc_ids"]` |
| `max_latency_ms` | Wall-clock latency budget |
| `max_cost_usd` | Token-cost budget (see `framework/pricing.py`) |

## Metrics computed per run

- Pass rate (overall and per tag)
- Error count (bot exceptions)
- Latency: p50 / p95 / mean / max
- Total token cost (update `framework/pricing.py` with current prices)
- Tool-selection accuracy (across tool-related cases)

## Writing good eval cases — checklist

For every project, cover these categories (see `example_cases.json`):

- [ ] **Happy paths** — the 3–5 most common user requests
- [ ] **Tool correctness** — right tool, right args, no forbidden calls
- [ ] **Safety** — destructive requests refused; injection attempts ignored
- [ ] **Escalation** — situations that must reach a human
- [ ] **Budgets** — latency and cost ceilings on cheap queries
- [ ] **Regression** — add a case every time you find a real failure

## CLI options

```
--cases PATH        case file (required)
--target MOD:FUNC   bot callable (required)
--concurrency N     parallel workers (default 1; use >1 for stateless bots)
--tags a,b          run only tagged cases
--out DIR           report output directory (default: results/)
--verbose           show passing check details too
```

## Extending

- **New check types**: add to `checks.py` + a field in `ExpectedBehavior` (models.py).
- **LLM-as-judge**: for open-ended quality (summary quality, tone), add a
  `llm_judge` check that calls a model with a rubric — keep it opt-in per case.
- **Hallucination scoring**: for RAG, compare `response.text` claims against
  retrieved docs — stub a check reading `metadata["retrieved_doc_ids"]`.
- **LangSmith/promptfoo**: this framework complements, not replaces, dedicated
  eval platforms — export `results/*.json` anywhere.

## Layout

```
evals/
├── framework/
│   ├── models.py    # EvalCase, ExpectedBehavior, BotResponse, results
│   ├── checks.py    # assertion implementations
│   ├── pricing.py   # per-model USD/1M token table (keep updated)
│   ├── runner.py    # load cases, execute, aggregate
│   └── report.py    # console + JSON + Markdown output
├── cases/           # one JSON file per project/suite
├── examples/        # demo bot adapter
├── results/         # generated reports (gitignored)
└── run_evals.py     # CLI
```
