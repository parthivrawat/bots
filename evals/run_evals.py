"""CLI entry point for the eval framework.

Usage:
    python run_evals.py --cases cases/example_cases.json --target examples.demo_bot:bot
    python run_evals.py --cases cases/example_cases.json --target examples.demo_bot:bot \
        --concurrency 4 --tags safety,injection --out results --verbose
"""

from __future__ import annotations

import argparse
import importlib
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from framework import BotCallable, load_suite, run_evals  # noqa: E402
from framework.report import print_console, save_json, save_markdown  # noqa: E402


def load_target(spec: str) -> BotCallable:
    """Import 'module.submodule:function_name' and return the callable."""
    if ":" not in spec:
        raise SystemExit("--target must be in 'module:function' form, e.g. examples.demo_bot:bot")
    mod_name, func_name = spec.split(":", 1)
    try:
        mod = importlib.import_module(mod_name)
    except ImportError as exc:
        raise SystemExit(f"Could not import '{mod_name}': {exc}")
    fn = getattr(mod, func_name, None)
    if not callable(fn):
        raise SystemExit(f"'{spec}' is not callable")
    return fn


def main() -> int:
    p = argparse.ArgumentParser(description="Run bot/agent eval cases.")
    p.add_argument("--cases", required=True, help="Path to JSON case file")
    p.add_argument("--target", required=True, help="Bot callable as 'module:function'")
    p.add_argument("--concurrency", type=int, default=1)
    p.add_argument("--tags", default=None, help="Comma-separated tag filter")
    p.add_argument("--out", default="results", help="Output dir for JSON/Markdown reports")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    suite_name, cases = load_suite(args.cases)
    bot = load_target(args.target)

    summary = run_evals(
        bot, cases, suite_name=suite_name,
        concurrency=args.concurrency,
        tags=args.tags.split(",") if args.tags else None,
    )

    print_console(summary, verbose=args.verbose)
    json_path = save_json(summary, args.out)
    md_path = save_markdown(summary, args.out)
    print(f"Reports written:\n  {json_path}\n  {md_path}")

    return 0 if summary.error_count == 0 and summary.pass_rate >= 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
