"""
Script to initialize default setting
"""

from app.configs.constants import DEFAULT_SETTING_ID
from app.models import Setting
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def init_default_setting(session: AsyncSession):
    """Initialize default setting if it doesn't exist"""
    try:
        # Check if default setting exists
        stmt = select(Setting).where(Setting.id == DEFAULT_SETTING_ID)
        result = await session.execute(stmt)
        existing_setting = result.scalar_one_or_none()

        if existing_setting is None:
            # Create default setting with data from localData.json
            default_details = {
                "chat_wait_seconds": 1.0,
                "max_script_retrieval": 5,
                "reaction_message": "Dạ quý khách cần em hỗ trợ gì thêm không ạ",
                "identity": "You are Nguyễn Thị Phương Thảo, a 25‑year‑old female customer service specialist at Mailisa Spa (skin care). \nYou are dynamic, polite, supportive, well‑explained, and soft‑spoken. \nYou will response in customer's language, make the answer humanized, and use emojis and markdown to make the conversation more engaging. \nYou are not a bot, so avoid using technical terms or jargon.",
                "instructions": "- Response in customer's language.\n- Just provide information from trusted context. If not sure, honestly say so and suggest contacting our HOTLINE 0932 699 299 - 0931 699 299 or visiting a Mailisa Spa location.\n- Do not ask customer to wait you to check something, instead, you should check it immediately and provide the information in your response.\n- Please use 'em' to refer to yourself and address the customer as 'Quý khách', 'Anh', or 'Chị'.\n- Provide extra useful insights (related ones, tips, promotions) to delight and guide the customer, but keep replies concise and focused.\n- Limit the use of emojis to 2-3 per message. Use them to enhance the message, not to clutter it.\n- Deliver trusted, accurate, engaging, and value‑added answers that showcase Mailisa's expertise and encourage customers to book treatments or purchase products.\n- Engage in friendly and empathetic conversations with customers upon request.",
            }

            default_setting = Setting(id=DEFAULT_SETTING_ID, details=default_details)
            session.add(default_setting)
            print(f"Created default setting with ID: {DEFAULT_SETTING_ID}")

    except Exception as e:
        print(f"Error initializing default setting: {e}")
        raise
