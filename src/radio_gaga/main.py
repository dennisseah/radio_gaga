import asyncio
import logging
from dataclasses import dataclass

from agent_framework import AgentSession

from radio_gaga.hosting import container
from radio_gaga.protocols.i_chat_agent import IChatAgent


@dataclass
class MyAgent:
    _chat_agent: IChatAgent
    _logger: logging.Logger

    async def each_turn(self, session: AgentSession) -> bool:
        user_message = await asyncio.to_thread(input, "\nYou: ")
        if user_message.strip().lower() in {"exit", "quit"}:
            return False

        print("Agent: ", end="", flush=True)
        await self._chat_agent.stream(user_message=user_message, session=session)
        return True

    async def run(self) -> None:
        session = self._chat_agent.initialize()

        try:
            while await self.each_turn(session):
                pass
        finally:
            self._chat_agent.terminate(session)


if __name__ == "__main__":
    main_class = container[MyAgent]
    asyncio.run(main_class.run())
