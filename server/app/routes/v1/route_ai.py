from app.services.integrations import script_rag_service, sheet_rag_service
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/ai", tags=["AI"])


# Request Models
class ScriptSearchRequest(BaseModel):
    query: str = Field(
        ...,
        description="Search query for script content",
        example="làm thế nào để điều trị mụn",
    )


class SheetSearchRequest(BaseModel):
    query: str = Field(
        ..., description="Search query for sheet content", example="giá dịch vụ làm đẹp"
    )
    sheet_id: str = Field(
        ..., description="ID of the sheet to search in", example="sheet_123"
    )


@router.post(
    "/scripts",
    summary="Search script content using RAG",
    description="Search through script content using Retrieval-Augmented Generation (RAG) to find the most relevant scripts based on semantic similarity.",
)
async def get_scripts(request_data: ScriptSearchRequest):
    """
    Search through script content using semantic similarity.

    This endpoint uses RAG (Retrieval-Augmented Generation) to find the most relevant
    script content based on the provided query. It returns up to 10 most similar results
    ranked by cosine similarity score.

    - **query**: The search query in Vietnamese or English
    - Returns list of matching script content with similarity scores
    """
    # Call the service to get the script
    result = await script_rag_service.test_search_script_chunks(
        query=request_data.query, limit=10
    )
    return result


@router.post(
    "/sheets",
    summary="Search sheet content using RAG",
    description="Search through specific sheet content using Retrieval-Augmented Generation (RAG) to find the most relevant information based on semantic similarity.",
)
async def get_sheets(request_data: SheetSearchRequest):
    """
    Search through specific sheet content using semantic similarity.

    This endpoint uses RAG (Retrieval-Augmented Generation) to find the most relevant
    content from a specific sheet based on the provided query. It returns up to 10
    most similar results ranked by cosine similarity score.

    - **query**: The search query in Vietnamese or English
    - **sheet_id**: ID of the specific sheet to search within
    - Returns list of matching sheet content with similarity scores
    """
    # Call the service to get the script
    result = await sheet_rag_service.test_search_chunks_by_sheet_id(
        sheet_id=request_data.sheet_id, query=request_data.query, limit=10
    )
    return result
