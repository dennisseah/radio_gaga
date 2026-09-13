import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime

from agent_framework import Agent, AgentSession

from radio_gaga import DEFAULT_SESSION_FILE
from radio_gaga.protocols.i_session_store import ISessionStore

SESSION_FILE = DEFAULT_SESSION_FILE


@dataclass
class SessionStore(ISessionStore):
    _logger: logging.Logger

    def load_session(self, agent: Agent) -> AgentSession:
        if not SESSION_FILE.exists():
            return agent.create_session()

        try:
            session_data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            return AgentSession.from_dict(session_data)
        except (OSError, KeyError, TypeError, ValueError) as error:
            self._logger.warning("Unable to load saved session: %s", error)
            self._quarantine_invalid_session()
            return agent.create_session()

    def _quarantine_invalid_session(self) -> None:
        invalid_path = SESSION_FILE.with_name(
            f"{SESSION_FILE.name}.invalid-"
            f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
        )
        try:
            os.replace(SESSION_FILE, invalid_path)
            self._logger.warning("Moved invalid session to %s", invalid_path)
        except OSError as error:
            self._logger.warning("Unable to quarantine invalid session: %s", error)

    def persist_session(self, session: AgentSession) -> None:
        temporary_path: str | None = None
        try:
            SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=SESSION_FILE.parent,
                prefix=f"{SESSION_FILE.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                json.dump(session.to_dict(), temporary_file, indent=2)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, SESSION_FILE)
            temporary_path = None
        finally:
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except FileNotFoundError:
                    pass
