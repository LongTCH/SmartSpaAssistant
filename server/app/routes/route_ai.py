from app.configs.database import get_session
from app.services.integrations import script_rag_service
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/similar-scripts")
async def get_embeddings(request: Request, db: AsyncSession = Depends(get_session)):
    """
    Get embeddings for a given text.
    """
    body = await request.json()
    inputs: str = body.get("inputs")
    limit: int = int(body.get("limit", 5))
    if not inputs:
        raise HTTPException(status_code=400, detail="inputs is required")
    scripts = await script_rag_service.get_similar_scripts(db, inputs, limit)
    return scripts
