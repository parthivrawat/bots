"""Data models for the bot evaluation framework.

The framework is intentionally transport-agnostic: your bot under test is any
callable that accepts a message (+ optional context) and returns a BotResponse.
Works for Telegram bots, RAG bots, tool-using agents, and multi-agent systems.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Bot contract
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    """A single tool/function invocation made by the bot."""

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class BotResponse:
    """What your bot returns for evaluation.

    All fields except `text` are optional — fill in what your system produces.
    The more you provide, the more the framework can measure.
    """

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    # e.g. metadata={"retrieved_doc_ids": [...], "escalated": True, "refused": True}


# The bot under test: message + context -> BotResponse
BotCallable = Callable[[str, dict[str, Any]], BotResponse]


# ---------------------------------------------------------------------------
# Eval case definition (loaded from JSON case files)
# ---------------------------------------------------------------------------

@dataclass
class ExpectedBehavior:
    """Declarative assertions about what a correct response looks like.

    Every field is optional; a case passes when ALL specified checks pass.
    """

    # Text checks
    must_contain: list[str] = field(default_factory=list)       # case-insensitive substrings
    must_not_contain: list[str] = field(default_factory=list)
    must_match_regex: list[str] = field(default_factory=list)

    # Tool checks
    must_call_tools: list[str] = field(default_factory=list)    # all must appear
    must_not_call_tools: list[str] = field(default_factory=list)
    must_call_tools_in_order: list[str] = field(default_factory=list)  # ordered subsequence

    # Behavior flags (checked against response.metadata)
    expect_refusal: bool = False          # response must look like a refusal
    expect_escalation: bool = False       # metadata["escalated"] must be True
    metadata_equals: dict[str, Any] = field(default_factory=dict)

    # Performance / cost budgets
    max_latency_ms: Optional[float] = None
    max_cost_usd: Optional[float] = None
    max_tool_calls: Optional[int] = None

    # Output structure
    expect_valid_json: bool = False       # response text must parse as JSON
    json_schema_required_keys: list[str] = field(default_factory=list)

    # Retrieval quality (for RAG bots): expected doc ids vs metadata["retrieved_doc_ids"]
    expected_retrieved_docs: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ExpectedBehavior":
        known = {f for f in ExpectedBehavior.__dataclass_fields__}
        unknown = set(d) - known
        if unknown:
            raise ValueError(f"Unknown expected-behavior keys: {sorted(unknown)}")
        return ExpectedBehavior(**d)


@dataclass
class EvalCase:
    id: str
    input: str
    expected: ExpectedBehavior
    context: dict[str, Any] = field(default_factory=dict)  # e.g. user role, session state
    tags: list[str] = field(default_factory=list)
    description: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "EvalCase":
        return EvalCase(
            id=d["id"],
            input=d["input"],
            expected=ExpectedBehavior.from_dict(d.get("expected", {})),
            context=d.get("context", {}),
            tags=d.get("tags", []),
            description=d.get("description", ""),
        )


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class EvalResult:
    case: EvalCase
    response: Optional[BotResponse]
    checks: list[CheckResult] = field(default_factory=list)
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.error is None and all(c.passed for c in self.checks)


@dataclass
class EvalSummary:
    suite_name: str
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    started_at: float = field(default_factory=time.time)
    results: list[EvalResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    @property
    def latencies_ms(self) -> list[float]:
        return [r.latency_ms for r in self.results if r.error is None]

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.results)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.error is not None)

    def by_tag(self, tag: str) -> list[EvalResult]:
        return [r for r in self.results if tag in r.case.tags]
