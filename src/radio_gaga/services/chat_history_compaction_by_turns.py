import logging
from dataclasses import dataclass

from agent_framework import AgentSession, Message, SummarizationStrategy
from agent_framework.foundry import FoundryChatClient

from radio_gaga.protocols.i_chat_history_compaction import IChatHistoryCompaction
from radio_gaga.services.chat_history_compaction_base import ChatHistoryCompactionBase


@dataclass
class ChatHistoryCompactionByTurns(ChatHistoryCompactionBase, IChatHistoryCompaction):
    _logger: logging.Logger
    _turns_before_compaction: int = 5
    _last_compaction_turn_count: int = 0

    def set_summarization_strategy(self, chat_client: FoundryChatClient) -> None:
        self._summarization_strategy = SummarizationStrategy(
            client=chat_client,
            target_count=self._turns_before_compaction,
            threshold=0,
        )

    def _get_turn_count(self, messages: list[Message]) -> int:
        return sum(
            message.role == "user" and not self._is_excluded(message)
            for message in messages
        )

    def initialize_session(self, session: AgentSession) -> None:
        super().initialize_session(session)
        messages = self._get_session_messages(session)
        # Continue counting from persisted history after an application restart.
        self._last_compaction_turn_count = self._get_turn_count(messages)

    async def compact_history(self, messages: list[Message]) -> bool:
        turn_count = self._get_turn_count(messages)
        turns_since_compaction = turn_count - self._last_compaction_turn_count
        # Turn compaction is gated before invoking the model-backed strategy.
        if turns_since_compaction < self._turns_before_compaction:
            return False

        compacted = await self._compact_history(messages)
        if compacted:
            self._last_compaction_turn_count = turn_count
        return compacted
