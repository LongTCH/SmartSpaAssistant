from app.agents.agent_graph import agent_graph


async def invoke_agent_graph(user_id, user_input: str):
    config = {"configurable": {"thread_id": user_id}}
    input_state = {"user_input": user_input, "user_id": user_id}
    result = await agent_graph.ainvoke(input_state, config=config, stream_mode="values")
    return result["response"]
