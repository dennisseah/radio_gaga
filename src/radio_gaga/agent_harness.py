import asyncio
import json
import logging
from dataclasses import dataclass

from agent_framework import (
    FunctionTool,
    InMemoryHistoryProvider,
    create_harness_agent,
)

from radio_gaga.agents.health_advisor import SubAgent
from radio_gaga.commons.execution_plan import get_execution_plan
from radio_gaga.commons.prompts import get_system_prompt
from radio_gaga.commons.statistics import (
    finish_and_log_turn_statistics,
    log_response_statistics,
)
from radio_gaga.hosting import container
from radio_gaga.protocols.i_chat_client import IChatClient
from radio_gaga.protocols.i_session_store import ISessionStore
from radio_gaga.services.tool_timing_middleware import ToolTimingMiddleware
from radio_gaga.services.turn_statistics import TurnStatistics
from radio_gaga.tools.medical_centers import Tool


@dataclass
class MyAgent:
    _logger: logging.Logger
    _client: IChatClient
    _session_store: ISessionStore

    async def run(self) -> None:
        medical_centers = container[Tool]
        health_advisor = container[SubAgent]
        statistics = TurnStatistics()

        agent = create_harness_agent(
            client=self._client.get_client(),
            agent_instructions=get_system_prompt(),
            history_provider=InMemoryHistoryProvider(load_messages=False),
            max_context_window_tokens=128_000,
            max_output_tokens=8_000,
            middleware=[
                ToolTimingMiddleware(
                    statistics,
                    agent_tool_names={"health_advisor"},
                )
            ],
            tools=[
                health_advisor.create_agent(statistics).as_tool(
                    name="health_advisor",
                    description="Answer a medical or health question.",
                ),
                FunctionTool(
                    name="medical_centers",
                    description="Find medical center where procedure can be performed.",
                    func=medical_centers.run,
                ),
            ],
        )
        session = self._session_store.load_session(agent)
        try:
            while True:
                question = await asyncio.to_thread(input, "Question: ")
                if question.strip().lower() in {"exit", "quit"}:
                    break

                if question.strip():
                    statistics.start_turn()
                    try:
                        response = await agent.run(question, session=session)
                    finally:
                        finish_and_log_turn_statistics(self._logger, statistics)
                    log_response_statistics(self._logger, statistics, response)
                    execution_plan = get_execution_plan(response)
                    if execution_plan is not None:
                        print(
                            "\nExecution plan:\n"
                            f"{json.dumps(execution_plan, indent=2)}\n"
                        )
                    print(f"\nAnswer: {response.text}\n")
        finally:
            self._session_store.persist_session(session)


if __name__ == "__main__":
    main_class = container[MyAgent]
    asyncio.run(main_class.run())
