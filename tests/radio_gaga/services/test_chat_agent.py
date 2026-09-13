from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from radio_gaga.services.chat_agent import ChatAgent


def test_initializes_agent_with_configured_dependencies() -> None:
    compaction_service = Mock()
    chat_client = Mock()
    model_client = Mock()
    logger = Mock()
    created_agent = Mock()

    chat_client.get_client.return_value = model_client

    with (
        patch(
            "radio_gaga.services.chat_agent.Agent", return_value=created_agent
        ) as agent,
        patch(
            "radio_gaga.services.chat_agent.get_system_prompt",
            return_value="system instructions",
        ),
    ):
        chat_agent = ChatAgent(compaction_service, chat_client, logger)

    logger.info.assert_called_once_with("Initializing ChatAgent")
    chat_client.get_client.assert_called_once_with()
    compaction_service.set_summarization_strategy.assert_called_once_with(model_client)
    agent.assert_called_once_with(
        client=model_client,
        name="MyAgent",
        instructions="system instructions",
        compaction_strategy=compaction_service.compact_history,
        default_options={"store": False},
    )
    assert chat_agent.get_agent() is created_agent


def test_get_agent_returns_constructed_agent() -> None:
    created_agent = Mock()

    with (
        patch("radio_gaga.services.chat_agent.Agent", return_value=created_agent),
        patch(
            "radio_gaga.services.chat_agent.get_system_prompt", return_value="prompt"
        ),
    ):
        chat_agent = ChatAgent(Mock(), Mock(), Mock())

    assert chat_agent.get_agent() is created_agent


@pytest.mark.asyncio
async def test_stream_returns_combined_text_and_logs_first_response() -> None:
    compaction_service = Mock()
    chat_client = Mock()
    model_client = Mock()
    logger = Mock()
    created_agent = Mock()
    final_response = Mock(
        usage_details={
            "input_token_count": 10,
            "output_token_count": 4,
            "total_token_count": 14,
            "cache_creation_input_token_count": 6,
            "cache_read_input_token_count": 3,
        }
    )

    stream = MagicMock()
    stream.__aiter__.return_value = [Mock(text="hello"), Mock(text=" world")]
    stream.get_final_response = AsyncMock(return_value=final_response)
    created_agent.run.return_value = stream
    chat_client.get_client.return_value = model_client

    with (
        patch("radio_gaga.services.chat_agent.Agent", return_value=created_agent),
        patch(
            "radio_gaga.services.chat_agent.get_system_prompt", return_value="prompt"
        ),
        patch(
            "radio_gaga.services.chat_agent.time.perf_counter",
            side_effect=[10.0, 10.5, 11.0],
        ),
    ):
        chat_agent = ChatAgent(compaction_service, chat_client, logger)

        response = await chat_agent.stream("question", Mock())

    assert response.text == "hello world"
    assert response.token_usage.prompt_tokens == 10
    assert response.token_usage.completion_tokens == 4
    assert response.token_usage.total_tokens == 14
    assert response.token_usage.cache_creation_input_tokens == 6
    assert response.token_usage.cache_read_input_tokens == 3


@pytest.mark.asyncio
async def test_stream_allows_response_without_text_chunks() -> None:
    created_agent = Mock()
    final_response = Mock(usage_details={})
    stream = MagicMock()
    stream.__aiter__.return_value = [Mock(text="")]
    stream.get_final_response = AsyncMock(return_value=final_response)
    created_agent.run.return_value = stream

    with (
        patch("radio_gaga.services.chat_agent.Agent", return_value=created_agent),
        patch(
            "radio_gaga.services.chat_agent.get_system_prompt", return_value="prompt"
        ),
    ):
        chat_agent = ChatAgent(Mock(), Mock(), Mock())

        response = await chat_agent.stream("question", Mock())

    assert response.text == ""
    assert response.start_generation_time == 0.0
    assert response.token_usage.total_tokens == 0
