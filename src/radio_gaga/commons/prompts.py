from jinja2 import Template

from radio_gaga import PROMPT_FOLDER


def _render_prompt(name: str) -> str:
    template_path = PROMPT_FOLDER / name
    with open(template_path) as f:
        template = Template(f.read())
    return template.render()


def get_system_prompt() -> str:
    return _render_prompt("system_prompt.jinja2")


def get_health_advisor_prompt() -> str:
    return _render_prompt("health_advisor_prompt.jinja2")
