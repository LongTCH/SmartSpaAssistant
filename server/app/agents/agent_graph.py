from app.agents.sheet_agent import SheetDeps, sheet_agent
from app.configs.mem0 import mem0_client
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from typing_extensions import TypedDict

MAX_HISTORY_MESSAGES = 7


class AgentState(TypedDict):
    user_input: str
    user_id: str
    messages: list[bytes]
    response: str


async def call_sheet_agent(state: AgentState) -> str:
    """
    Call the sheet agent with the user input and return the response.
    """
    # Extract the user input from the state
    try:
        user_input = state["user_input"]
        user_id = state["user_id"]
        # retrieve last messages from state
        recent_messages = (
            state["messages"][-MAX_HISTORY_MESSAGES:] if state.get("messages") else []
        )
        message_history: list[ModelMessage] = []
        for message in recent_messages:
            model_message = ModelMessagesTypeAdapter.validate_json(message)
            message_history.extend(model_message)
        # Retrieve memories from mem0
        memories = mem0_client.search(user_input, user_id=user_id, limit=5)["results"]
        context = ""
        for memory in memories:
            context += f"- {memory['memory']}\n"
        deps = SheetDeps(context_memory=context, latest_message=user_input)
        response: AgentRunResult = await sheet_agent.run(
            user_prompt=user_input, message_history=message_history, deps=deps
        )
        if state.get("messages") is None:
            state["messages"] = []
        state["messages"].append(response.new_messages_json())
        agent_response = response.output
        mem0_client.add(
            f"User: {user_input}\nAssistant: {agent_response}", user_id=user_id
        )
        return {
            "user_input": user_input,
            "messages": state["messages"],
            "response": agent_response,
        }
    except Exception as e:
        print(f"Error in call_sheet_agent: {e}")


def create_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("sheet_agent", call_sheet_agent)

    # Add edges
    graph.add_edge(START, "sheet_agent")
    graph.add_edge("sheet_agent", END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


agent_graph = create_graph()
