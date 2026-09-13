import runpy
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from radio_gaga.main import MyAgent


@pytest.mark.asyncio
async def test_run_persists_after_turn_without_duplicate_exit_write() -> None:
    agent = Mock()
    session = Mock()
    agent.create_session.return_value = session
    agent.run.return_value = _stream_chunks("hello")
    chat_agent = Mock()
    chat_agent.get_agent.return_value = agent
    session_store = Mock()
    session_store.load_session.return_value = session
    read_input = AsyncMock(side_effect=["question", "exit"])

    with patch("radio_gaga.main.asyncio.to_thread", read_input):
        await MyAgent(chat_agent, session_store).run()

    chat_agent.get_agent.assert_called_once_with()
    session_store.load_session.assert_called_once_with(agent)
    agent.run.assert_called_once_with("question", session=session, stream=True)
    session_store.persist_session.assert_called_once_with(session)


@pytest.mark.asyncio
async def test_run_persists_when_agent_raises() -> None:
    agent = Mock()
    session = Mock()
    chat_agent = Mock()
    chat_agent.get_agent.return_value = agent
    session_store = Mock()
    session_store.load_session.return_value = session
    read_input = AsyncMock(return_value="question")
    agent.run.side_effect = RuntimeError("agent failed")

    with (
        patch("radio_gaga.main.asyncio.to_thread", read_input),
        pytest.raises(RuntimeError, match="agent failed"),
    ):
        await MyAgent(chat_agent, session_store).run()

    session_store.persist_session.assert_called_once_with(session)


def test_module_entrypoint_runs_main_agent() -> None:
    main_agent = Mock()
    run_argument = object()
    main_agent.run.return_value = run_argument
    fake_container = MagicMock()
    fake_container.__getitem__.return_value = main_agent

    with (
        patch("radio_gaga.hosting.container", fake_container),
        patch("radio_gaga.main.asyncio.run") as run,
    ):
        runpy.run_module("radio_gaga.main", run_name="__main__")

    fake_container.__getitem__.assert_called_once()
    run.assert_called_once_with(run_argument)


async def _stream_chunks(text: str):
    yield Mock(text=text)
