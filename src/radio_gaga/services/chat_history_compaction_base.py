import json
import logging
from collections import Counter
from dataclasses import dataclass, field

from agent_framework import AgentSession, Message, SummarizationStrategy


@dataclass
class ChatHistoryCompactionBase:
    _logger: logging.Logger
    # The framework creates this strategy after dependency injection completes.
    _summarization_strategy: SummarizationStrategy = field(init=False, repr=False)
    # These fields track compaction across the current application session.
    _compaction_attempt_count: int = 0
    _compaction_count: int = 0
    _compacted_messages: list[Message] | None = None
    _compaction_source_message_ids: set[str] | None = None
    _compaction_source_message_fingerprints: Counter[str] | None = None

    @staticmethod
    def _is_excluded(message: Message) -> bool:
        # Framework versions use `_excluded`; accept the legacy key as well.
        properties = message.additional_properties
        return bool(properties.get("_excluded", properties.get("excluded", False)))

    def initialize_session(self, session: AgentSession) -> None:
        """Initialize strategy state from a loaded session when needed."""
        # Discard any snapshot left by a previous application session.
        self._reset_pending_compaction()

    @staticmethod
    def _get_session_messages(session: AgentSession) -> list[Message]:
        history = session.state.get("in_memory")
        if not isinstance(history, dict):
            return []
        messages = history.get("messages", [])
        return messages if isinstance(messages, list) else []

    async def _compact_history(self, messages: list[Message]) -> bool:
        self._logger.info(f"Compaction attempt #{self._compaction_attempt_count + 1}")
        self._compaction_attempt_count += 1
        compacted_message_count = sum(
            not self._is_excluded(message)
            for message in messages
            if message.role != "system"
        )
        # Capture stable IDs and content fingerprints before the strategy
        # mutates history.
        existing_message_ids = {id(message) for message in messages}
        self._compaction_source_message_ids = {
            message.message_id for message in messages if message.message_id is not None
        }
        self._compaction_source_message_fingerprints = Counter(
            self._message_fingerprint(message)
            for message in messages
            if message.message_id is None
        )
        compacted = await self._summarization_strategy(messages)

        self._logger.info(f"Existing messages count: {len(existing_message_ids)}")
        self._logger.info(f"Compacted: {compacted}")

        if compacted:
            # Keep the compacted list until the outer session can persist it.
            self._compaction_count += 1
            self._compacted_messages = list(messages)
            summary_message = next(
                (
                    message
                    for message in messages
                    if id(message) not in existing_message_ids
                ),
                None,
            )
            self._logger.info(
                f"Summary message: {summary_message.text if summary_message else None}"
            )

        self._logger.info(
            f"[Compaction status: attempts={self._compaction_attempt_count}, "
            f"messages={compacted_message_count}, "
            f"successful={self._compaction_count}]"
        )
        return compacted

    def sync_session(self, session: AgentSession) -> None:
        if self._compacted_messages is None:
            return

        # The framework compacts a request-local list, so merge it into durable state.
        source_message_ids = self._compaction_source_message_ids or set()
        source_fingerprints = self._compaction_source_message_fingerprints or Counter()
        history = session.state.get("in_memory")
        current_messages = self._get_session_messages(session)
        # Reconcile the framework's request-local history with persisted session state.
        new_messages: list[Message] = []
        for message in current_messages:
            if self._is_excluded(message):
                continue
            if message.message_id is not None:
                if message.message_id in source_message_ids:
                    continue
            else:
                # Older messages may lack IDs; fingerprints prevent duplicate writes.
                fingerprint = self._message_fingerprint(message)
                if source_fingerprints[fingerprint] > 0:
                    source_fingerprints[fingerprint] -= 1
                    continue
            new_messages.append(message)
        messages_to_store = [*self._compacted_messages, *new_messages]
        if isinstance(history, dict):
            history["messages"] = messages_to_store
        else:
            session.state["messages"] = messages_to_store
        self._reset_pending_compaction()

    def _reset_pending_compaction(self) -> None:
        self._compacted_messages = None
        self._compaction_source_message_ids = None
        self._compaction_source_message_fingerprints = None

    @staticmethod
    def _message_fingerprint(message: Message) -> str:
        return json.dumps(message.to_dict(), sort_keys=True, default=str)
