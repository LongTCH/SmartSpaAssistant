import uuid

import uvicorn
from app.agents import invoke_agent_graph
from app.agents.agent_graph import agent_graph  # bạn giữ nguyên phần này
from app.configs import env_config
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")

thread_id = str(uuid.uuid4())


@app.get("/", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/chat")
async def post_chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    try:
        response = await invoke_agent_graph(thread_id, user_input)
    except Exception as e:
        response = f"**Error:** {str(e)}"
    return {"response": response}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=env_config.SERVER_PORT)
