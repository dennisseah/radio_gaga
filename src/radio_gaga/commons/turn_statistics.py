from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

from agent_framework import (
    UsageDetails,
    add_usage_details,
)


@dataclass(frozen=True)
class ToolCallTiming:
    sequence: int
    kind: str
    name: str
    duration_seconds: float


@dataclass(frozen=True)
class AgentCallUsage:
    name: str
    usage_details: UsageDetails


class TurnStatistics:
    def __init__(self, clock: Callable[[], float] = perf_counter) -> None:
        self._clock = clock
        self._turn_started_at: float | None = None
        self._next_sequence = 1
        self.tool_calls: list[ToolCallTiming] = []
        self.agent_usages: list[AgentCallUsage] = []

    def start_turn(self) -> None:
        self._turn_started_at = self._clock()
        self._next_sequence = 1
        self.tool_calls.clear()
        self.agent_usages.clear()

    def record_agent_usage(self, name: str, usage_details: UsageDetails | None) -> None:
        if usage_details:
            self.agent_usages.append(
                AgentCallUsage(name=name, usage_details=UsageDetails(usage_details))
            )

    def total_usage(self, parent_usage: UsageDetails | None = None) -> UsageDetails:
        total = parent_usage
        for agent_usage in self.agent_usages:
            total = add_usage_details(total, agent_usage.usage_details)
        return total or UsageDetails()

    def start_tool_call(self) -> tuple[int, float]:
        sequence = self._next_sequence
        self._next_sequence += 1
        return sequence, self._clock()

    def finish_tool_call(
        self, sequence: int, started_at: float, kind: str, name: str
    ) -> None:
        self.tool_calls.append(
            ToolCallTiming(
                sequence=sequence,
                kind=kind,
                name=name,
                duration_seconds=self._clock() - started_at,
            )
        )

    def finish_turn(self) -> float:
        if self._turn_started_at is None:
            raise RuntimeError("Turn timing has not been started")

        duration_seconds = self._clock() - self._turn_started_at
        self._turn_started_at = None
        return duration_seconds
