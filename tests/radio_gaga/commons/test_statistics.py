from unittest.mock import Mock, call

from agent_framework import UsageDetails

from radio_gaga.commons.statistics import (
    finish_and_log_turn_statistics,
    log_response_statistics,
)
from radio_gaga.commons.turn_statistics import (
    AgentCallUsage,
    ToolCallTiming,
    TurnStatistics,
)


def test_finish_and_log_turn_statistics_logs_summary_and_calls_in_sequence() -> None:
    logger = Mock()
    statistics = Mock(spec=TurnStatistics)
    statistics.finish_turn.return_value = 0.5
    statistics.tool_calls = [
        ToolCallTiming(2, "function", "medical_centers", 0.2),
        ToolCallTiming(1, "agent", "health_advisor", 0.1),
    ]

    finish_and_log_turn_statistics(logger, statistics)

    assert logger.info.call_args_list == [
        call(
            "Turn statistics: duration=%.3fs tool_calls=%d "
            "agent_calls=%d function_calls=%d",
            0.5,
            2,
            1,
            1,
        ),
        call(
            "Tool call statistics: sequence=%d type=%s name=%s duration=%.3fs",
            1,
            "agent",
            "health_advisor",
            0.1,
        ),
        call(
            "Tool call statistics: sequence=%d type=%s name=%s duration=%.3fs",
            2,
            "function",
            "medical_centers",
            0.2,
        ),
    ]


def test_log_response_statistics_logs_metadata_and_usage() -> None:
    logger = Mock()
    statistics = Mock(spec=TurnStatistics)
    usage = UsageDetails(total_token_count=10)
    total_usage = UsageDetails(total_token_count=15)
    statistics.agent_usages = [AgentCallUsage("health_advisor", usage)]
    statistics.total_usage.return_value = total_usage
    response = Mock(
        response_id="response-1",
        finish_reason="stop",
        usage_details=usage,
    )

    log_response_statistics(logger, statistics, response)

    assert logger.info.call_args_list == [
        call(
            "Response metadata: response_id=%s finish_reason=%s usage=%s",
            "response-1",
            "stop",
            usage,
        ),
        call("Delegated agent usage: name=%s usage=%s", "health_advisor", usage),
        call("Total turn token usage: usage=%s", total_usage),
    ]
