import json
import logging
import os
from dataclasses import dataclass
from uuid import uuid4

from agent_framework import Agent, AgentSession

from radio_gaga import DEFAULT_SESSION_FILE
from radio_gaga.protocols.i_session_store import ISessionStore

SESSION_FILE = DEFAULT_SESSION_FILE


@dataclass
class SessionStore(ISessionStore):
    _logger: logging.Logger

    def load_session(self, agent: Agent) -> AgentSession:
        # Start a fresh conversation when no persisted session exists yet.
        if not SESSION_FILE.exists():
            return agent.create_session()

        try:
            with open(SESSION_FILE, encoding="utf-8") as f:  # noqa: ASYNC230
                data = json.loads(f.read())
            return AgentSession.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            self._logger.warning("Invalid session file: %s", error)
            self._quarantine_invalid_session()
            return agent.create_session()

    def persist_session(self, session: AgentSession) -> None:
        serialized = session.to_dict()
        json_str = json.dumps(serialized, indent=2)
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = SESSION_FILE.with_name(f"{SESSION_FILE.name}.{uuid4()}.tmp")
        try:
            with open(temporary_file, "w", encoding="utf-8") as f:  # noqa: ASYNC230
                f.write(json_str)
            os.replace(temporary_file, SESSION_FILE)
        finally:
            try:
                os.unlink(temporary_file)
            except FileNotFoundError:
                pass

    def _quarantine_invalid_session(self) -> None:
        quarantine_file = SESSION_FILE.with_name(
            f"{SESSION_FILE.name}.invalid-{uuid4()}"
        )
        try:
            os.replace(SESSION_FILE, quarantine_file)
        except OSError as error:
            self._logger.warning("Failed to quarantine invalid session file: %s", error)
        else:
            self._logger.warning(
                "Quarantined invalid session file as %s", quarantine_file
            )
