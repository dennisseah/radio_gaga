from contextlib import AbstractAsyncContextManager
from typing import Protocol

from agent_framework import AgentSession

from radio_gaga.models.chat_response import ChatResponse


class IPlannerAgent(Protocol):
    def get_session(self) -> AbstractAsyncContextManager[AgentSession]:
        """Return a managed session scope.

        Returns:
            AbstractAsyncContextManager[AgentSession]: The managed session scope.
        """
        ...

    async def stream(self, user_message: str, session: AgentSession) -> ChatResponse:
        """
        Stream the agent's response to a user message.

        Args:
            user_message (str): The message from the user.
            session (AgentSession): The agent session to use for the conversation.

        Returns:
            ChatResponse: The agent's response containing the text, start generation
            time, and time taken.
        """
        ...
