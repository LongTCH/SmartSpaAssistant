from jinja2 import Template


def render_tool_template(template_str: str, **kwargs) -> str:
    template = Template(template_str)
    return template.render(**kwargs)
