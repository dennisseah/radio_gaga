import logging

from agent_framework import AgentResponse

from radio_gaga.commons.turn_statistics import TurnStatistics


def finish_and_log_turn_statistics(
    logger: logging.Logger, statistics: TurnStatistics
) -> None:
    duration_seconds = statistics.finish_turn()
    agent_calls = sum(call.kind == "agent" for call in statistics.tool_calls)
    function_calls = sum(call.kind == "function" for call in statistics.tool_calls)
    logger.info(
        "Turn statistics: duration=%.3fs tool_calls=%d "
        "agent_calls=%d function_calls=%d",
        duration_seconds,
        len(statistics.tool_calls),
        agent_calls,
        function_calls,
    )
    for call in sorted(statistics.tool_calls, key=lambda item: item.sequence):
        logger.info(
            "Tool call statistics: sequence=%d type=%s name=%s duration=%.3fs",
            call.sequence,
            call.kind,
            call.name,
            call.duration_seconds,
        )


def log_response_statistics(
    logger: logging.Logger,
    statistics: TurnStatistics,
    response: AgentResponse,
) -> None:
    logger.info(
        "Response metadata: response_id=%s finish_reason=%s usage=%s",
        response.response_id,
        response.finish_reason,
        response.usage_details,
    )
    for agent_usage in statistics.agent_usages:
        logger.info(
            "Delegated agent usage: name=%s usage=%s",
            agent_usage.name,
            agent_usage.usage_details,
        )
    logger.info(
        "Total turn token usage: usage=%s",
        statistics.total_usage(response.usage_details),
    )
