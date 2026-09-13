import logging
import time
from dataclasses import dataclass

from agent_framework import Agent, AgentSession

from radio_gaga.commons.prompts import get_system_prompt
from radio_gaga.protocols.i_chat_agent import IChatAgent
from radio_gaga.protocols.i_chat_client import IChatClient
from radio_gaga.protocols.i_chat_history_compaction import IChatHistoryCompaction


@dataclass
class ChatAgent(IChatAgent):
    _compaction_service: IChatHistoryCompaction
    _chat_client: IChatClient
    _logger: logging.Logger

    def __post_init__(self) -> None:
        self._logger.info("Initializing ChatAgent")

        client = self._chat_client.get_client()
        self._compaction_service.set_summarization_strategy(client)

        self._agent = Agent(
            client=client,
            name="MyAgent",
            instructions=get_system_prompt(),
            compaction_strategy=self._compaction_service.compact_history,
            default_options={"store": False},
        )

    async def stream(self, user_message: str, session: AgentSession) -> str:
        time_start = time.perf_counter()

        async_stream = self._agent.run(user_message, session=session, stream=True)
        response_started = False

        response: list[str] = []
        async for chunk in async_stream:
            if chunk.text:
                if not response_started:
                    time_taken = time.perf_counter() - time_start
                    print()
                    self._logger.info(
                        f"Time taken to start agent response: {time_taken:.2f} seconds"
                    )
                    response_started = True
                response.append(chunk.text)

        return "".join(response)

    def get_agent(self) -> Agent:
        return self._agent
