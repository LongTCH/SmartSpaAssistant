from app.routes.route_conversations import router as conversations_router
from app.routes.route_documents import router as documents_router
from app.routes.route_nlp import router as nlp_router
from app.routes.route_scripts import router as scripts_router
from app.routes.route_sheets import router as sheets_router
from app.routes.route_webhooks import router as webhooks_router
from app.routes.websocket import ws_router
from fastapi import APIRouter, FastAPI

init_router = APIRouter()


@init_router.get("/")
def index():
    return {"message": "Facebook Messenger Webhook"}


def include_router(app: FastAPI):
    """
    Include all routers in the FastAPI app.

    Args:
        app (FastAPI): The FastAPI app instance.
    """
    app.include_router(init_router)
    app.include_router(conversations_router)
    app.include_router(documents_router)
    app.include_router(nlp_router)
    app.include_router(webhooks_router)
    app.include_router(scripts_router)
    app.include_router(sheets_router)
    app.include_router(ws_router)
