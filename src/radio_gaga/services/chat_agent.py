import logging
from dataclasses import dataclass

from agent_framework import Agent

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

        self.agent = Agent(
            client=client,
            name="MyAgent",
            instructions=get_system_prompt(),
            compaction_strategy=self._compaction_service.compact_history,
            default_options={"store": False},
        )

    def get_agent(self) -> Agent:
        return self.agent
