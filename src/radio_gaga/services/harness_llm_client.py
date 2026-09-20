import logging
from dataclasses import dataclass

from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential
from lagom.environment import Env

from radio_gaga.protocols.i_chat_client import IChatClient


class HarnessLLMClientEnv(Env):
    foundry_project_endpoint: str
    harness_foundry_model: str


@dataclass
class HarnessLLMClient(IChatClient):
    _env: HarnessLLMClientEnv
    _logger: logging.Logger

    def __post_init__(self):
        self._logger.info("Initializing FoundryChatClient for HarnessLLMClient")

        self.client = FoundryChatClient(
            project_endpoint=self._env.foundry_project_endpoint,
            model=self._env.harness_foundry_model,
            credential=DefaultAzureCredential(),
        )

    def get_client(self) -> FoundryChatClient:
        return self.client
