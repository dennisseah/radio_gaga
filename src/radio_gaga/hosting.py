"""Defines our top level DI container.
Utilizes the Lagom library for dependency injection, see more at:

- https://lagom-di.readthedocs.io/en/latest/
- https://github.com/meadsteve/lagom
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from lagom import Container, dependency_definition

from radio_gaga.protocols.i_chat_agent import IChatAgent
from radio_gaga.protocols.i_chat_client import IChatClient
from radio_gaga.protocols.i_chat_history_compaction import IChatHistoryCompaction
from radio_gaga.protocols.i_session_store import ISessionStore

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

configured_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = logging.getLevelNamesMapping().get(configured_log_level, logging.INFO)

radio_gaga_logger = logging.getLogger("radio_gaga")
radio_gaga_logger.setLevel(LOG_LEVEL)
radio_gaga_logger.propagate = False

if not radio_gaga_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "\033[32m%(asctime)s %(levelname)s %(name)s: %(message)s\033[0m"
        )
    )
    radio_gaga_logger.addHandler(handler)

if configured_log_level not in logging.getLevelNamesMapping():
    radio_gaga_logger.warning(
        "Invalid LOG_LEVEL=%r; defaulting to INFO", configured_log_level
    )


container = Container()
"""The top level DI container for our application."""


# Register our dependencies ------------------------------------------------------------


@dependency_definition(container, singleton=True)
def _() -> logging.Logger:
    return radio_gaga_logger


@dependency_definition(container, singleton=True)
def _(c: Container) -> IChatAgent:
    from radio_gaga.services.chat_agent import ChatAgent

    return c[ChatAgent]


@dependency_definition(container, singleton=True)
def _(c: Container) -> IChatClient:
    from radio_gaga.services.chat_client import ChatClient

    return c[ChatClient]


@dependency_definition(container)
def _(c: Container) -> IChatHistoryCompaction:
    from radio_gaga.services.chat_history_compaction import ChatHistoryCompaction

    return c[ChatHistoryCompaction]


@dependency_definition(container)
def _(c: Container) -> ISessionStore:
    from radio_gaga.services.session_store import SessionStore

    return c[SessionStore]
