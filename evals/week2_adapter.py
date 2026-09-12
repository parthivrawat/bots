"""Eval-framework target for the week2-scheduled-bot project.

Run from E:\\Bots\\evals:
    python run_evals.py --cases cases/week2_jobs.json --target week2_adapter:bot
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "week2-scheduled-bot" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.adapters.eval_adapter import bot  # noqa: F401,E402
