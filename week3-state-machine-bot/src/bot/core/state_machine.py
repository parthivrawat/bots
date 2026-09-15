"""State machine engine for multi-step conversation workflows.

A workflow is a map of state names to async handlers. Each handler receives the
user's raw input, the accumulated data, and the calling context, and returns the
next state name, updated data, and the bot's reply text. A terminal state named
'__done__' ends the workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    from .contracts import HandlerContext


@dataclass
class Transition:
    next_state: str
    data: dict[str, Any]
    reply: str


StateHandler = Callable[[str, dict[str, Any], "HandlerContext"], Awaitable[Transition]]


class Workflow:
    def __init__(self, name: str, start_state: str, states: dict[str, StateHandler]):
        self.name = name
        self.start_state = start_state
        self.states = states

    async def step(self, current_state: str, text: str, data: dict[str, Any],
                   ctx: "HandlerContext") -> Transition:
        if current_state == "__done__":
            return Transition(next_state="__done__", data=data, reply="")
        handler = self.states.get(current_state)
        if handler is None:
            return Transition(next_state="__done__", data=data, reply="Unknown state. Cancelling.")
        return await handler(text, data, ctx)


class StateMachine:
    def __init__(self):
        self.workflows: dict[str, Workflow] = {}

    def register(self, workflow: Workflow) -> None:
        self.workflows[workflow.name] = workflow

    async def start(self, workflow_name: str, ctx: "HandlerContext") -> tuple[str, dict, str]:
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return ("__done__", {}, "Unknown workflow.")
        result = await workflow.step(workflow.start_state, "", {}, ctx)
        return (result.next_state, result.data, result.reply)

    async def advance(self, workflow_name: str, current_state: str, text: str,
                      data: dict, ctx: "HandlerContext") -> Transition:
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return Transition(next_state="__done__", data=data, reply="Unknown workflow. Cancelling.")
        return await workflow.step(current_state, text, data, ctx)
