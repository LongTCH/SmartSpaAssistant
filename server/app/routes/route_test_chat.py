import uuid

from app.agents import invoke_agent
from app.services.integrations import sheet_rag_service
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/test-chat", tags=["Test Chat"])


templates = Jinja2Templates(directory="app/templates")

thread_id = str(uuid.uuid4())


@router.get("/", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.post("/chat")
async def post_chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    try:
        response = await invoke_agent(thread_id, user_input)
    except Exception as e:
        response = f"**Error:** {str(e)}"
    return {"response": response}


@router.post("/sheets")
async def post_sheet(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    sheet_id = data.get("sheet_id")
    try:
        response = await sheet_rag_service.search_chunks_by_sheet_id(
            sheet_id=sheet_id, query=user_input, limit=5
        )
    except Exception as e:
        response = f"**Error:** {str(e)}"
    return response
