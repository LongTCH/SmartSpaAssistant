from app.routes.route_alerts import router as alerts_router
from app.routes.route_conversations import router as conversations_router
from app.routes.route_guests import router as guests_router
from app.routes.route_interests import router as interests_router
from app.routes.route_notifications import router as notifications_router
from app.routes.route_scripts import router as scripts_router
from app.routes.route_setting import router as settings_router
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
    app.include_router(webhooks_router)
    app.include_router(scripts_router)
    app.include_router(sheets_router)
    app.include_router(ws_router)
    app.include_router(guests_router)
    app.include_router(interests_router)
    app.include_router(settings_router)
    app.include_router(notifications_router)
    app.include_router(alerts_router)
