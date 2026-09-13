import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from agent_framework import AgentSession

import radio_gaga.services.session_store as session_store_module
from radio_gaga.services.session_store import SessionStore


@pytest.fixture
def session_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "session.json"
    monkeypatch.setattr(session_store_module, "SESSION_FILE", path)
    return path


def test_load_session_returns_new_session_when_file_is_missing(
    session_file: Path,
) -> None:
    agent = Mock()
    expected = AgentSession()
    agent.create_session.return_value = expected

    actual = SessionStore(Mock()).load_session(agent)

    assert actual is expected
    agent.create_session.assert_called_once_with()


def test_persist_and_load_session_round_trip(session_file: Path) -> None:
    store = SessionStore(Mock())
    expected = AgentSession()

    store.persist_session(expected)
    actual = store.load_session(Mock())

    assert actual.session_id == expected.session_id
    assert json.loads(session_file.read_text()) == expected.to_dict()
    assert not list(session_file.parent.glob("*.tmp"))


def test_persist_creates_missing_parent_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session_file = tmp_path / "nested" / "session.json"
    monkeypatch.setattr(session_store_module, "SESSION_FILE", session_file)

    SessionStore(Mock()).persist_session(AgentSession())

    assert session_file.exists()


def test_load_session_quarantines_invalid_json(session_file: Path) -> None:
    logger = Mock()
    store = SessionStore(logger)
    agent = Mock()
    replacement = AgentSession()
    agent.create_session.return_value = replacement
    session_file.write_text("not json")

    actual = store.load_session(agent)

    assert actual is replacement
    assert not session_file.exists()
    assert len(list(session_file.parent.glob("session.json.invalid-*"))) == 1
    assert logger.warning.call_count == 2


def test_quarantine_logs_when_replacement_fails(session_file: Path) -> None:
    logger = Mock()
    store = SessionStore(logger)
    session_file.write_text("invalid")

    with patch.object(
        session_store_module.os, "replace", side_effect=OSError("failed")
    ):
        store._quarantine_invalid_session()

    logger.warning.assert_called_once()


def test_persist_cleans_up_temporary_file_when_replacement_fails(
    session_file: Path,
) -> None:
    store = SessionStore(Mock())

    with (
        patch.object(session_store_module.os, "replace", side_effect=OSError("failed")),
        patch.object(session_store_module.os, "unlink", side_effect=FileNotFoundError),
        pytest.raises(OSError, match="failed"),
    ):
        store.persist_session(AgentSession())
