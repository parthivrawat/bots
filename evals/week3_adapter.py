"""Eval-framework target for the week3-state-machine-bot project.

Run from E:\\Bots\\evals:
    python run_evals.py --cases cases/week3_state.json --target week3_adapter:bot
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "week3-state-machine-bot" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.adapters.eval_adapter import bot  # noqa: F401,E402
