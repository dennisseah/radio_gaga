from typing import Any

import pytest
from agent_framework import AgentResponse, Content, Message

from radio_gaga.commons.execution_plan import get_execution_plan


@pytest.mark.parametrize(
    "result",
    [
        None,
        "Result without JSON",
        "{invalid JSON",
        '{"goal": 42, "steps": []}',
        '{"goal": "Valid goal"}',
        '{"goal": "Valid goal", "steps": [42]}',
    ],
)
def test_get_execution_plan_rejects_invalid_plan_results(result: Any) -> None:
    response = AgentResponse(
        messages=[
            Message(
                "tool",
                [Content("function_result", call_id="call", result=result)],
            )
        ]
    )

    assert get_execution_plan(response) is None
