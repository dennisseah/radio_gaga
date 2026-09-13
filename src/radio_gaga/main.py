import asyncio
from dataclasses import dataclass

from radio_gaga.hosting import container
from radio_gaga.protocols.i_chat_agent import IChatAgent
from radio_gaga.protocols.i_session_store import ISessionStore


@dataclass
class MyAgent:
    _chat_agent: IChatAgent
    _session_store: ISessionStore

    async def run(self) -> None:
        agent = self._chat_agent.get_agent()
        session = self._session_store.load_session(agent)
        session_persisted = False

        try:
            while True:
                user_message = await asyncio.to_thread(input, "\nYou: ")
                if user_message.strip().lower() in {"exit", "quit"}:
                    break

                session_persisted = False
                print("Agent: ", end="", flush=True)
                async_stream = agent.run(user_message, session=session, stream=True)

                async for chunk in async_stream:
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                print()
                self._session_store.persist_session(session)
                session_persisted = True
        finally:
            if not session_persisted:
                self._session_store.persist_session(session)


if __name__ == "__main__":
    main_class = container[MyAgent]
    asyncio.run(main_class.run())
