from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import Message

from radio_gaga.services.chat_history_compaction import ChatHistoryCompaction


def test_set_summarization_strategy_configures_client() -> None:
    service = ChatHistoryCompaction(Mock())
    client = Mock()

    service.set_summarization_strategy(client)

    assert service._summarization_strategy.client is client
    assert service._summarization_strategy.max_summary_input_tokens == 8_000


@pytest.mark.asyncio
async def test_compact_history_tracks_success_and_summary() -> None:
    logger = Mock()
    service = ChatHistoryCompaction(logger)
    summary = Message("assistant", "summary")
    messages = [Message("system", "system"), Message("user", "question")]
    service._summarization_strategy = AsyncMock(return_value=True)

    async def add_summary(current_messages: list[Message]) -> bool:
        current_messages.append(summary)
        return True

    service._summarization_strategy.side_effect = add_summary

    assert await service.compact_history(messages) is True
    assert service._compaction_attempt_count == 1
    assert service._compaction_count == 1
    assert service._last_compaction_message_count == 1
    assert any(
        call.args[0].startswith("Summary message:")
        for call in logger.info.call_args_list
    )


@pytest.mark.asyncio
async def test_compact_history_tracks_unsuccessful_attempt() -> None:
    service = ChatHistoryCompaction(Mock())
    service._summarization_strategy = AsyncMock(return_value=False)

    assert await service.compact_history([Message("user", "question")]) is False
    assert service._compaction_attempt_count == 1
    assert service._compaction_count == 0
