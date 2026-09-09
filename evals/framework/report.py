"""Reporting: console table, JSON dump, and Markdown report generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import EvalSummary
from .runner import latency_stats, tool_selection_accuracy


def print_console(summary: EvalSummary, verbose: bool = False) -> None:
    """Print a compact results table to stdout."""
    stats = latency_stats(summary)
    tsa = tool_selection_accuracy(summary)

    print(f"\n{'=' * 70}")
    print(f"  EVAL SUITE: {summary.suite_name}   (run {summary.run_id})")
    print(f"{'=' * 70}")

    for r in summary.results:
        mark = "PASS" if r.passed else ("ERR " if r.error else "FAIL")
        line = f"  [{mark}] {r.case.id:<32} {r.latency_ms:>7.0f}ms  ${r.cost_usd:.4f}"
        if r.case.tags:
            line += f"   ({', '.join(r.case.tags)})"
        print(line)
        if r.error:
            print(f"         error: {r.error}")
        if verbose or not r.passed:
            for c in r.checks:
                if not c.passed:
                    print(f"         x {c.name}  {c.detail}")

    print(f"{'-' * 70}")
    print(f"  Pass rate:      {summary.passed}/{summary.total}  ({summary.pass_rate:.0%})")
    print(f"  Errors:         {summary.error_count}")
    print(f"  Latency ms:     p50={stats['p50']:.0f}  p95={stats['p95']:.0f}  "
          f"mean={stats['mean']:.0f}  max={stats['max']:.0f}")
    print(f"  Total cost:     ${summary.total_cost_usd:.4f}")
    if tsa is not None:
        print(f"  Tool accuracy:  {tsa:.0%}  (of {sum(1 for r in summary.results if r.case.expected.must_call_tools or r.case.expected.must_not_call_tools or r.case.expected.must_call_tools_in_order)} tool cases)")
    print(f"{'=' * 70}\n")


def to_dict(summary: EvalSummary) -> dict:
    stats = latency_stats(summary)
    return {
        "suite": summary.suite_name,
        "run_id": summary.run_id,
        "timestamp": datetime.fromtimestamp(summary.started_at, tz=timezone.utc).isoformat(),
        "metrics": {
            "total": summary.total,
            "passed": summary.passed,
            "pass_rate": round(summary.pass_rate, 4),
            "errors": summary.error_count,
            "latency_ms": {k: round(v, 1) for k, v in stats.items()},
            "total_cost_usd": round(summary.total_cost_usd, 6),
            "tool_selection_accuracy": (
                round(tool_selection_accuracy(summary), 4)
                if tool_selection_accuracy(summary) is not None else None
            ),
        },
        "results": [
            {
                "id": r.case.id,
                "input": r.case.input,
                "tags": r.case.tags,
                "passed": r.passed,
                "error": r.error,
                "latency_ms": round(r.latency_ms, 1),
                "cost_usd": round(r.cost_usd, 6),
                "response_text": (r.response.text[:500] if r.response else None),
                "tool_calls": (
                    [{"name": t.name, "args": t.arguments} for t in r.response.tool_calls]
                    if r.response else []
                ),
                "failed_checks": [
                    {"check": c.name, "detail": c.detail}
                    for c in r.checks if not c.passed
                ],
            }
            for r in summary.results
        ],
    }


def save_json(summary: EvalSummary, out_dir: str | Path) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"eval-{summary.run_id}.json"
    path.write_text(json.dumps(to_dict(summary), indent=2), encoding="utf-8")
    return path


def save_markdown(summary: EvalSummary, out_dir: str | Path) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"eval-{summary.run_id}.md"
    d = to_dict(summary)
    m = d["metrics"]

    lines = [
        f"# Eval Report — {d['suite']}",
        "",
        f"- **Run**: `{d['run_id']}` at {d['timestamp']}",
        f"- **Pass rate**: {m['passed']}/{m['total']} ({m['pass_rate']:.0%})",
        f"- **Errors**: {m['errors']}",
        f"- **Latency (ms)**: p50={m['latency_ms']['p50']}, p95={m['latency_ms']['p95']}, "
        f"mean={m['latency_ms']['mean']}, max={m['latency_ms']['max']}",
        f"- **Total cost**: ${m['total_cost_usd']:.4f}",
    ]
    if m["tool_selection_accuracy"] is not None:
        lines.append(f"- **Tool-selection accuracy**: {m['tool_selection_accuracy']:.0%}")
    lines += ["", "## Results", "", "| Case | Status | Latency | Cost | Failed checks |",
              "|---|---|---|---|---|"]
    for r in d["results"]:
        status = "PASS" if r["passed"] else ("ERROR" if r["error"] else "FAIL")
        failed = "; ".join(c["check"] for c in r["failed_checks"]) or "-"
        lines.append(
            f"| `{r['id']}` | {status} | {r['latency_ms']:.0f}ms | ${r['cost_usd']:.4f} | {failed} |"
        )
    lines += ["", "## Failure details", ""]
    for r in d["results"]:
        if r["passed"]:
            continue
        lines.append(f"### `{r['id']}`")
        lines.append(f"- **Input**: {r['input']}")
        if r["error"]:
            lines.append(f"- **Error**: {r['error']}")
        for c in r["failed_checks"]:
            lines.append(f"- **{c['check']}**: {c['detail']}")
        if r["response_text"]:
            lines.append(f"- **Response**: {r['response_text'][:300]}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
