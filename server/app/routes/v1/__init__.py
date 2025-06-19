from fastapi import APIRouter, FastAPI

from .route_ai import router as ai_router
from .route_alerts import router as alerts_router
from .route_conversations import router as conversations_router
from .route_guests import router as guests_router
from .route_interests import router as interests_router
from .route_notifications import router as notifications_router
from .route_scripts import router as scripts_router
from .route_setting import router as settings_router
from .route_sheets import router as sheets_router
from .route_webhooks import router as webhooks_router
from .websocket import ws_router

init_router = APIRouter()


@init_router.get("/v1/")
def index():
    return {"message": "Facebook Messenger Webhook"}


def include_router(app: FastAPI):
    """
    Include all routers in the FastAPI app.

    Args:
        app (FastAPI): The FastAPI app instance.
    """
    app.include_router(init_router)
    app.include_router(ai_router)
    app.include_router(conversations_router)
    app.include_router(webhooks_router)
    app.include_router(scripts_router)
    app.include_router(sheets_router)
    app.include_router(ws_router)
    app.include_router(guests_router)
    app.include_router(interests_router)
    app.include_router(settings_router)
    app.include_router(notifications_router)
    app.include_router(alerts_router)
