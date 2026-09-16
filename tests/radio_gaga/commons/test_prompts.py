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
    assert "Response workflow:" in prompt
    assert 'exact order: "Plan" followed by "Execution."' in prompt
    assert "output only one valid JSON object in a fenced `json` code block" in prompt
    assert (
        '{"goal":"string","steps":["string"],"professional_follow_up":"string or null"}'
        in prompt
    )
    assert 'After the JSON plan, output the "Execution" section' in prompt
    assert "never stop after presenting only the plan" in prompt
    assert "the answer, private chain-of-thought, or hidden reasoning" in prompt
