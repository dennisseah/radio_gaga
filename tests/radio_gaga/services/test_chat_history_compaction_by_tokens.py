from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import AgentSession, Message

from radio_gaga.services.chat_history_compaction_by_tokens import (
    ChatHistoryCompactionByTokens,
)


def test_set_summarization_strategy_configures_token_limit() -> None:
    service = ChatHistoryCompactionByTokens(Mock())
    client = Mock()

    service.set_summarization_strategy(client)

    assert service._summarization_strategy.client is client
    assert service._summarization_strategy.target_count == 1
    assert service._summarization_strategy.threshold == 0
    assert service._summarization_strategy.max_summary_input_tokens == 160_000


def test_initialize_session_resets_pending_compaction() -> None:
    service = ChatHistoryCompactionByTokens(Mock())
    session = AgentSession()
    session.state = {
        "in_memory": {
            "messages": [
                Message("user", "old question"),
                Message("assistant", "old answer"),
                Message(
                    "user",
                    "summarized question",
                    additional_properties={"_excluded": True},
                ),
            ]
        }
    }

    service.initialize_session(session)

    assert service._compacted_messages is None
    assert service._compaction_source_message_ids is None


@pytest.mark.asyncio
async def test_compact_history_tracks_success() -> None:
    logger = Mock()
    service = ChatHistoryCompactionByTokens(logger, _max_summary_input_tokens=1)
    summary = Message("assistant", "summary")
    messages = [Message("user", "question")]

    async def summarize(current_messages: list[Message]) -> bool:
        current_messages.append(summary)
        return True

    service._summarization_strategy = AsyncMock(side_effect=summarize)

    assert await service.compact_history(messages) is True
    assert service._compaction_attempt_count == 1
    assert service._compaction_count == 1


@pytest.mark.asyncio
async def test_compact_history_tracks_failure() -> None:
    service = ChatHistoryCompactionByTokens(Mock(), _max_summary_input_tokens=1)
    service._summarization_strategy = AsyncMock(return_value=False)

    assert await service.compact_history([Message("user", "question")]) is False
    assert service._compaction_attempt_count == 1
    assert service._compaction_count == 0


@pytest.mark.asyncio
async def test_compact_history_waits_for_token_threshold() -> None:
    service = ChatHistoryCompactionByTokens(Mock(), _max_summary_input_tokens=1_000)
    service._summarization_strategy = AsyncMock(return_value=False)

    assert await service.compact_history([Message("user", "short")]) is False
    service._summarization_strategy.assert_not_awaited()

    long_message = Message("user", "x" * 5_000)
    assert await service.compact_history([long_message]) is False
    service._summarization_strategy.assert_awaited_once()


@pytest.mark.asyncio
async def test_compact_history_ignores_persisted_excluded_messages() -> None:
    service = ChatHistoryCompactionByTokens(Mock(), _max_summary_input_tokens=1)
    service._summarization_strategy = AsyncMock(return_value=False)
    messages = [
        Message(
            "user",
            "summarized question",
            additional_properties={"_excluded": True},
        ),
        Message("user", "current question"),
    ]

    assert await service.compact_history(messages) is False


def test_sync_session_replaces_in_memory_history_after_compaction() -> None:
    service = ChatHistoryCompactionByTokens(Mock())
    compacted_messages = [Message("assistant", "summary")]
    old_message = Message("user", "old", message_id="old")
    response_message = Message("assistant", "current response", message_id="response")
    service._compacted_messages = compacted_messages
    service._compaction_source_message_ids = {"old"}
    session = AgentSession()
    session.state = {
        "in_memory": {"messages": [old_message, response_message]},
    }

    service.sync_session(session)

    assert session.state["in_memory"]["messages"] == [
        *compacted_messages,
        response_message,
    ]
    assert service._compacted_messages is None


def test_sync_session_writes_fallback_state_when_provider_state_is_missing() -> None:
    service = ChatHistoryCompactionByTokens(Mock())
    compacted_messages = [Message("assistant", "summary")]
    service._compacted_messages = compacted_messages
    session = AgentSession()

    service.sync_session(session)

    assert session.state["messages"] == compacted_messages
    assert service._compacted_messages is None


def test_sync_session_returns_without_pending_compaction() -> None:
    service = ChatHistoryCompactionByTokens(Mock())
    session = AgentSession()

    service.sync_session(session)

    assert session.state == {}
