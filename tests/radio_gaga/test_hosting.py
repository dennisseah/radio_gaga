import importlib
import logging
from unittest.mock import Mock, patch

import radio_gaga.hosting as hosting
from radio_gaga.hosting import container
from radio_gaga.protocols.i_chat_agent import IChatAgent
from radio_gaga.protocols.i_chat_client import IChatClient
from radio_gaga.protocols.i_chat_history_compaction import IChatHistoryCompaction
from radio_gaga.protocols.i_session_store import ISessionStore


def test_container_resolves_logger() -> None:
    assert container[logging.Logger].name == "radio_gaga"


def test_container_resolves_chat_client() -> None:
    chat_client = Mock()
    with patch("radio_gaga.services.chat_client.ChatClient", return_value=chat_client):
        assert container[IChatClient] is chat_client


def test_container_resolves_chat_agent() -> None:
    chat_agent = Mock()
    with patch("radio_gaga.services.chat_agent.ChatAgent", return_value=chat_agent):
        assert container[IChatAgent] is chat_agent


def test_container_resolves_compaction_service() -> None:
    compaction_service = Mock()
    with patch(
        "radio_gaga.services.chat_history_compaction.ChatHistoryCompaction",
        return_value=compaction_service,
    ):
        assert container[IChatHistoryCompaction] is compaction_service


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
