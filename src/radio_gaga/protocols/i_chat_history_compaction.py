from typing import Protocol

from agent_framework import AgentSession, Message
from agent_framework.foundry import FoundryChatClient


class IChatHistoryCompaction(Protocol):
    def initialize_session(self, session: AgentSession) -> None:
        """Restore compaction state from a loaded session."""
        ...

    def set_summarization_strategy(self, chat_client: FoundryChatClient) -> None:
        """Set summarization strategy for a chat client

        Args:
            chat_client (FoundryChatClient): Foundry chat client instance to set
            the summarization strategy for.
        """
        ...

    async def compact_history(self, messages: list[Message]) -> bool:
        """
        Compact the chat history by summarizing messages.

        Args:
            messages (list[Message]): List of chat messages to compact.

        Returns:
            bool: True if compaction was successful, False otherwise.
        """
        ...

    def sync_session(self, session: AgentSession) -> None:
        """Copy the latest successful compaction into persisted session state.

        Args:
            session (AgentSession): The agent session to sync the compaction state into.
        """
        ...
