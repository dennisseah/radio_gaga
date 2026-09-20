import json
from typing import Any, NotRequired, TypedDict, cast

from agent_framework import AgentResponse, Content


class ExecutionPlan(TypedDict):
    goal: str
    steps: list[str]
    professional_follow_up: NotRequired[str | None]


def _parse_plan(result: Any) -> ExecutionPlan | None:
    if not isinstance(result, str):
        return None

    json_start = result.find("{")
    if json_start == -1:
        return None
    try:
        plan, _ = json.JSONDecoder().raw_decode(result[json_start:])
    except json.JSONDecodeError:
        return None
    if isinstance(plan, dict) and isinstance(plan.get("goal"), str):
        steps = plan.get("steps")
        if isinstance(steps, list) and all(isinstance(step, str) for step in steps):
            return cast(ExecutionPlan, plan)
    return None


def _format_call_step(content: Content) -> str:
    step = f"Call {content.name or 'function'}"
    if content.arguments:
        arguments = content.arguments
        if not isinstance(arguments, str):
            arguments = json.dumps(arguments, default=str, sort_keys=True)
        step = f"{step} with {arguments}"
    return step


def get_execution_plan(response: AgentResponse) -> ExecutionPlan | None:
    calls = {
        content.call_id: content
        for message in response.messages
        for content in message.contents
        if content.type == "function_call" and content.call_id is not None
    }
    completed_call_ids: list[str] = []
    plan_call_id: str | None = None
    plan: ExecutionPlan | None = None

    for message in response.messages:
        for content in message.contents:
            if content.type != "function_result" or content.call_id is None:
                continue
            completed_call_ids.append(content.call_id)
            if plan is None and (candidate := _parse_plan(content.result)) is not None:
                plan = candidate
                plan_call_id = content.call_id

    if plan is None:
        return None

    call_steps = [
        _format_call_step(calls[call_id])
        for call_id in completed_call_ids
        if call_id != plan_call_id and call_id in calls
    ]
    plan["steps"] = [*plan["steps"], *call_steps]
    return plan
