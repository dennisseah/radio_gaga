from unittest.mock import Mock, patch

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
