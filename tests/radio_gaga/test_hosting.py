import importlib
import logging
from unittest.mock import Mock, patch

import radio_gaga.hosting as hosting
from radio_gaga.hosting import container
from radio_gaga.protocols.i_chat_client import IChatClient
from radio_gaga.protocols.i_chat_history_compaction import IChatHistoryCompaction
from radio_gaga.protocols.i_planner_agent import IPlannerAgent
from radio_gaga.protocols.i_session_store import ISessionStore


def test_container_resolves_logger() -> None:
    assert container[logging.Logger].name == "radio_gaga"


def test_container_resolves_chat_client() -> None:
    chat_client = Mock()
    with patch("radio_gaga.services.chat_client.ChatClient", return_value=chat_client):
        assert container[IChatClient] is chat_client


def test_container_resolves_planner_agent() -> None:
    planner_agent = Mock()
    with patch(
        "radio_gaga.services.chat_agent.PlannerAgent", return_value=planner_agent
    ):
        assert container[IPlannerAgent] is planner_agent


def test_container_resolves_compaction_service(
    monkeypatch,
) -> None:
    monkeypatch.setenv("CHAT_HISTORY_COMPACTION_STRATEGY", "by_turns")
    compaction_service = Mock()
    with patch(
        "radio_gaga.services.chat_history_compaction_by_turns.ChatHistoryCompactionByTurns",
        return_value=compaction_service,
    ):
        assert container[IChatHistoryCompaction] is compaction_service


def test_container_resolves_token_compaction_service(monkeypatch) -> None:
    monkeypatch.setenv("CHAT_HISTORY_COMPACTION_STRATEGY", "by_tokens")
    reloaded_hosting = importlib.reload(hosting)
    compaction_service = Mock()

    with patch(
        "radio_gaga.services.chat_history_compaction_by_tokens.ChatHistoryCompactionByTokens",
        return_value=compaction_service,
    ):
        assert reloaded_hosting.container[IChatHistoryCompaction] is compaction_service

    importlib.reload(hosting)


def test_container_shares_compaction_service_instance() -> None:
    first = container[IChatHistoryCompaction]
    second = container[IChatHistoryCompaction]

    assert first is second


def test_container_resolves_session_store() -> None:
    session_store = Mock()
    with patch(
        "radio_gaga.services.session_store.SessionStore", return_value=session_store
    ):
        assert container[ISessionStore] is session_store


def test_invalid_log_level_defaults_to_info() -> None:
    with patch.object(hosting.os, "getenv", return_value="invalid"):
        reloaded_hosting = importlib.reload(hosting)

    assert reloaded_hosting.LOG_LEVEL == logging.INFO

    importlib.reload(hosting)
