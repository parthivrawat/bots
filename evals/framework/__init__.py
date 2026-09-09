"""Reusable bot/agent evaluation framework.

Usage:
    from framework import BotResponse, ToolCall, load_suite, run_evals
    from framework.report import print_console, save_json, save_markdown
"""

from .models import (
    BotCallable,
    BotResponse,
    CheckResult,
    EvalCase,
    EvalResult,
    EvalSummary,
    ExpectedBehavior,
    ToolCall,
)
from .pricing import estimate_cost_usd
from .runner import load_cases, load_suite, run_evals

__all__ = [
    "BotCallable",
    "BotResponse",
    "CheckResult",
    "EvalCase",
    "EvalResult",
    "EvalSummary",
    "ExpectedBehavior",
    "ToolCall",
    "estimate_cost_usd",
    "load_cases",
    "load_suite",
    "run_evals",
]
