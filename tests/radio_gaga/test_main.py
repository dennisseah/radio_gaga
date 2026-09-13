import runpy
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from radio_gaga.main import MyAgent


@pytest.mark.asyncio
async def test_run_reports_time_to_first_response_and_persists_once() -> None:
    agent = Mock()
    session = Mock()
    agent.create_session.return_value = session
    agent.run.side_effect = [_stream_chunks("hello"), _stream_chunks("hello")]
    chat_agent = Mock()
    chat_agent.get_agent.return_value = agent
    session_store = Mock()
    session_store.load_session.return_value = session
    logger = Mock()
    read_input = AsyncMock(side_effect=["question", "another question", "exit"])

    with (
        patch("radio_gaga.main.asyncio.to_thread", read_input),
        patch(
            "radio_gaga.main.time.perf_counter",
            side_effect=[10.0, 12.34, 20.0, 22.34],
        ),
    ):
        await MyAgent(chat_agent, session_store, logger).run()

    chat_agent.get_agent.assert_called_once_with()
    session_store.load_session.assert_called_once_with(agent)
    assert agent.run.call_count == 2
    session_store.persist_session.assert_called_once_with(session)
    assert logger.info.call_count == 2
    assert all(
        call.args[0] == "Time taken to start agent response: 2.34 seconds"
        for call in logger.info.call_args_list
    )


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
        await MyAgent(chat_agent, session_store, Mock()).run()

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
