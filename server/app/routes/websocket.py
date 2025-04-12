from fastapi import APIRouter, Request, HTTPException, Depends, Form
from typing import Annotated
from starlette.responses import Response as HttpResponse
from app.configs import env_config
from app.configs.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import chat_service, conversation_service, file_metadata_service
import asyncio

ws_router = APIRouter(prefix="/ws")
