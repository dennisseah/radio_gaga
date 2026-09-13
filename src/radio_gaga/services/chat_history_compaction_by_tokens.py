import json
import logging
from dataclasses import dataclass, field

from agent_framework import AgentSession, Message, SummarizationStrategy
from agent_framework._compaction import CharacterEstimatorTokenizer
from agent_framework.foundry import FoundryChatClient

from radio_gaga.protocols.i_chat_history_compaction import IChatHistoryCompaction
from radio_gaga.services.chat_history_compaction_base import ChatHistoryCompactionBase


@dataclass
class ChatHistoryCompactionByTokens(ChatHistoryCompactionBase, IChatHistoryCompaction):
    _logger: logging.Logger
    _max_summary_input_tokens: int = 160_000
    _tokenizer: CharacterEstimatorTokenizer = field(
        default_factory=CharacterEstimatorTokenizer,
        init=False,
        repr=False,
    )

    def initialize_session(self, session: AgentSession) -> None:
        super().initialize_session(session)

    def set_summarization_strategy(self, chat_client: FoundryChatClient) -> None:
        # The local token gate controls when compaction starts; this strategy
        # controls how the selected history is summarized and retained.
        self._summarization_strategy = SummarizationStrategy(
            client=chat_client,
            target_count=1,
            threshold=0,
            max_summary_input_tokens=self._max_summary_input_tokens,
            tokenizer=self._tokenizer,
        )

    def _get_token_count(self, messages: list[Message]) -> int:
        # Use the same lightweight estimator supplied to the summarizer.
        return sum(
            self._tokenizer.count_tokens(json.dumps(message.to_dict(), sort_keys=True))
            for message in messages
            if message.role != "system" and not self._is_excluded(message)
        )

    async def compact_history(self, messages: list[Message]) -> bool:
        # Gate on estimated tokens so framework message-count defaults do not
        # trigger compaction early.
        if self._get_token_count(messages) < self._max_summary_input_tokens:
            return False
        return await self._compact_history(messages)
