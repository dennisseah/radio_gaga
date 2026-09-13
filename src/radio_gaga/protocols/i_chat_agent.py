from typing import Protocol

from agent_framework import Agent


class IChatAgent(Protocol):
    def get_agent(self) -> Agent:
        """
        Returns the underlying Agent instance.
        """
        ...
