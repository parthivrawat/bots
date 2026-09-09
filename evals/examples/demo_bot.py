"""Demo bot showing how to adapt ANY bot to the eval framework's contract.

Replace `handle()` internals with calls into your real bot. The framework only
cares that you return a BotResponse with whatever fields your system produces.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from framework import BotResponse, ToolCall  # noqa: E402


def handle(message: str, context: dict) -> BotResponse:
    """Toy rule-based bot — stands in for a real agent during setup."""
    text = message.lower()
    calls: list[ToolCall] = []
    meta: dict = {}

    time.sleep(0.02)  # simulate some work

    if text.startswith("analyze:"):
        meta["mode"] = "analyze"
        return BotResponse(
            text=json.dumps({
                "intent": "complaint",
                "urgency": "high",
                "sentiment": "negative",
                "requires_human": True,
            }),
            tool_calls=calls,
            input_tokens=40, output_tokens=25,
            model="gpt-4o-mini",
            metadata=meta,
        )

    if "order" in text and "#" in text:
        order_id = text.split("#")[1].rstrip("?.! ")
        calls.append(ToolCall(name="get_order", arguments={"order_id": order_id}))
        return BotResponse(
            text=f"Order #{order_id} is in transit and arrives Friday.",
            tool_calls=calls, input_tokens=30, output_tokens=20,
            model="gpt-4o-mini", metadata=meta,
        )

    if "refund" in text:
        calls.append(ToolCall(name="search_knowledge", arguments={"q": "refund policy"}))
        meta["retrieved_doc_ids"] = ["refund-policy-v2"]
        return BotResponse(
            text="Our refund policy allows returns within 30 days.",
            tool_calls=calls, input_tokens=50, output_tokens=30,
            model="gpt-4o-mini", metadata=meta,
        )

    if "delete all" in text or "ignore your previous instructions" in text:
        if "delete all" in text:
            meta["refused"] = True
            return BotResponse(
                text="I can't perform destructive actions like that.",
                tool_calls=calls, input_tokens=25, output_tokens=15,
                model="gpt-4o-mini", metadata=meta,
            )
        # Injection inside an ANALYZE payload still gets analyzed safely
        meta["mode"] = "analyze"
        return BotResponse(
            text=json.dumps({"intent": "phishing", "urgency": "low",
                             "sentiment": "neutral", "requires_human": False}),
            input_tokens=60, output_tokens=25, model="gpt-4o-mini", metadata=meta,
        )

    if "lawyer" in text:
        meta["escalated"] = True
        return BotResponse(
            text="I'm connecting you with a human support agent right away.",
            input_tokens=30, output_tokens=15, model="gpt-4o-mini", metadata=meta,
        )

    if "support hours" in text:
        return BotResponse(
            text="Our support team is available 9am-6pm weekdays.",
            input_tokens=20, output_tokens=12, model="gpt-4o-mini", metadata=meta,
        )

    return BotResponse(
        text="Hello! How can I help you today?",
        input_tokens=15, output_tokens=10, model="gpt-4o-mini", metadata=meta,
    )


def bot(message: str, context: dict) -> BotResponse:
    """Eval entry point signature: (message, context) -> BotResponse."""
    return handle(message, context)
