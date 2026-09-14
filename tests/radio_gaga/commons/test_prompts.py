from radio_gaga.commons.prompts import get_system_prompt


def test_get_system_prompt_loads_resource() -> None:
    prompt = get_system_prompt()

    assert prompt


def test_get_system_prompt_includes_safety_boundaries() -> None:
    prompt = get_system_prompt()

    assert "definitive diagnosis" in prompt
    assert "emergency care" in prompt
    assert "Only answer questions about medicine, health, or radiology" in prompt
    assert "conversational greetings are allowed" in prompt
    assert "professional tone appropriate for a medical website" in prompt
    assert "Do not entertain inappropriate, frivolous, role-playing" in prompt
    assert 'echo phrases such as "I am Batman."' in prompt
