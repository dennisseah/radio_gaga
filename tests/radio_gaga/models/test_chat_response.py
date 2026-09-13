import pytest
from pydantic import ValidationError

from radio_gaga.models.chat_response import ChatResponse, ChatTokenUsage


def test_chat_token_usage_defaults_cache_counts_to_zero() -> None:
    usage = ChatTokenUsage(
        prompt_tokens=10,
        completion_tokens=4,
        total_tokens=14,
    )

    assert usage.cache_creation_input_tokens == 0
    assert usage.cache_read_input_tokens == 0


def test_chat_token_usage_preserves_cache_counts() -> None:
    usage = ChatTokenUsage(
        prompt_tokens=10,
        completion_tokens=4,
        total_tokens=14,
        cache_creation_input_tokens=6,
        cache_read_input_tokens=3,
    )

    assert usage.model_dump() == {
        "prompt_tokens": 10,
        "completion_tokens": 4,
        "total_tokens": 14,
        "cache_creation_input_tokens": 6,
        "cache_read_input_tokens": 3,
    }


def test_chat_token_usage_rejects_negative_token_counts() -> None:
    with pytest.raises(ValidationError, match="Token counts cannot be negative"):
        ChatTokenUsage(prompt_tokens=10, completion_tokens=4, total_tokens=-1)

    with pytest.raises(ValidationError, match="Token counts cannot be negative"):
        ChatTokenUsage(prompt_tokens=-1, completion_tokens=4, total_tokens=3)


def test_chat_response_allows_empty_text_for_non_text_responses() -> None:
    usage = ChatTokenUsage(prompt_tokens=10, completion_tokens=4, total_tokens=14)

    response = ChatResponse(
        text="",
        start_generation_time=0.0,
        time_taken=1.0,
        token_usage=usage,
    )

    assert response.text == ""


def test_chat_response_preserves_response_metadata() -> None:
    usage = ChatTokenUsage(prompt_tokens=10, completion_tokens=4, total_tokens=14)

    response = ChatResponse(
        text="hello",
        start_generation_time=0.5,
        time_taken=1.0,
        token_usage=usage,
    )

    assert response.text == "hello"
    assert response.start_generation_time == 0.5
    assert response.time_taken == 1.0
    assert response.token_usage is usage
