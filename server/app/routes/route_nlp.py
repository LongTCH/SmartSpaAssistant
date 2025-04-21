from app.services import nlp_service
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/nlp", tags=["NLP"])


@router.post("/keyword")
async def extract_keywords(request: Request):
    """
    Extract keywords from a given text using the NLP service.
    """
    body = await request.json()
    keyword = body.get("keyword")
    if not keyword:
        raise HTTPException(status_code=400, detail="Missing required field: keyword")
    keyword = await nlp_service.extract_nouns_adjectives(keyword)
    return keyword
