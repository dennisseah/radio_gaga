from unittest.mock import Mock, patch

from radio_gaga.agents.health_advisor import HealthAdvisorLLMClientEnv, SubAgent
from radio_gaga.commons.agent_usage_middleware import AgentUsageMiddleware
from radio_gaga.commons.turn_statistics import TurnStatistics


def test_create_agent_configures_usage_middleware() -> None:
    environment = HealthAdvisorLLMClientEnv(
        foundry_project_endpoint="https://example.test",
        health_advisor_foundry_model="health-model",
    )
    statistics = TurnStatistics()

    with (
        patch("radio_gaga.agents.health_advisor.Agent") as create_agent,
        patch("radio_gaga.agents.health_advisor.FoundryChatClient") as foundry_client,
        patch("radio_gaga.agents.health_advisor.DefaultAzureCredential") as credential,
    ):
        SubAgent(Mock(), environment).create_agent(statistics)

    foundry_client.assert_called_once_with(
        project_endpoint="https://example.test",
        model="health-model",
        credential=credential.return_value,
    )
    [middleware] = create_agent.call_args.kwargs["middleware"]
    assert isinstance(middleware, AgentUsageMiddleware)
    assert middleware._statistics is statistics
    [history_provider] = create_agent.call_args.kwargs["context_providers"]
    assert not history_provider.load_messages
