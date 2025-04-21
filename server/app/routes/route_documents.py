import asyncio

from app.configs.database import get_session
from app.services import file_metadata_service
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response as HttpResponse

router = APIRouter(prefix="/document_stores", tags=["Document Stores"])


@router.post("")
async def process_document_store(db: AsyncSession = Depends(get_session)):
    # Start the update process in a background task without waiting
    asyncio.create_task(file_metadata_service.update_knowledge(db))
    # await file_metadata_service.update_knowledge(db)
    return HttpResponse(status_code=200)
