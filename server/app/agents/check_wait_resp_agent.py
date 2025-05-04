from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry

instructions = """
# You are a helpful assistant. Your task is to check if the response request customer to wait for retrieve information or not.
Example:
- If the response is "I will look up information and advise you in detail. Just a little time!", return True.
- If the response is "I will look up information and advise you in detail. Just a little time! Please wait a moment.", return True.
- If the response is "I will look up information and advise you in detail. Just a little time! Please wait a moment. I will get back to you as soon as possible.", return True.
- If the response is "I will look up information and advise you in detail. Just a little time! Please wait a moment. I will get back to you as soon as possible. Thank you for your patience.", return True.
etc
"""

check_wait_resp_agent = Agent(
    model="google-gla:gemini-2.0-flash",
    instructions=instructions,
    retries=2,
    output_type=str,
    output_retries=3,
)


@check_wait_resp_agent.output_validator
async def validate_output(context: RunContext[None], output: str) -> str:
    """
    Validate the output of the check wait response agent.
    """
    if not "True" in output and not "False" in output:
        raise ModelRetry(
            "Invalid output format. Expected a boolean value (True or False)."
        )
    return output
