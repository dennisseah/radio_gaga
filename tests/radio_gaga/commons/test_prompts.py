from radio_gaga.commons.prompts import get_system_prompt


def test_get_system_prompt_loads_resource() -> None:
    prompt = get_system_prompt()

    assert prompt


def test_get_system_prompt_includes_safety_boundaries() -> None:
    prompt = get_system_prompt()

    assert "definitive diagnosis" in prompt
    assert "emergency care" in prompt
