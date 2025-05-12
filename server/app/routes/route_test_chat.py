from app.services.integrations import script_rag_service, sheet_rag_service
from fastapi import APIRouter, Request

router = APIRouter(prefix="/test-chat", tags=["Test Chat"])


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


@router.post("/scripts")
async def post_sheet(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    try:
        response = await script_rag_service.search_script_chunks(
            query=user_input, limit=5
        )
    except Exception as e:
        response = f"**Error:** {str(e)}"
    return response
