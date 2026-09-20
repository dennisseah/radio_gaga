from collections.abc import Awaitable, Callable

from agent_framework import (
    AgentContext,
    AgentMiddleware,
    AgentResponse,
    ResponseStream,
)

from radio_gaga.commons.turn_statistics import TurnStatistics


class AgentUsageMiddleware(AgentMiddleware):
    def __init__(self, statistics: TurnStatistics) -> None:
        self._statistics = statistics

    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        await call_next()

        def record_usage(response: AgentResponse) -> AgentResponse:
            name = context.agent.name or context.agent.id
            self._statistics.record_agent_usage(name, response.usage_details)
            return response

        if isinstance(context.result, ResponseStream):
            context.stream_result_hooks.append(record_usage)
        elif isinstance(context.result, AgentResponse):
            record_usage(context.result)
