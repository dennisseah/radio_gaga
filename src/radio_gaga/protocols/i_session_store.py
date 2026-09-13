from typing import Protocol

from agent_framework import Agent, AgentSession


class ISessionStore(Protocol):
    def load_session(self, agent: Agent) -> AgentSession:
        """Return the session associated with the given agent.

        Args:
            agent (Agent): agent for which to load the session.

        Returns:
            AgentSession: session associated with the given agent.
        """
        ...

    def persist_session(self, session: AgentSession) -> None:
        """Persist session data

        Args:
            session (_type_): agent session to persist.
        """
