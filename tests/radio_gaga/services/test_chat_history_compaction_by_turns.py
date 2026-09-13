from collections import Counter
from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import AgentSession, Message

from radio_gaga.services.chat_history_compaction_by_turns import (
    ChatHistoryCompactionByTurns,
)


def test_set_summarization_strategy_configures_client() -> None:
    service = ChatHistoryCompactionByTurns(Mock())
    client = Mock()

    service.set_summarization_strategy(client)

    assert service._summarization_strategy.client is client
    assert service._summarization_strategy.target_count == 5
    assert service._summarization_strategy.threshold == 0


def test_initialize_session_restores_turn_baseline() -> None:
    service = ChatHistoryCompactionByTurns(Mock())
    session = AgentSession()
    session.state = {
        "in_memory": {
            "messages": [
                Message("user", "old question"),
                Message("assistant", "old answer"),
                Message(
                    "user",
                    "excluded question",
                    additional_properties={"_excluded": True},
                ),
            ]
        }
    }

    service.initialize_session(session)

    assert service._last_compaction_turn_count == 1


@pytest.mark.asyncio
async def test_compact_history_tracks_success_and_summary() -> None:
    logger = Mock()
    service = ChatHistoryCompactionByTurns(logger)
    summary = Message("assistant", "summary")
    messages = [
        Message("system", "system"),
        *[Message("user", f"question {index}") for index in range(5)],
    ]
    service._summarization_strategy = AsyncMock(return_value=True)

    async def add_summary(current_messages: list[Message]) -> bool:
        current_messages.append(summary)
        return True

    service._summarization_strategy.side_effect = add_summary

    assert await service.compact_history(messages) is True
    assert service._compaction_attempt_count == 1
    assert service._compaction_count == 1
    assert service._last_compaction_turn_count == 5
    service._summarization_strategy.assert_awaited_once_with(messages)
    assert any(
        call.args[0].startswith("Summary message:")
        for call in logger.info.call_args_list
    )


@pytest.mark.asyncio
async def test_compact_history_tracks_unsuccessful_attempt() -> None:
    service = ChatHistoryCompactionByTurns(Mock())
    service._summarization_strategy = AsyncMock(return_value=False)

    messages = [Message("user", f"question {index}") for index in range(4)]

    assert await service.compact_history(messages) is False
    assert service._compaction_attempt_count == 0
    assert service._compaction_count == 0


@pytest.mark.asyncio
async def test_compact_history_waits_for_next_turn_threshold() -> None:
    service = ChatHistoryCompactionByTurns(Mock())
    service._summarization_strategy = AsyncMock(return_value=True)
    messages = [Message("user", f"question {index}") for index in range(5)]

    assert await service.compact_history(messages) is True
    messages.append(Message("user", "question 5"))
    assert await service.compact_history(messages) is False
    assert service._compaction_attempt_count == 1


@pytest.mark.asyncio
async def test_compact_history_does_not_count_system_or_excluded_messages() -> None:
    service = ChatHistoryCompactionByTurns(Mock())
    messages = [
        Message("system", "system"),
        *[Message("user", f"question {index}") for index in range(4)],
        Mock(role="user", additional_properties={"excluded": True}),
    ]

    assert await service.compact_history(messages) is False
    assert service._compaction_attempt_count == 0


@pytest.mark.asyncio
async def test_compact_history_tracks_unsuccessful_threshold_attempt() -> None:
    service = ChatHistoryCompactionByTurns(Mock())
    service._summarization_strategy = AsyncMock(return_value=False)
    messages = [Message("user", f"question {index}") for index in range(5)]

    assert await service.compact_history(messages) is False
    assert service._compaction_attempt_count == 1
    assert service._compaction_count == 0


def test_sync_session_replaces_in_memory_history_after_compaction() -> None:
    service = ChatHistoryCompactionByTurns(Mock())
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


def test_sync_session_skips_excluded_messages() -> None:
    service = ChatHistoryCompactionByTurns(Mock())
    summary_message = Message("assistant", "summary")
    excluded_message = Message(
        "user",
        "old",
        message_id="old",
        additional_properties={"_excluded": True},
    )
    response_message = Message("assistant", "current response", message_id="response")
    service._compacted_messages = [summary_message]
    service._compaction_source_message_ids = {"old"}
    session = AgentSession()
    session.state = {
        "in_memory": {"messages": [excluded_message, response_message]},
    }

    service.sync_session(session)

    assert session.state["in_memory"]["messages"] == [summary_message, response_message]


def test_sync_session_does_not_duplicate_messages_without_ids() -> None:
    service = ChatHistoryCompactionByTurns(Mock())
    old_message = Message("user", "old")
    response_message = Message("assistant", "current response")
    summary_message = Message("assistant", "summary")
    service._compacted_messages = [summary_message]
    service._compaction_source_message_fingerprints = Counter(
        {service._message_fingerprint(old_message): 1}
    )
    session = AgentSession()
    session.state = {
        "in_memory": {"messages": [old_message, response_message]},
    }

    service.sync_session(session)

    assert session.state["in_memory"]["messages"] == [summary_message, response_message]
