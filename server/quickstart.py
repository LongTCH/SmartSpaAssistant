from typing import Any, Dict

from pydantic_ai import Agent, Tool
from pydantic_ai.tools import ToolDefinition

# Danh sách các công cụ được định nghĩa động
list_tools = [
    {
        "name": "print_name",
        "description": "In ra tên của người dùng",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Tên của người dùng"}
            },
            "required": ["name"],
        },
    },
    {
        "name": "print_age",
        "description": "In ra tuổi của người dùng",
        "parameters": {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "description": "Tuổi của người dùng"}
            },
            "required": ["age"],
        },
    },
]

# Hàm tạo công cụ từ định nghĩa


def create_tool(tool_info: Dict[str, Any]) -> Tool:
    async def tool_function(**kwargs):
        print(kwargs)
        return kwargs

    this_tool_def = ToolDefinition(
        name=tool_info["name"],
        description=tool_info["description"],
        parameters_json_schema=tool_info["parameters"],
    )

    async def prepare_tool(ctx, tool_def: ToolDefinition):
        return this_tool_def

    tool = Tool(
        name=tool_info["name"],
        description=tool_info["description"],
        prepare=prepare_tool,
        takes_ctx=False,
        function=tool_function,
    )
    return tool


# Tạo danh sách các công cụ
tools = [create_tool(tool_info) for tool_info in list_tools]
# Khởi tạo agent với các công cụ
agent = Agent(model="openai:gpt-4o-mini", tools=tools)
# Sử dụng agent
result = agent.run_sync("Tên tôi là Nguyễn Văn A.")
print(result.output)
