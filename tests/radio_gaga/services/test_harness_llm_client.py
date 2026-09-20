from unittest.mock import Mock, patch

from radio_gaga.services.harness_llm_client import HarnessLLMClient, HarnessLLMClientEnv


def test_initializes_foundry_client() -> None:
    environment = HarnessLLMClientEnv(
        foundry_project_endpoint="https://example.test",
        harness_foundry_model="test-model",
    )
    logger = Mock()
    client = Mock()

    with (
        patch(
            "radio_gaga.services.harness_llm_client.FoundryChatClient",
            return_value=client,
        ) as foundry_client,
        patch(
            "radio_gaga.services.harness_llm_client.DefaultAzureCredential"
        ) as credential,
    ):
        chat_client = HarnessLLMClient(environment, logger)

    credential.assert_called_once_with()
    foundry_client.assert_called_once_with(
        project_endpoint="https://example.test",
        model="test-model",
        credential=credential.return_value,
    )
    logger.info.assert_called_once_with(
        "Initializing FoundryChatClient for HarnessLLMClient"
    )
    assert chat_client.get_client() is client
