import logging
from dataclasses import dataclass

from agent_framework import Message, SummarizationStrategy
from agent_framework.foundry import FoundryChatClient

from radio_gaga.protocols.i_chat_history_compaction import IChatHistoryCompaction


@dataclass
class ChatHistoryCompaction(IChatHistoryCompaction):
    _logger: logging.Logger
    _compaction_attempt_count: int = 0
    _compaction_count: int = 0
    _last_compaction_message_count: int = 0

    def set_summarization_strategy(self, chat_client: FoundryChatClient):
        self._summarization_strategy = SummarizationStrategy(
            client=chat_client,
            max_summary_input_tokens=8_000,
        )

    async def compact_history(self, messages: list[Message]) -> bool:
        self._logger.info(f"Compaction attempt #{self._compaction_attempt_count + 1}")

        self._compaction_attempt_count += 1
        self._last_compaction_message_count = sum(
            not message.additional_properties.get("excluded", False)
            for message in messages
            if message.role != "system"
        )
        existing_messages = {id(message) for message in messages}
        compacted = await self._summarization_strategy(messages)

        self._logger.info(f"Existing messages count: {len(existing_messages)}")
        self._logger.info(f"Compacted: {compacted}")

        if compacted:
            self._compaction_count += 1
            summary_message = next(
                (
                    message
                    for message in messages
                    if id(message) not in existing_messages
                ),
                None,
            )
            self._logger.info(
                f"Summary message: {summary_message.text if summary_message else None}"
            )

        self._logger.info(
            f"[Compaction status: attempts={self._compaction_attempt_count}, "
            f"messages={self._last_compaction_message_count}, "
            f"successful={self._compaction_count}]"
        )
        return compacted
