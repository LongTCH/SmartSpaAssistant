from app.pydantic_agents.model_hub import model_hub
from pydantic_ai import Agent

# @dataclass
# class MemoryAgentDeps:
#     summaries: list[str]


# And importantly, you will be given latest messages of the customer and the assistant.
# You can refer to the chat history for better understanding.

instructions = """
You are a helpful ai summary assistant.
You will summarize the conversation.
Please write in customer's language.
"""

model = model_hub["gemini-2.5-flash"]
memory_agent = Agent(model=model, instructions=instructions, retries=2, output_type=str)


# @memory_agent.instructions
# async def get_summaries(
#     context: RunContext[MemoryAgentDeps],
# ) -> str:
#     """
#     Get summaries from the context.
#     """
#     return "Below are some summaries of the conversation:\n" + "\n".join(
#         context.deps.summaries
#     )
