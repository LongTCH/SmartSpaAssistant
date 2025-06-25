from app.configs.constants import DEFAULT_SETTING_ID
from app.models import Setting
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def get_settings(db: AsyncSession) -> Setting:
    result = await db.execute(select(Setting).where(Setting.id == DEFAULT_SETTING_ID))
    return result.scalar_one_or_none()


async def save_settings(db: AsyncSession, settings: Setting) -> Setting:
    db.add(settings)
    await db.flush()
    return settings


async def update_settings(db: AsyncSession, settings: Setting) -> Setting:
    db.add(settings)
    await db.flush()
    return settings
