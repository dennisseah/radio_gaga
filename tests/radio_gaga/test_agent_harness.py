import runpy
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest
from agent_framework import AgentResponse, Content, FunctionTool, Message

from radio_gaga.agent_harness import MyAgent
from radio_gaga.agents.health_advisor import SubAgent
from radio_gaga.commons.execution_plan import get_execution_plan
from radio_gaga.tools.medical_centers import Tool


def test_get_execution_plan_includes_all_completed_function_calls() -> None:
    response = AgentResponse(
        messages=[
            Message(
                "assistant",
                [
                    Content.from_function_call(
                        call_id="health-call",
                        name="specialist_agent",
                    ),
                    Content.from_function_call(
                        call_id="center-call",
                        name="facility_lookup",
                        arguments={"procedure": "liver transplant"},
                    ),
                    Content.from_function_call(
                        call_id="incomplete-call",
                        name="unfinished_tool",
                    ),
                ],
            ),
            Message(
                "tool",
                [
                    Content.from_function_result(
                        "health-call",
                        result=(
                            "```json\n"
                            '{"goal":"Explain liver transplant",'
                            '"steps":["Explain procedure","Discuss risks"]}\n'
                            "```\n\n**Execution**\nDetails"
                        ),
                    ),
                    Content.from_function_result(
                        "center-call",
                        result="Arizona Medical Center",
                    ),
                ],
            ),
        ]
    )

    assert get_execution_plan(response) == {
        "goal": "Explain liver transplant",
        "steps": [
            "Explain procedure",
            "Discuss risks",
            'Call facility_lookup with {"procedure": "liver transplant"}',
        ],
    }


@pytest.mark.asyncio
async def test_run_restores_and_persists_agent_session() -> None:
    client = Mock()
    model_client = Mock()
    client.get_client.return_value = model_client
    response_one = Mock(
        text="first answer",
        messages=[
            Message(
                "assistant",
                [
                    Content.from_function_call(
                        call_id="health-call",
                        name="health_advisor",
                    )
                ],
            ),
            Message(
                "tool",
                [
                    Content.from_function_result(
                        "health-call",
                        result=(
                            '{"goal":"Answer the health question",'
                            '"steps":["Provide general health information"]}'
                        ),
                    )
                ],
            ),
        ],
        response_id="response-1",
        finish_reason="stop",
        usage_details={"total_token_count": 10},
    )
    response_two = Mock(
        text="second answer",
        messages=[],
        response_id="response-2",
        finish_reason="stop",
        usage_details={"total_token_count": 20},
    )
    health_tool = FunctionTool(
        name="health_advisor",
        description="Answer a medical or health question.",
        func=Mock(),
    )
    health_agent = Mock()
    health_agent.as_tool.return_value = health_tool
    health_advisor = Mock()
    health_advisor.create_agent.return_value = health_agent
    parking_lot = Tool(Mock())
    fake_container = MagicMock()
    fake_container.__getitem__.side_effect = {
        SubAgent: health_advisor,
        Tool: parking_lot,
    }.__getitem__
    agent = Mock()
    agent.run = AsyncMock(side_effect=[response_one, response_two])
    session = Mock()
    session_store = Mock()
    session_store.load_session.return_value = session
    logger = Mock()
    statistics = Mock()
    statistics.tool_calls = []
    statistics.agent_usages = []
    statistics.finish_turn.side_effect = [0.5, 0.75]
    statistics.total_usage.side_effect = [
        {"total_token_count": 10},
        {"total_token_count": 20},
    ]

    with (
        patch("radio_gaga.agent_harness.container", fake_container),
        patch(
            "radio_gaga.agent_harness.create_harness_agent", return_value=agent
        ) as create_agent,
        patch(
            "radio_gaga.agent_harness.get_system_prompt", return_value="instructions"
        ),
        patch("radio_gaga.agent_harness.TurnStatistics", return_value=statistics),
        patch(
            "radio_gaga.agent_harness.asyncio.to_thread",
            AsyncMock(side_effect=["first question", "", "second question", "exit"]),
        ),
        patch("builtins.print") as print_output,
    ):
        await MyAgent(logger, client, session_store).run()

    create_agent.assert_called_once()
    health_advisor.create_agent.assert_called_once_with(statistics)
    health_agent.as_tool.assert_called_once_with(
        name="health_advisor",
        description="Answer a medical or health question.",
    )
    coordinator_args = create_agent.call_args.kwargs
    assert coordinator_args["client"] is model_client
    assert coordinator_args["agent_instructions"] == "instructions"
    history_provider = coordinator_args["history_provider"]
    assert not history_provider.load_messages
    delegated_health_tool, parking_tool = coordinator_args["tools"]
    assert delegated_health_tool is health_tool
    assert isinstance(parking_tool, FunctionTool)
    assert parking_tool.name == "medical_centers"
    assert isinstance(getattr(parking_tool.func, "__self__", None), Tool)
    assert getattr(parking_tool.func, "__func__", None) is Tool.run
    session_store.load_session.assert_called_once_with(agent)
    assert agent.run.await_args_list == [
        call("first question", session=session),
        call("second question", session=session),
    ]
    assert print_output.call_args_list == [
        call(
            "\nExecution plan:\n"
            "{\n"
            '  "goal": "Answer the health question",\n'
            '  "steps": [\n'
            '    "Provide general health information"\n'
            "  ]\n"
            "}\n"
        ),
        call("\nAnswer: first answer\n"),
        call("\nAnswer: second answer\n"),
    ]
    assert statistics.start_turn.call_count == 2
    assert statistics.finish_turn.call_count == 2
    session_store.persist_session.assert_called_once_with(session)


@pytest.mark.asyncio
async def test_run_persists_session_when_agent_fails() -> None:
    client = Mock()
    agent = Mock()
    agent.run = AsyncMock(side_effect=RuntimeError("agent failed"))
    session = Mock()
    session_store = Mock()
    session_store.load_session.return_value = session
    health_advisor = Mock()
    health_agent = Mock()
    health_agent.middleware = []
    health_advisor.create_agent.return_value = health_agent
    fake_container = MagicMock()
    fake_container.__getitem__.side_effect = {
        SubAgent: health_advisor,
        Tool: Tool(Mock()),
    }.__getitem__
    statistics = Mock()
    statistics.tool_calls = []
    statistics.finish_turn.return_value = 0.25

    with (
        patch("radio_gaga.agent_harness.container", fake_container),
        patch("radio_gaga.agent_harness.create_harness_agent", return_value=agent),
        patch("radio_gaga.agent_harness.TurnStatistics", return_value=statistics),
        patch(
            "radio_gaga.agent_harness.asyncio.to_thread",
            AsyncMock(return_value="question"),
        ),
        pytest.raises(RuntimeError, match="agent failed"),
    ):
        await MyAgent(Mock(), client, session_store).run()

    session_store.persist_session.assert_called_once_with(session)
    statistics.finish_turn.assert_called_once_with()


def test_module_entrypoint_runs_main_agent() -> None:
    main_agent = Mock()
    run_argument = object()
    main_agent.run.return_value = run_argument
    fake_container = MagicMock()
    fake_container.__getitem__.return_value = main_agent

    with (
        patch("radio_gaga.hosting.container", fake_container),
        patch("radio_gaga.agent_harness.asyncio.run") as run,
    ):
        runpy.run_module("radio_gaga.agent_harness", run_name="__main__")

    fake_container.__getitem__.assert_called_once()
    run.assert_called_once_with(run_argument)
