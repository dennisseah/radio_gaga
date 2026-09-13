from pydantic import BaseModel, field_validator


class ChatTokenUsage(BaseModel):
    """Token accounting returned for one agent response."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @field_validator(
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
    )
    def validate_token_count(cls, value: int) -> int:
        """Reject negative provider-reported token counts."""
        if value < 0:
            raise ValueError("Token counts cannot be negative")
        return value


class ChatResponse(BaseModel):
    """Text, timing, and token metadata produced by the chat agent."""

    text: str
    start_generation_time: float
    time_taken: float
    token_usage: ChatTokenUsage
