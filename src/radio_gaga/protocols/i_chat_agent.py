from typing import Protocol

from agent_framework import Agent, AgentSession


class IChatAgent(Protocol):
    async def stream(self, user_message: str, session: AgentSession) -> str:
        """
        Stream the agent's response to a user message.

        Args:
            user_message (str): The message from the user.
            session (AgentSession): The agent session to use for the conversation.

        Returns:
            str: The agent's response.
        """
        ...

    def get_agent(self) -> Agent:
        """
        Returns the underlying Agent instance.
        """
        ...
