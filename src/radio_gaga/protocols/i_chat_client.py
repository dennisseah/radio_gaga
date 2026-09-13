from typing import Protocol

from agent_framework.foundry import FoundryChatClient


class IChatClient(Protocol):
    def get_client(self) -> FoundryChatClient:
        """
        Returns the underlying FoundryChatClient instance.
        """
        ...
