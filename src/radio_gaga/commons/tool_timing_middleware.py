from collections.abc import Awaitable, Callable

from agent_framework import FunctionInvocationContext, FunctionMiddleware

from radio_gaga.commons.turn_statistics import TurnStatistics


class ToolTimingMiddleware(FunctionMiddleware):
    def __init__(
        self, statistics: TurnStatistics, *, agent_tool_names: set[str]
    ) -> None:
        self._statistics = statistics
        self._agent_tool_names = agent_tool_names

    async def process(
        self,
        context: FunctionInvocationContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        sequence, started_at = self._statistics.start_tool_call()
        try:
            await call_next()
        finally:
            name = context.function.name
            kind = "agent" if name in self._agent_tool_names else "function"
            self._statistics.finish_tool_call(sequence, started_at, kind, name)
