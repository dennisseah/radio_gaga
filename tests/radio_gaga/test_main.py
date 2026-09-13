import runpy
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from radio_gaga.main import MyAgent
from radio_gaga.models.chat_response import ChatResponse, ChatTokenUsage


@pytest.mark.asyncio
async def test_run_reports_time_to_first_response_and_persists_once() -> None:
    session = Mock()
    chat_agent = Mock()
    response = ChatResponse(
        text="hello",
        start_generation_time=0.5,
        time_taken=1.0,
        token_usage=ChatTokenUsage(
            prompt_tokens=1,
            completion_tokens=1,
            total_tokens=2,
        ),
    )
    chat_agent.stream = AsyncMock(side_effect=[response, response])
    session_store = Mock()
    session_store.load_session.return_value = session
    logger = Mock()
    compaction_service = Mock()
    read_input = AsyncMock(side_effect=["question", "another question", "exit"])

    with patch("radio_gaga.main.asyncio.to_thread", read_input):
        await MyAgent(chat_agent, session_store, logger, compaction_service).run()

    chat_agent.get_agent.assert_called_once_with()
    session_store.load_session.assert_called_once_with(
        chat_agent.get_agent.return_value
    )
    compaction_service.initialize_session.assert_called_once_with(session)
    assert chat_agent.stream.call_count == 2
    chat_agent.stream.assert_any_await(user_message="question", session=session)
    chat_agent.stream.assert_any_await(user_message="another question", session=session)
    session_store.persist_session.assert_called_once_with(session)
    compaction_service.sync_session.assert_called_once_with(session)


@pytest.mark.asyncio
async def test_run_persists_when_agent_raises() -> None:
    session = Mock()
    chat_agent = Mock()
    chat_agent.stream = AsyncMock(side_effect=RuntimeError("agent failed"))
    session_store = Mock()
    session_store.load_session.return_value = session
    compaction_service = Mock()
    read_input = AsyncMock(return_value="question")

    with (
        patch("radio_gaga.main.asyncio.to_thread", read_input),
        pytest.raises(RuntimeError, match="agent failed"),
    ):
        await MyAgent(chat_agent, session_store, Mock(), compaction_service).run()

    compaction_service.initialize_session.assert_called_once_with(session)
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
