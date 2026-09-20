import logging
from dataclasses import dataclass

from agent_framework import Agent, InMemoryHistoryProvider
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential
from lagom.environment import Env

from radio_gaga.commons.prompts import get_health_advisor_prompt
from radio_gaga.services.agent_usage_middleware import AgentUsageMiddleware
from radio_gaga.services.turn_statistics import TurnStatistics


class HealthAdvisorLLMClientEnv(Env):
    foundry_project_endpoint: str
    health_advisor_foundry_model: str


@dataclass
class SubAgent:
    _logger: logging.Logger
    _env: HealthAdvisorLLMClientEnv

    def create_agent(self, statistics: TurnStatistics) -> Agent:
        client = FoundryChatClient(
            project_endpoint=self._env.foundry_project_endpoint,
            model=self._env.health_advisor_foundry_model,
            credential=DefaultAzureCredential(),
        )

        return Agent(
            client=client,
            instructions=get_health_advisor_prompt(),
            name="health_advisor",
            description="A specialist agent that answers medical and health questions.",
            context_providers=[InMemoryHistoryProvider(load_messages=False)],
            middleware=[AgentUsageMiddleware(statistics)],
        )
