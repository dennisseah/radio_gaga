import asyncio
import logging
import time
from dataclasses import dataclass

from radio_gaga.hosting import container
from radio_gaga.protocols.i_chat_agent import IChatAgent
from radio_gaga.protocols.i_session_store import ISessionStore


@dataclass
class MyAgent:
    _chat_agent: IChatAgent
    _session_store: ISessionStore
    _logger: logging.Logger

    async def each_turn(self, agent, session) -> bool:
        user_message = await asyncio.to_thread(input, "\nYou: ")
        if user_message.strip().lower() in {"exit", "quit"}:
            return False

        print("Agent: ", end="", flush=True)
        time_start = time.perf_counter()
        async_stream = agent.run(user_message, session=session, stream=True)
        response_started = False

        async for chunk in async_stream:
            if chunk.text:
                if not response_started:
                    time_taken = time.perf_counter() - time_start
                    print()
                    self._logger.info(
                        f"Time taken to start agent response: {time_taken:.2f} seconds"
                    )
                    response_started = True
                print(chunk.text, end="", flush=True)

        print()
        return True

    async def run(self) -> None:
        agent = self._chat_agent.get_agent()
        session = self._session_store.load_session(agent)

        try:
            while await self.each_turn(agent, session):
                pass
        finally:
            self._session_store.persist_session(session)


if __name__ == "__main__":
    main_class = container[MyAgent]
    asyncio.run(main_class.run())
