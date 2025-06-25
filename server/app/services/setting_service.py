from typing import Any, Dict

from app.dtos import SettingUpdateDto
from app.models import Setting
from app.repositories import setting_repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified


async def get_setting_details(db: AsyncSession) -> Dict[str, Any]:
    setting = await setting_repository.get_settings(db)
    return setting.details if setting else {}


async def update_settings(db: AsyncSession, updates: SettingUpdateDto) -> Setting:
    setting = await setting_repository.get_settings(db)
    details = setting.details

    # Cập nhật các trường từ SettingUpdateDto
    if updates.chat_wait_seconds is not None:
        details["chat_wait_seconds"] = updates.chat_wait_seconds

    if updates.max_script_retrieval is not None:
        details["max_script_retrieval"] = updates.max_script_retrieval

    if updates.reaction_message is not None:
        details["reaction_message"] = updates.reaction_message

    if updates.identity is not None:
        details["identity"] = updates.identity

    if updates.instructions is not None:
        details["instructions"] = updates.instructions

    flag_modified(setting, "details")
    # Lưu dữ liệu đã cập nhật
    setting = await setting_repository.update_settings(db, setting)
    return setting
