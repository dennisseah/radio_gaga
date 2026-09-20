from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import AgentResponse, ResponseStream, UsageDetails

from radio_gaga.commons.agent_usage_middleware import AgentUsageMiddleware
from radio_gaga.commons.tool_timing_middleware import ToolTimingMiddleware
from radio_gaga.commons.turn_statistics import TurnStatistics


def test_turn_statistics_records_total_and_resets_calls() -> None:
    clock = Mock(side_effect=[10.0, 11.5, 20.0, 22.0])
    statistics = TurnStatistics(clock)

    statistics.start_turn()
    statistics.tool_calls.append(Mock())
    assert statistics.finish_turn() == 1.5

    statistics.start_turn()
    assert statistics.tool_calls == []
    assert statistics.agent_usages == []
    assert statistics.finish_turn() == 2.0


def test_finish_turn_raises_when_turn_was_not_started() -> None:
    with pytest.raises(RuntimeError, match="Turn timing has not been started"):
        TurnStatistics().finish_turn()


def test_turn_statistics_combines_parent_and_delegated_usage() -> None:
    statistics = TurnStatistics()
    statistics.record_agent_usage(
        "health_advisor",
        UsageDetails(input_token_count=100, output_token_count=20),
    )

    total = statistics.total_usage(
        UsageDetails(input_token_count=50, output_token_count=10)
    )

    assert total.get("input_token_count") == 150
    assert total.get("output_token_count") == 30


@pytest.mark.asyncio
async def test_agent_usage_middleware_records_streamed_response_usage() -> None:
    async def empty_stream():
        if False:
            yield None

    statistics = TurnStatistics()
    middleware = AgentUsageMiddleware(statistics)
    response = AgentResponse(
        usage_details=UsageDetails(
            input_token_count=100,
            output_token_count=20,
            total_token_count=120,
        )
    )
    context = Mock()
    context.agent.name = "health_advisor"
    context.result = ResponseStream(
        empty_stream(),
        finalizer=lambda _: response,
    )
    context.stream_result_hooks = []

    await middleware.process(context, AsyncMock())
    recorded_response = context.stream_result_hooks[0](response)

    assert recorded_response is response
    assert statistics.agent_usages[0].name == "health_advisor"
    assert statistics.agent_usages[0].usage_details == response.usage_details


@pytest.mark.asyncio
async def test_agent_usage_middleware_records_direct_response_usage() -> None:
    statistics = TurnStatistics()
    middleware = AgentUsageMiddleware(statistics)
    response = AgentResponse(
        usage_details=UsageDetails(total_token_count=120),
    )
    context = Mock()
    context.agent.name = None
    context.agent.id = "health-advisor-id"
    context.result = response

    await middleware.process(context, AsyncMock())

    assert statistics.agent_usages[0].name == "health-advisor-id"
    assert statistics.agent_usages[0].usage_details == response.usage_details


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "expected_kind"),
    [("health_advisor", "agent"), ("parking_lot", "function")],
)
async def test_tool_timing_middleware_classifies_calls(
    tool_name: str, expected_kind: str
) -> None:
    clock = Mock(side_effect=[3.0, 3.25])
    statistics = TurnStatistics(clock)
    middleware = ToolTimingMiddleware(
        statistics,
        agent_tool_names={"health_advisor"},
    )
    context = Mock()
    context.function.name = tool_name
    call_next = AsyncMock()

    await middleware.process(context, call_next)

    call_next.assert_awaited_once_with()
    [timing] = statistics.tool_calls
    assert timing.sequence == 1
    assert timing.kind == expected_kind
    assert timing.name == tool_name
    assert timing.duration_seconds == 0.25


@pytest.mark.asyncio
async def test_tool_timing_middleware_records_failed_calls() -> None:
    clock = Mock(side_effect=[5.0, 5.5])
    statistics = TurnStatistics(clock)
    middleware = ToolTimingMiddleware(statistics, agent_tool_names=set())
    context = Mock()
    context.function.name = "parking_lot"
    call_next = AsyncMock(side_effect=RuntimeError("tool failed"))

    with pytest.raises(RuntimeError, match="tool failed"):
        await middleware.process(context, call_next)

    assert statistics.tool_calls[0].duration_seconds == 0.5
