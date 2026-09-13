from jinja2 import Template

from radio_gaga import PROMPT_FOLDER


def get_system_prompt() -> str:

    template_path = PROMPT_FOLDER / "system_prompt.jinja2"
    with open(template_path) as f:
        template = Template(f.read())
    return template.render()
