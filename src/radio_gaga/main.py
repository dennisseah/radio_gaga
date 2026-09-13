import asyncio
import logging
from dataclasses import dataclass

from agent_framework import AgentSession

from radio_gaga.hosting import container
from radio_gaga.protocols.i_chat_agent import IChatAgent
from radio_gaga.protocols.i_chat_history_compaction import IChatHistoryCompaction
from radio_gaga.protocols.i_session_store import ISessionStore


@dataclass
class MyAgent:
    _chat_agent: IChatAgent
    _session_store: ISessionStore
    _logger: logging.Logger
    _compaction_service: IChatHistoryCompaction

    async def each_turn(self, agent, session: AgentSession) -> bool:
        user_message = await asyncio.to_thread(input, "\nYou: ")
        if user_message.strip().lower() in {"exit", "quit"}:
            return False

        print("Agent: ", end="", flush=True)
        response = await self._chat_agent.stream(
            user_message=user_message, session=session
        )
        print(response, flush=True)
        return True

    async def run(self) -> None:
        agent = self._chat_agent.get_agent()
        session = self._session_store.load_session(agent)
        self._compaction_service.initialize_session(session)

        try:
            while await self.each_turn(agent, session):
                pass
        finally:
            self._compaction_service.sync_session(session)
            self._session_store.persist_session(session)


if __name__ == "__main__":
    main_class = container[MyAgent]
    asyncio.run(main_class.run())
