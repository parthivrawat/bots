"""Eval-framework target for the week1-chatbot project.

Run from E:\\Bots\\evals:
    python run_evals.py --cases cases/week1_bot.json --target week1_adapter:bot
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "week1-chatbot" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.adapters.eval_adapter import bot  # noqa: F401,E402
