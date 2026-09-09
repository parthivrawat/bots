"""Eval runner: loads case files, executes them against a bot, scores results."""

from __future__ import annotations

import json
import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable, Optional

from .checks import run_checks
from .models import BotCallable, BotResponse, EvalCase, EvalResult, EvalSummary
from .pricing import estimate_cost_usd

logger = logging.getLogger(__name__)


def load_cases(path: str | Path) -> list[EvalCase]:
    """Load eval cases from a JSON file.

    Accepted formats:
      - a list of case objects
      - {"suite": "name", "cases": [...]}

    Returns the parsed cases; suite name is attached via load_suite().
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_cases = data["cases"] if isinstance(data, dict) else data
    cases = [EvalCase.from_dict(c) for c in raw_cases]
    ids = [c.id for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate case ids in {path}")
    return cases


def load_suite(path: str | Path) -> tuple[str, list[EvalCase]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    name = data.get("suite", Path(path).stem) if isinstance(data, dict) else Path(path).stem
    return name, load_cases(path)


def _run_one(bot: BotCallable, case: EvalCase, timeout_s: float) -> EvalResult:
    start = time.perf_counter()
    result = EvalResult(case=case, response=None)
    try:
        response = bot(case.input, case.context)
        if not isinstance(response, BotResponse):
            raise TypeError(
                f"bot returned {type(response).__name__}, expected BotResponse. "
                "Wrap your bot's output in framework.models.BotResponse."
            )
        result.response = response
    except Exception as exc:  # noqa: BLE001 — eval must record, not crash
        result.error = f"{type(exc).__name__}: {exc}"
        result.latency_ms = (time.perf_counter() - start) * 1000
        return result

    result.latency_ms = (time.perf_counter() - start) * 1000
    result.cost_usd = estimate_cost_usd(
        response.model, response.input_tokens, response.output_tokens
    )

    result.checks = run_checks(case, response)

    # Latency / cost budgets are evaluated here because they need runtime values
    exp = case.expected
    if exp.max_latency_ms is not None:
        ok = result.latency_ms <= exp.max_latency_ms
        from .models import CheckResult
        result.checks.append(CheckResult(
            name=f"max_latency_ms<={exp.max_latency_ms}", passed=ok,
            detail=f"actual {result.latency_ms:.0f}ms",
        ))
    if exp.max_cost_usd is not None:
        ok = result.cost_usd <= exp.max_cost_usd
        from .models import CheckResult
        result.checks.append(CheckResult(
            name=f"max_cost_usd<={exp.max_cost_usd}", passed=ok,
            detail=f"actual ${result.cost_usd:.5f}",
        ))
    return result


def run_evals(
    bot: BotCallable,
    cases: Iterable[EvalCase],
    suite_name: str = "eval-suite",
    *,
    concurrency: int = 1,
    timeout_s: float = 120.0,
    tags: Optional[list[str]] = None,
) -> EvalSummary:
    """Run cases against a bot callable and return a scored summary.

    Args:
        bot:         callable(message, context) -> BotResponse
        cases:       EvalCase iterable
        suite_name:  label for reports
        concurrency: parallel workers (keep 1 for stateful bots / strict rate limits)
        timeout_s:   per-case timeout budget (advisory; enforced as a check)
        tags:        if set, only run cases carrying at least one of these tags
    """
    case_list = list(cases)
    if tags:
        wanted = set(tags)
        case_list = [c for c in case_list if wanted & set(c.tags)]

    summary = EvalSummary(suite_name=suite_name)
    if not case_list:
        logger.warning("No cases to run.")
        return summary

    if concurrency <= 1:
        for case in case_list:
            res = _run_one(bot, case, timeout_s)
            summary.results.append(res)
            logger.info("[%s] %s", "PASS" if res.passed else "FAIL", case.id)
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {pool.submit(_run_one, bot, c, timeout_s): c for c in case_list}
            for fut in as_completed(futures):
                res = fut.result()
                summary.results.append(res)
                logger.info("[%s] %s", "PASS" if res.passed else "FAIL", res.case.id)

    # Advisory timeout check: flag cases exceeding the budget
    for res in summary.results:
        if res.latency_ms > timeout_s * 1000:
            from .models import CheckResult
            res.checks.append(CheckResult(
                name=f"timeout_budget<{timeout_s}s", passed=False,
                detail=f"took {res.latency_ms / 1000:.1f}s",
            ))

    return summary


# ---------------------------------------------------------------------------
# Aggregates used by the report layer
# ---------------------------------------------------------------------------

def latency_stats(summary: EvalSummary) -> dict[str, float]:
    lats = sorted(summary.latencies_ms)
    if not lats:
        return {"p50": 0.0, "p95": 0.0, "mean": 0.0, "max": 0.0}

    def pct(p: float) -> float:
        idx = min(len(lats) - 1, max(0, int(round(p * (len(lats) - 1)))))
        return lats[idx]

    return {
        "p50": pct(0.50),
        "p95": pct(0.95),
        "mean": statistics.fmean(lats),
        "max": lats[-1],
    }


def tool_selection_accuracy(summary: EvalSummary) -> Optional[float]:
    """Fraction of cases where the exact required/forbidden tool checks passed."""
    relevant = [
        r for r in summary.results
        if r.case.expected.must_call_tools
        or r.case.expected.must_not_call_tools
        or r.case.expected.must_call_tools_in_order
    ]
    if not relevant:
        return None
    ok = sum(
        1 for r in relevant
        if all(c.passed for c in r.checks if "tool" in c.name)
    )
    return ok / len(relevant)
