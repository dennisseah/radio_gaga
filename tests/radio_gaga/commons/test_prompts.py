from radio_gaga.commons.prompts import get_health_advisor_prompt, get_system_prompt


def test_get_system_prompt_loads_resource() -> None:
    prompt = get_system_prompt()

    assert prompt


def test_get_system_prompt_includes_safety_boundaries() -> None:
    prompt = get_system_prompt()

    assert "Medical or health questions" in prompt
    assert "Parking lot information" in prompt
    assert "Brief conversational greetings" in prompt
    assert '"What is love?"' in prompt
    assert '`echo "I am Batman"`' in prompt
    assert "call `health_advisor`" in prompt
    assert "return its complete response" in prompt
    assert "call `parking_lot`" in prompt
    assert "Do not call tools for greetings or unsupported requests" in prompt


def test_get_health_advisor_prompt_includes_safety_and_response_workflow() -> None:
    prompt = get_health_advisor_prompt()

    assert "definitive diagnosis" in prompt
    assert "emergency care" in prompt
    assert "### Response workflow" in prompt
    assert "Return these two sections in order" in prompt
    assert "Output only one valid JSON object in a fenced `json` block" in prompt
    assert (
        '{"goal":"string","steps":["string"],"professional_follow_up":"string or null"}'
        in prompt
    )
    assert "Never stop after the plan" in prompt
    assert "private chain-of-thought, or hidden reasoning" in prompt
