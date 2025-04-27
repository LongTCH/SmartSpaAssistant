from typing import Any, Dict

from app.services import setting_service
from fastapi import APIRouter

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("")
async def get_local_data():
    return await setting_service.get_local_data_dict()


@router.put("")
async def update_local_data(data: Dict[str, Any]):
    return await setting_service.save_local_data(data)
