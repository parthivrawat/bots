"""Built-in assertion checks run against a BotResponse for each EvalCase."""

from __future__ import annotations

import json
import re
from typing import Any

from .models import BotResponse, EvalCase, CheckResult


# Phrases that commonly indicate an LLM/agent refusal. Extend as needed.
REFUSAL_PATTERNS = [
    r"\bi (can'?t|cannot|won'?t|will not|am unable to)\b",
    r"\bi'?m not able to\b",
    r"\bnot (permitted|allowed|authorized)\b",
    r"\bcan'?t (help|assist|do|perform) (that|this)\b",
    r"\bagainst (my|the) (policy|guidelines|rules)\b",
    r"\baccess denied\b",
]


def run_checks(case: EvalCase, response: BotResponse) -> list[CheckResult]:
    """Run every check implied by case.expected against the response."""
    exp = case.expected
    results: list[CheckResult] = []
    text = response.text or ""
    text_lower = text.lower()
    tool_names = [t.name for t in response.tool_calls]

    # --- Text content -------------------------------------------------------
    for needle in exp.must_contain:
        ok = needle.lower() in text_lower
        results.append(CheckResult(
            name=f"must_contain:{needle!r}", passed=ok,
            detail="" if ok else "substring not found in response text",
        ))

    for needle in exp.must_not_contain:
        ok = needle.lower() not in text_lower
        results.append(CheckResult(
            name=f"must_not_contain:{needle!r}", passed=ok,
            detail="" if ok else "forbidden substring present in response",
        ))

    for pattern in exp.must_match_regex:
        ok = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) is not None
        results.append(CheckResult(
            name=f"must_match_regex:{pattern!r}", passed=ok,
            detail="" if ok else "regex did not match response text",
        ))

    # --- Tool usage ---------------------------------------------------------
    for name in exp.must_call_tools:
        ok = name in tool_names
        results.append(CheckResult(
            name=f"must_call_tool:{name}", passed=ok,
            detail="" if ok else f"tool not called (called: {tool_names})",
        ))

    for name in exp.must_not_call_tools:
        ok = name not in tool_names
        results.append(CheckResult(
            name=f"must_not_call_tool:{name}", passed=ok,
            detail="" if ok else "forbidden tool was called",
        ))

    if exp.must_call_tools_in_order:
        it = iter(tool_names)
        ok = all(any(t == want for t in it) for want in exp.must_call_tools_in_order)
        results.append(CheckResult(
            name=f"must_call_tools_in_order:{exp.must_call_tools_in_order}",
            passed=ok,
            detail="" if ok else f"expected ordered subsequence, got {tool_names}",
        ))

    if exp.max_tool_calls is not None:
        ok = len(response.tool_calls) <= exp.max_tool_calls
        results.append(CheckResult(
            name=f"max_tool_calls<={exp.max_tool_calls}", passed=ok,
            detail=f"made {len(response.tool_calls)} call(s)",
        ))

    # --- Behavior flags -----------------------------------------------------
    if exp.expect_refusal:
        refused = bool(response.metadata.get("refused")) or any(
            re.search(p, text_lower) for p in REFUSAL_PATTERNS
        )
        results.append(CheckResult(
            name="expect_refusal", passed=refused,
            detail="" if refused else "response does not look like a refusal",
        ))

    if exp.expect_escalation:
        ok = bool(response.metadata.get("escalated"))
        results.append(CheckResult(
            name="expect_escalation", passed=ok,
            detail="" if ok else "metadata['escalated'] is not true",
        ))

    for key, want in exp.metadata_equals.items():
        got = response.metadata.get(key)
        ok = got == want
        results.append(CheckResult(
            name=f"metadata[{key!r}]=={want!r}", passed=ok,
            detail="" if ok else f"got {got!r}",
        ))

    # --- Output structure ---------------------------------------------------
    parsed_json: Any = None
    if exp.expect_valid_json or exp.json_schema_required_keys:
        try:
            parsed_json = json.loads(text)
            json_ok = True
        except (json.JSONDecodeError, TypeError):
            json_ok = False
        if exp.expect_valid_json:
            results.append(CheckResult(
                name="expect_valid_json", passed=json_ok,
                detail="" if json_ok else "response text is not valid JSON",
            ))
        if exp.json_schema_required_keys:
            if not json_ok or not isinstance(parsed_json, dict):
                ok = False
                detail = "response is not a JSON object"
            else:
                missing = [k for k in exp.json_schema_required_keys if k not in parsed_json]
                ok = not missing
                detail = "" if ok else f"missing keys: {missing}"
            results.append(CheckResult(
                name=f"json_required_keys:{exp.json_schema_required_keys}",
                passed=ok, detail=detail,
            ))

    # --- Retrieval quality (RAG) -------------------------------------------
    if exp.expected_retrieved_docs:
        retrieved = set(response.metadata.get("retrieved_doc_ids", []))
        missing = [d for d in exp.expected_retrieved_docs if d not in retrieved]
        ok = not missing
        results.append(CheckResult(
            name=f"retrieved_docs:{exp.expected_retrieved_docs}",
            passed=ok,
            detail="" if ok else f"missing docs: {missing} (retrieved: {sorted(retrieved)})",
        ))

    return results
