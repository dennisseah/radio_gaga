import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from agent_framework import Agent, AgentSession

from radio_gaga.commons.prompts import get_system_prompt
from radio_gaga.models.chat_response import ChatResponse, ChatTokenUsage
from radio_gaga.protocols.i_chat_agent import IChatAgent
from radio_gaga.protocols.i_chat_client import IChatClient
from radio_gaga.protocols.i_chat_history_compaction import IChatHistoryCompaction
from radio_gaga.protocols.i_session_store import ISessionStore


@dataclass
class ChatAgent(IChatAgent):
    _chat_client: IChatClient
    _compaction_service: IChatHistoryCompaction
    _session_store: ISessionStore
    _logger: logging.Logger

    def __post_init__(self) -> None:
        self._logger.info("Initializing ChatAgent")

        # Configure the compaction callback before constructing the agent.
        client = self._chat_client.get_client()
        self._compaction_service.set_summarization_strategy(client)

        self._agent = Agent(
            client=client,
            name="MyAgent",
            instructions=get_system_prompt(),
            compaction_strategy=self._compaction_service.compact_history,
            default_options={"store": False},
        )

    async def stream(self, user_message: str, session: AgentSession) -> ChatResponse:
        time_start = time.perf_counter()

        async_stream = self._agent.run(user_message, session=session, stream=True)
        start_gen_time: float | None = None

        response: list[str] = []
        async for chunk in async_stream:
            if chunk.text:
                # Measure latency to the first visible text chunk.
                if start_gen_time is None:
                    start_gen_time = time.perf_counter() - time_start
                response.append(chunk.text)
                print(chunk.text, end="", flush=True)
        print()

        # Usage metadata is available on the finalized response, not stream updates.
        final_response = await async_stream.get_final_response()
        usage_details = final_response.usage_details or {}

        resp = ChatResponse(
            text="".join(response),
            start_generation_time=start_gen_time or 0.0,
            time_taken=time.perf_counter() - time_start,
            token_usage=ChatTokenUsage(
                prompt_tokens=usage_details.get("input_token_count", 0) or 0,
                completion_tokens=usage_details.get("output_token_count", 0) or 0,
                total_tokens=usage_details.get("total_token_count", 0) or 0,
                cache_creation_input_tokens=usage_details.get(
                    "cache_creation_input_token_count", 0
                )
                or 0,
                cache_read_input_tokens=usage_details.get(
                    "cache_read_input_token_count", 0
                )
                or 0,
            ),
        )
        self._logger.info(
            f"Start generation time: {resp.start_generation_time:.2f} seconds"
        )
        self._logger.info(f"Time taken: {resp.time_taken:.2f} seconds")
        self._logger.info(
            "Token usage: prompt=%d completion=%d total=%d "
            "cache_creation=%d cache_read=%d",
            resp.token_usage.prompt_tokens,
            resp.token_usage.completion_tokens,
            resp.token_usage.total_tokens,
            resp.token_usage.cache_creation_input_tokens,
            resp.token_usage.cache_read_input_tokens,
        )

        return resp

    def initialize(self) -> AgentSession:
        session = self._session_store.load_session(self._agent)
        self._compaction_service.initialize_session(session)
        return session

    def terminate(self, session: AgentSession) -> None:
        self._compaction_service.sync_session(session)
        self._session_store.persist_session(session)

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AgentSession]:
        session = self.initialize()
        try:
            yield session
        finally:
            self.terminate(session)
